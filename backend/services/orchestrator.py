import json
import re
import time
import logging
from datetime import datetime
from typing import Optional

from backend.models.automation_schemas import (
    AutomationRequest, AutomationResponse, AgentResult
)
from backend.services.rag_service import query_rag, _try_llm_chain
from backend.prompts.orchestrator_prompt import (
    INTENT_CLASSIFIER_PROMPT, ORCHESTRATOR_PROMPT
)
from backend.db import get_user_context

logger = logging.getLogger(__name__)


# ── Intent classifier ─────────────────────────────────────────────────

def _classify_intent(message: str) -> dict:
    """Use LLM to extract intent, insurance type, entities from message."""
    prompt = INTENT_CLASSIFIER_PROMPT.replace("{message}", message)

    raw = _try_llm_chain(
        context  = message,
        question = "Classify this insurance query",
        prompt_template = prompt,
    )

    if raw is None:
        # Rule-based fallback intent detection
        msg = message.lower()

        # ── Insurance type detection ──────────────────────────────────
        if any(w in msg for w in ["crop", "cotton", "wheat", "rice", "farm",
                                   "harvest", "rain", "drought", "flood", "sowing",
                                   "farmer", "yield", "vidarbha", "kharif", "rabi"]):
            ins_type = "crop"
        elif any(w in msg for w in ["health", "hospital", "medical", "doctor",
                                     "treatment", "surgery", "icu", "medicine"]):
            ins_type = "health"
        elif any(w in msg for w in ["travel", "flight", "trip", "baggage",
                                     "passport", "abroad", "visa", "tour"]):
            ins_type = "travel"
        elif any(w in msg for w in ["car", "vehicle", "bike", "motor", "accident",
                                     "crash", "bumper", "tyre", "drove"]):
            ins_type = "motor"
        else:
            ins_type = "motor"  # default

        # ── Intent detection ──────────────────────────────────────────
        if any(w in msg for w in ["accident", "claim", "damage", "broke",
                                   "crashed", "destroyed", "damaged", "lost",
                                   "stolen", "flood", "drought", "rains destroyed",
                                   "crop loss", "fire", "theft"]):
            intent  = "file_claim"
            agents  = ["rag", "claims", "fraud"]

        elif any(w in msg for w in ["renew", "renewal", "better deal",
                                     "cheaper", "compare", "switch insurer"]):
            intent  = "renewal"
            agents  = ["rag", "renewal"]

        elif any(w in msg for w in ["risk", "premium", "profile", "score",
                                     "how risky", "my risk"]):
            intent  = "risk_profile"
            agents  = ["risk"]

        elif any(w in msg for w in ["fraud", "suspicious", "fake", "verify claim"]):
            intent  = "fraud_check"
            agents  = ["rag", "fraud"]

        else:
            intent  = "policy_query"
            agents  = ["rag"]

        # ── Extract policy number ─────────────────────────────────────
        policy_match = re.search(r'[A-Z]{2,}-[A-Z0-9]{2,}-\d{4}-\d+', message, re.IGNORECASE)
        policy_number = policy_match.group(0).upper() if policy_match else None

        return {
            "intent":         intent,
            "insurance_type": ins_type,
            "policy_number":  policy_number,
            "urgency":        "high" if intent == "file_claim" else "medium",
            "entities":       {},
            "agents_needed":  agents,
        }

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except Exception as e:
        logger.warning("Intent parse failed: %s", e)
        return {
            "intent":         "general_query",
            "insurance_type": "motor",
            "policy_number":  None,
            "urgency":        "low",
            "entities":       {},
            "agents_needed":  ["rag"],
        }


# ── Individual agent runners ──────────────────────────────────────────

def _run_rag_agent(
    message: str,
    insurance_type: str,
    policy_number: Optional[str],
) -> AgentResult:
    start = time.time()
    try:
        query = message
        if policy_number:
            query += f" Policy number: {policy_number}"

        result = query_rag(query, insurance_type)
        duration = int((time.time() - start) * 1000)

        return AgentResult(
            agent_name  = "Policy RAG",
            status      = "success",
            duration_ms = duration,
            summary     = f"Retrieved policy context — confidence: {result.get('confidence', 'Low')}",
            data        = result,
        )
    except Exception as e:
        return AgentResult(
            agent_name  = "Policy RAG",
            status      = "failed",
            duration_ms = int((time.time() - start) * 1000),
            summary     = f"RAG failed: {str(e)[:80]}",
            data        = None,
        )


def _run_fraud_agent(
    message: str,
    insurance_type: str,
    policy_number: str,
    entities: dict,
    claim_id: str | None = None,
) -> AgentResult:
    start = time.time()
    try:
        from backend.services.fraud_detector import detect_fraud

        # Look up real database history
        context = get_user_context(policy_number=policy_number)
        previous_claims = sum(1 for c in context.get("claims", []) if c["claim_id"] != claim_id)

        amount = 0.0
        try:
            amt_str = entities.get("amount")
            if not amt_str or str(amt_str).lower() in ["null", "none", ""]:
                amount_match = re.search(r'(?:\u20b9|\$|Rs\.?)\s*([\d,]+)', message)
                if amount_match:
                    amt_str = amount_match.group(1)
            if amt_str and str(amt_str).lower() not in ["null", "none", ""]:
                amount = float(str(amt_str).replace(",", "").replace("\u20b9", ""))
        except Exception:
            amount = 0.0

        data = {
            "claim_id":            claim_id,
            "claim_type":          insurance_type,
            "policy_number":       policy_number or "UNKNOWN",
            "claim_amount":        amount,
            "days_after_incident": 1,
            "previous_claims":     previous_claims,
            "incident_date":       entities.get("date", datetime.now().strftime("%d-%m-%Y")),
            "description":         message,
        }

        result = detect_fraud(data)
        duration = max(int((time.time() - start) * 1000), 1)

        return AgentResult(
            agent_name  = "Fraud Detector",
            status      = "success",
            duration_ms = duration,
            summary     = f"Fraud score: {result['fraud_score']}/100 — {result['verdict']} (based on {previous_claims} previous claims)",
            data        = result,
        )
    except Exception as e:
        return AgentResult(
            agent_name  = "Fraud Detector",
            status      = "failed",
            duration_ms = max(int((time.time() - start) * 1000), 1),
            summary     = f"Fraud check failed: {str(e)[:80]}",
            data        = None,
        )


def _run_risk_agent(
    insurance_type: str,
    entities: dict,
) -> AgentResult:
    start = time.time()
    try:
        from backend.services.risk_profiler import profile_risk
        from backend.models.risk_schemas import (
            RiskProfileRequest,
            HealthRiskInput, MotorRiskInput,
            TravelRiskInput, CropRiskInput,
        )

        # Build minimal risk input from available entities
        if insurance_type == "health":
            request = RiskProfileRequest(
                insurance_type = "health",
                health = HealthRiskInput(age=35, bmi=24.0),
            )
        elif insurance_type == "motor":
            request = RiskProfileRequest(
                insurance_type = "motor",
                motor = MotorRiskInput(
                    age=30, vehicle_age=3,
                    annual_km=15000, vehicle_type="sedan"
                ),
            )
        elif insurance_type == "travel":
            request = RiskProfileRequest(
                insurance_type = "travel",
                travel = TravelRiskInput(
                    age=30, trips_per_year=3,
                    avg_trip_duration=7,
                    destinations=["usa"],
                ),
            )
        else:
            request = RiskProfileRequest(
                insurance_type = "crop",
                crop = CropRiskInput(
                    crop_type="wheat",
                    land_area_acres=10.0,
                    location_state="Punjab",
                    irrigation="partial",
                    season="rabi",
                ),
            )

        result = profile_risk(request)
        duration = int((time.time() - start) * 1000)

        return AgentResult(
            agent_name  = "Risk Profiler",
            status      = "success",
            duration_ms = duration,
            summary     = f"Risk score: {result.risk_score}/100 — {result.risk_category} risk · Premium adjustment: {result.premium_adjustment}",
            data        = result.model_dump(),
        )
    except Exception as e:
        return AgentResult(
            agent_name  = "Risk Profiler",
            status      = "failed",
            duration_ms = int((time.time() - start) * 1000),
            summary     = f"Risk profiling failed: {str(e)[:80]}",
            data        = None,
        )


def _run_renewal_agent(
    insurance_type: str,
    policy_number: Optional[str],
    entities: dict,
) -> AgentResult:
    start = time.time()
    try:
        from backend.services.renewal_agent import run_renewal_agent
        from backend.models.renewal_schemas import (
            RenewalRequest, CurrentPolicy, UserProfile
        )

        # Look up real database history
        context = get_user_context(policy_number=policy_number)
        policy  = context.get("policy")
        user    = context.get("user")

        if policy:
            current_policy = CurrentPolicy(
                provider_name        = policy.get("provider", "Current Insurer"),
                annual_premium       = policy.get("annual_premium", 12000.0),
                sum_insured          = policy.get("sum_insured", 500000.0),
                coverage_type        = "Comprehensive",
                years_with_provider  = policy.get("years_with_provider", 2),
                claim_free_years     = policy.get("claim_free_years", 1),
            )
            user_name = user.get("name", "User") if user else "User"
        else:
            current_policy = CurrentPolicy(
                provider_name        = "Current Insurer",
                annual_premium       = 12000.0,
                sum_insured          = 500000.0,
                coverage_type        = "Comprehensive",
                years_with_provider  = 2,
                claim_free_years     = 1,
            )
            user_name = "User"

        request = RenewalRequest(
            current_policy = current_policy,
            user_profile = UserProfile(
                name           = user_name,
                age            = 35,
                city           = entities.get("location", "Hyderabad"),
                insurance_type = insurance_type,
                risk_score     = 0,
            ),
        )

        result = run_renewal_agent(request)
        duration = max(int((time.time() - start) * 1000), 1)

        return AgentResult(
            agent_name  = "Renewal Agent",
            status      = "success",
            duration_ms = duration,
            summary     = f"Best deal: {result.best_deal.provider_name} at ₹{result.best_deal.negotiated_premium:,.0f}/year — saving ₹{result.savings_amount:,.0f}",
            data        = result.model_dump(),
        )
    except Exception as e:
        return AgentResult(
            agent_name  = "Renewal Agent",
            status      = "failed",
            duration_ms = max(int((time.time() - start) * 1000), 1),
            summary     = f"Renewal check failed: {str(e)[:80]}",
            data        = None,
        )


def _run_claims_agent(
    message: str,
    insurance_type: str,
    entities: dict,
    policy_number: str | None = None,
) -> AgentResult:
    """Simplified claims agent — no image required in orchestrator."""
    start = time.time()
    try:
        from backend.services.claims_service import PART_COST_MAP

        # Extract amount from message or estimate from description
        amt_str = entities.get("amount")
        if not amt_str or str(amt_str).lower() in ["null", "none", ""]:
            amount_match = re.search(r'(?:\u20b9|\$|Rs\.?)\s*([\d,]+)', message)
            if amount_match:
                amt_str = amount_match.group(1)
        if amt_str and str(amt_str).lower() not in ["null", "none", ""]:
            amount_str = str(amt_str).replace(",", "").replace("\u20b9", "")
            try:
                amount = float(amount_str)
            except Exception:
                amount = 0.0
        else:
            amount = 0.0

        # If no amount mentioned, estimate from description keywords
        if amount == 0:
            msg = message.lower()
            detected = []
            for part, costs in PART_COST_MAP.items():
                if part in msg:
                    detected.append({
                        "part": part.title(),
                        "severity": "Moderate",
                        "estimated_cost": costs["moderate"]
                    })
            amount = sum(d["estimated_cost"] for d in detected) or 15000.0

        deductible = round(amount * 0.10, 2)
        covered    = round(amount - deductible, 2)

        import uuid
        from backend.db import save_claim
        claim_id = str(uuid.uuid4())

        try:
            save_claim(
                claim_id       = claim_id,
                policy_id      = policy_number or "UNKNOWN",
                amount         = amount,
                covered_amount = covered,
                status         = "estimated",
                description    = message,
            )
        except Exception as dbe:
            logger.warning("Failed to save claim in orchestrator: %s", dbe)

        result = {
            "claim_id":              claim_id,
            "total_repair_estimate": amount,
            "covered_amount":        covered,
            "deductible":            deductible,
            "confidence":            "Medium",
            "degraded":              True,
            "notes":                 "Estimated from incident description — submit damage photo for accurate assessment",
        }

        duration = max(int((time.time() - start) * 1000), 1)
        return AgentResult(
            agent_name  = "Claims Estimator",
            status      = "success",
            duration_ms = duration,
            summary     = f"Estimated repair: ₹{amount:,.0f} — Covered: ₹{covered:,.0f} after 10% deductible",
            data        = result,
        )
    except Exception as e:
        return AgentResult(
            agent_name  = "Claims Estimator",
            status      = "failed",
            duration_ms = int((time.time() - start) * 1000),
            summary     = f"Claims estimation failed: {str(e)[:80]}",
            data        = None,
        )


def _run_full_claim_pipeline(
    message: str,
    insurance_type: str,
    entities: dict,
    policy_number: str | None,
) -> tuple[AgentResult, AgentResult | None]:
    """
    End-to-end claim pipeline:
    1. Run claims agent to estimate and save claim to DB
    2. Run fraud detection on the saved claim
    3. Update claim status based on fraud verdict (auto-approve or flag)
    4. Recalculate/update user's risk profile based on new claim count
    """
    import uuid
    from backend.db import save_claim, save_risk_profile, get_user_context

    # 1. Run claims agent
    claim_result = _run_claims_agent(message, insurance_type, entities, policy_number)
    if claim_result.status != "success" or not claim_result.data:
        return claim_result, None

    claim_data = claim_result.data
    claim_id = claim_data.get("claim_id")
    amount = claim_data.get("total_repair_estimate", 0.0)
    covered_amount = claim_data.get("covered_amount", 0.0)

    # 2. Run fraud agent
    fraud_result = _run_fraud_agent(
        message, insurance_type,
        policy_number or "UNKNOWN", entities,
        claim_id=claim_id
    )

    if fraud_result.status == "success" and fraud_result.data:
        fraud_data = fraud_result.data
        verdict = fraud_data.get("verdict", "Genuine")
        
        # 3. Save updated claim status to DB
        status = "approved" if verdict == "Genuine" else "under_review"
        
        try:
            save_claim(
                claim_id=claim_id,
                policy_id=policy_number or "UNKNOWN",
                amount=amount,
                covered_amount=covered_amount,
                status=status,
                description=message
            )
            # Update the claim status inside the claims result data so it displays properly in UI
            claim_result.summary = f"Claim status: {status.upper()} — Estimated repair: ₹{amount:,.0f} — Covered: ₹{covered_amount:,.0f} after 10% deductible"
            claim_result.data["status"] = status
        except Exception as dbe:
            logger.warning("Failed to update claim status in pipeline: %s", dbe)

        # 4. Update risk profile in DB
        try:
            context = get_user_context(policy_number=policy_number)
            user = context.get("user")
            if user:
                user_id = user["user_id"]
                previous_claims = context.get("previous_claims_count", 0)
                # Compute updated risk score
                current_profile = context.get("risk_profile")
                base_score = current_profile["score"] if current_profile else 30
                # Increase score based on number of claims
                new_score = min(base_score + (previous_claims * 15), 100)
                new_category = "High" if new_score > 60 else "Medium" if new_score > 35 else "Low"
                profile_id = str(uuid.uuid4())
                save_risk_profile(profile_id, user_id, insurance_type, new_score, new_category)
                logger.info("Updated risk profile for user %s to score %d (%s)", user_id, new_score, new_category)

                # 5. Send SMS notification
                phone = user.get("phone")
                if phone:
                    from backend.services.notifications import send_sms
                    msg = f"InsureAI Update: Claim {claim_id[:8]}... for ₹{amount:,.0f} under policy {policy_number} has been {status.upper()}."
                    send_sms(phone, msg)
        except Exception as rpe:
            logger.warning("Failed to update risk profile or send SMS in pipeline: %s", rpe)

    return claim_result, fraud_result


# ── Final report generator ────────────────────────────────────────────

def _generate_final_report(
    message: str,
    intent: str,
    insurance_type: str,
    agent_results: list[AgentResult],
) -> tuple[str, list[str], bool]:
    """Generate unified report + next steps from all agent results."""

    # Build comprehensive context
    context_parts = [
        f"User Query: {message}",
        f"Detected Intent: {intent}",
        f"Insurance Type: {insurance_type.title()}",
        "",
        "Agent Results:",
    ]

    for ar in agent_results:
        if ar.status == "success":
            context_parts.append(f"✓ {ar.agent_name}: {ar.summary}")
        else:
            context_parts.append(f"✗ {ar.agent_name}: {ar.summary}")

    context = "\n".join(context_parts)
    question = f"Generate a unified insurance report for: {message}"

    report = _try_llm_chain(
        context         = context,
        question        = question,
        prompt_template = ORCHESTRATOR_PROMPT,
    )

    degraded = False

    # Build next steps from agent data
    next_steps = []

    for ar in agent_results:
        if ar.status != "success" or not ar.data:
            continue

        if ar.agent_name == "Fraud Detector":
            verdict = ar.data.get("verdict", "")
            if verdict == "Fraudulent":
                next_steps.append("⚠️ Claim flagged as high risk — contact our fraud team immediately")
            elif verdict == "Suspicious":
                next_steps.append("⚠️ Claim requires manual review — our team will contact you in 24hrs")
            else:
                next_steps.append("✅ Fraud check passed — claim is clear to proceed")

        if ar.agent_name == "Claims Estimator":
            covered = ar.data.get("covered_amount", 0)
            next_steps.append(f"📋 Submit damage photos for accurate assessment (estimated cover: ₹{covered:,.0f})")

        if ar.agent_name == "Renewal Agent":
            savings = ar.data.get("savings_amount", 0)
            best    = ar.data.get("best_deal", {})
            if savings > 500:
                next_steps.append(f"💰 Switch to {best.get('provider_name', 'better insurer')} to save ₹{savings:,.0f}/year")

        if ar.agent_name == "Risk Profiler":
            category = ar.data.get("risk_category", "")
            if category in ["High", "Very High"]:
                next_steps.append("📊 High risk profile detected — review lifestyle factors to reduce premium")

        if ar.agent_name == "Policy RAG":
            next_steps.append("📄 Review your policy document for specific coverage details")

    if not next_steps:
        next_steps = [
            "📄 Review policy document for coverage details",
            "📞 Contact support at 1800-XXX-XXXX for assistance",
        ]

    if report is None:
        degraded = True
        rag_agent = next((ar for ar in agent_results if ar.agent_name == "Policy RAG"), None)

        if rag_agent and rag_agent.data:
            # Use actual RAG answer instead of generic message
            rag_answer = rag_agent.data.get("answer", "")
            report = (
                f"Based on your policy documents:\n\n{rag_answer}\n\n"
                f"Confidence: {rag_agent.data.get('confidence', 'Low')}"
            )
        else:
            report = (
                f"InsureAI ran {len(agent_results)} agent(s) on your query.\n\n" +
                "\n".join(f"• {ar.agent_name}: {ar.summary}" for ar in agent_results
                          if ar.status == "success") +
                "\n\nFor detailed assistance please contact our support team."
            )

    return report, next_steps[:5], degraded


# ── Main orchestrator ─────────────────────────────────────────────────

def run_orchestrator(request: AutomationRequest) -> AutomationResponse:
    """
    Main agent automation pipeline:
    1. Classify intent from natural language
    2. Plan which agents to run
    3. Execute agents sequentially
    4. Aggregate results
    5. Generate unified report
    """
    total_start  = time.time()
    agent_results: list[AgentResult] = []

    # Step 1 — Classify intent
    intent_data    = _classify_intent(request.message)
    intent         = intent_data.get("intent", "general_query")
    insurance_type = request.insurance_type or intent_data.get("insurance_type", "motor")
    policy_number  = request.policy_number  or intent_data.get("policy_number")
    entities       = intent_data.get("entities", {})
    agents_needed  = intent_data.get("agents_needed", ["rag"])

    logger.info(
        "Intent: %s | Type: %s | Agents: %s",
        intent, insurance_type, agents_needed
    )

    # Step 2 + 3 — Execute agents in order
    policy_context = None
    claim_result   = None
    fraud_result   = None
    risk_result    = None
    renewal_result = None

    # RAG first — always provides policy context
    if "rag" in agents_needed:
        result = _run_rag_agent(request.message, insurance_type, policy_number)
        agent_results.append(result)
        if result.status == "success" and result.data:
            policy_context = result.data.get("answer", "")

    # Claims & Fraud integrated pipeline or independent fallback
    if "claims" in agents_needed and "fraud" in agents_needed:
        c_res, f_res = _run_full_claim_pipeline(
            request.message, insurance_type, entities, policy_number or None
        )
        agent_results.append(c_res)
        if c_res.status == "success":
            claim_result = c_res.data
        if f_res:
            agent_results.append(f_res)
            if f_res.status == "success":
                fraud_result = f_res.data
    else:
        # Fallback to independent calls
        if "claims" in agents_needed:
            result = _run_claims_agent(request.message, insurance_type, entities, policy_number or None)
            agent_results.append(result)
            if result.status == "success":
                claim_result = result.data

        if "fraud" in agents_needed:
            _claim_id: str | None = claim_result.get("claim_id") if claim_result else None
            result = _run_fraud_agent(
                request.message, insurance_type,
                policy_number or "UNKNOWN", entities,
                claim_id=_claim_id
            )
            agent_results.append(result)
            if result.status == "success":
                fraud_result = result.data

    # Risk fourth — independent
    if "risk" in agents_needed:
        result = _run_risk_agent(insurance_type, entities)
        agent_results.append(result)
        if result.status == "success":
            risk_result = result.data

    # Renewal last — uses risk score
    if "renewal" in agents_needed:
        result = _run_renewal_agent(insurance_type, policy_number, entities)
        agent_results.append(result)
        if result.status == "success":
            renewal_result = result.data

    # Step 4 + 5 — Aggregate + report
    final_report, next_steps, degraded = _generate_final_report(
        request.message, intent, insurance_type, agent_results
    )

    total_ms   = int((time.time() - total_start) * 1000)
    successful = sum(1 for ar in agent_results if ar.status == "success")
    confidence = (
        "High"   if successful >= 3 else
        "Medium" if successful >= 1 else
        "Low"
    )

    return AutomationResponse(
        user_message   = request.message,
        intent         = intent,
        insurance_type = insurance_type,
        agents_run     = agent_results,
        policy_context = policy_context,
        claim_result   = claim_result,
        fraud_result   = fraud_result,
        risk_result    = risk_result,
        renewal_result = renewal_result,
        final_report   = final_report,
        next_steps     = next_steps,
        total_time_ms  = total_ms,
        confidence     = confidence,
        degraded       = degraded,
    )
