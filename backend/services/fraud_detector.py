import re
import os
import sqlite3
import logging
from datetime import datetime

MOCK_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mock_db")

from backend.services.rag_service import _try_llm_chain
from backend.prompts.fraud_prompt import FRAUD_DETECTION_PROMPT

logger = logging.getLogger(__name__)

# ── Suspicious keywords by category ──────────────────────────────────
VAGUE_WORDS = [
    "sudden", "unknown", "not sure", "maybe", "somehow",
    "i think", "not certain", "approximately", "i guess",
]

SUSPICIOUS_WORDS = [
    "friend drove", "borrowed", "someone else",
    "no witnesses", "no receipt", "cash payment",
    "lost documents", "burned", "stolen then found",
]


# ── Layer 1: Rule Engine ──────────────────────────────────────────────

def _rule_late_claim(data: dict) -> tuple[int, str | None]:
    days = int(data.get("days_after_incident", 0))
    if days > 30:
        return 30, f"Claim filed very late ({days} days after incident)"
    elif days > 7:
        return 15, f"Claim filed late ({days} days after incident)"
    return 0, None


def _rule_high_amount(data: dict) -> tuple[int, str | None]:
    amount = float(data.get("claim_amount", 0))
    claim_type = data.get("claim_type", "motor").lower()

    thresholds = {
        "motor":  {"high": 100000, "very_high": 300000},
        "health": {"high": 200000, "very_high": 500000},
        "travel": {"high": 50000,  "very_high": 150000},
        "crop":   {"high": 150000, "very_high": 400000},
    }
    t = thresholds.get(claim_type, thresholds["motor"])

    if amount > t["very_high"]:
        return 25, f"Very high claim amount (₹{amount:,.0f}) for {claim_type} insurance"
    elif amount > t["high"]:
        return 15, f"Above average claim amount (₹{amount:,.0f}) for {claim_type} insurance"
    return 0, None


def _rule_frequent_claims(data: dict) -> tuple[int, str | None]:
    prev = int(data.get("previous_claims", 0))
    if prev > 4:
        return 25, f"Very high claims history ({prev} previous claims)"
    elif prev > 2:
        return 15, f"Multiple previous claims ({prev} claims)"
    return 0, None


def _rule_vague_description(data: dict) -> tuple[int, str | None]:
    desc = data.get("description", "").lower()
    found = [w for w in VAGUE_WORDS if w in desc]
    if len(found) >= 2:
        return 20, f"Very vague incident description (keywords: {', '.join(found)})"
    elif found:
        return 10, f"Vague incident description (keyword: {found[0]})"
    return 0, None


def _rule_suspicious_description(data: dict) -> tuple[int, str | None]:
    desc = data.get("description", "").lower()
    found = [w for w in SUSPICIOUS_WORDS if w in desc]
    if found:
        return 20, f"Suspicious pattern in description: '{found[0]}'"
    return 0, None


def _rule_policy_format(data: dict) -> tuple[int, str | None]:
    policy = data.get("policy_number", "").strip()
    # Accept: DG-2025-042 OR DG-MOTOR-2025-042
    pattern = r'^[A-Z]{2,}-[A-Z0-9]{2,}-\d{2,}(-\d+)?$'
    if not re.match(pattern, policy):
        return 15, f"Policy number format looks invalid: '{policy}'"
    return 0, None


def _rule_incident_date(data: dict) -> tuple[int, str | None]:
    date_str = data.get("incident_date", "")
    if not date_str:
        return 0, None
        
    incident = None
    # Try multiple common formats
    for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
        try:
            incident = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue
            
    if not incident:
        # Fallback for plain digits if possible (e.g. 22032026)
        if len(date_str) == 8 and date_str.isdigit():
            try:
                incident = datetime.strptime(date_str, "%d%m%Y")
            except ValueError:
                pass

    if not incident:
        return 10, f"Incident date '{date_str}' is in an unrecognized format. Please use DD-MM-YYYY."

    if incident > datetime.now():
        return 30, "Incident date is in the future"
    if (datetime.now() - incident).days > 365:
        return 20, "Incident occurred over a year ago"
        
    return 0, None


def _rule_flight_check(data: dict) -> tuple[int, str | None]:
    if data.get("claim_type", "").lower() != "travel":
        return 0, None
    flight_num = data.get("flight_number")
    if not flight_num:
        return 10, "Flight number missing for travel claim"
        
    db_path = os.path.join(MOCK_DB_DIR, "flights.db")
    if not os.path.exists(db_path):
        return 0, None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM flights WHERE flight_number = ?", (flight_num.upper(),))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return 20, f"Flight number {flight_num.upper()} not found in airline records"
        if row[0] == "On Time":
            return 50, f"Flight {flight_num.upper()} was on time, contradicting delay/cancellation claim"
    except Exception as e:
        logger.warning(f"DB Error checking flight: {e}")
        
    return 0, None


def _rule_hospital_check(data: dict) -> tuple[int, str | None]:
    if data.get("claim_type", "").lower() != "health":
        return 0, None
    hospital = data.get("hospital_name")
    if not hospital:
        return 10, "Hospital name missing for health claim"
        
    db_path = os.path.join(MOCK_DB_DIR, "hospitals.db")
    if not os.path.exists(db_path):
        return 0, None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT is_blacklisted, average_billing_multiplier FROM hospitals WHERE hospital_name = ?", (hospital,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return 0, None # unknown hospital, assume ok for now
            
        is_blacklisted, avg_multiplier = row
        if is_blacklisted:
            return 60, f"Hospital '{hospital}' is on the blacklisted providers list"
        
        claim_amt = float(data.get("claim_amount", 0))    
        if avg_multiplier > 2.0 and claim_amt > 100000:
            return 25, f"Hospital '{hospital}' has a history of extreme overbilling (multiplier: {avg_multiplier}x)"
            
    except Exception as e:
        logger.warning(f"DB Error checking hospital: {e}")
        
    return 0, None


def _rule_workshop_check(data: dict) -> tuple[int, str | None]:
    if data.get("claim_type", "").lower() != "motor":
        return 0, None
    workshop = data.get("workshop_name")
    if not workshop:
        # Not strictly required, but slightly suspicious
        return 5, "Workshop name missing for motor claim"
        
    db_path = os.path.join(MOCK_DB_DIR, "workshops.db")
    if not os.path.exists(db_path):
        return 0, None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT is_blacklisted FROM workshops WHERE workshop_name = ?", (workshop,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return 60, f"Workshop '{workshop}' is on the blacklisted repairers list"
            
    except Exception as e:
        logger.warning(f"DB Error checking workshop: {e}")
        
    return 0, None


# ── Layer 2: Score Aggregator ─────────────────────────────────────────

RULES = [
    _rule_late_claim,
    _rule_high_amount,
    _rule_frequent_claims,
    _rule_vague_description,
    _rule_suspicious_description,
    _rule_policy_format,
    _rule_incident_date,
    _rule_flight_check,
    _rule_hospital_check,
    _rule_workshop_check,
]


def _calculate_score(data: dict) -> tuple[int, list[str]]:
    total_score = 0
    reasons = []

    for rule in RULES:
        try:
            points, reason = rule(data)
            if points > 0 and reason:
                total_score += points
                reasons.append(reason)
        except Exception as e:
            logger.warning("Rule %s failed: %s", rule.__name__, e)

    return min(total_score, 100), reasons


def _get_verdict(score: int) -> tuple[str, str]:
    if score >= 70:
        return "Fraudulent", "High"
    elif score >= 40:
        return "Suspicious", "Medium"
    else:
        return "Genuine", "Low"


def _get_recommended_action(verdict: str) -> str:
    return {
        "Genuine":    "Auto Approve — no further action needed",
        "Suspicious": "Manual Review — assign to senior investigator",
        "Fraudulent": "Reject & Escalate — flag for legal review",
    }[verdict]


# ── Layer 3: LLM Investigation Report ────────────────────────────────

def _generate_investigation_report(
    data: dict, score: int, reasons: list[str]
) -> str:
    context = (
        f"Claim Type: {data.get('claim_type', 'Unknown')}\n"
        f"Policy Number: {data.get('policy_number', 'N/A')}\n"
        f"Claim Amount: ₹{float(data.get('claim_amount', 0)):,.0f}\n"
        f"Days After Incident: {data.get('days_after_incident', 'N/A')}\n"
        f"Previous Claims: {data.get('previous_claims', 0)}\n"
        f"Incident Description: {data.get('description', 'N/A')}\n"
        f"Fraud Score: {score}/100\n"
        f"Risk Signals Detected:\n"
        + ("\n".join(f"- {r}" for r in reasons) if reasons else "None")
    )
    question = (
        f"Generate a fraud investigation report for this claim "
        f"with score {score}/100."
    )

    report = _try_llm_chain(
        context=context,
        question=question,
        prompt_template=FRAUD_DETECTION_PROMPT,
    )

    if report is None:
        # Rule-based fallback report
        if not reasons:
            return (
                "No fraud signals detected. Claim details are consistent "
                "and within expected parameters. Safe to auto-approve."
            )
        return (
            f"Fraud analysis identified {len(reasons)} risk signal(s):\n\n"
            + "\n".join(f"• {r}" for r in reasons)
            + f"\n\nOverall risk score: {score}/100. "
            + (
                "Claim appears genuine despite minor flags."
                if score < 40 else
                "Manual review is recommended before processing."
            )
        )
    return report


# ── Main Entry Point ──────────────────────────────────────────────────

def detect_fraud(data: dict) -> dict:
    """
    Main fraud detection function.
    Layer 1 → Rules → Layer 2 → Score → Layer 3 → LLM report
    """
    score, reasons = _calculate_score(data)
    verdict, risk_level = _get_verdict(score)
    action = _get_recommended_action(verdict)
    report = _generate_investigation_report(data, score, reasons)

    return {
        "fraud_score":          score,
        "risk_level":           risk_level,
        "verdict":              verdict,
        "reasons":              reasons,
        "investigation_report": report,
        "recommended_action":   action,
        "confidence":           (
            "High" if len(reasons) >= 3
            else "Medium" if reasons
            else "Low"
        ),
        "degraded":             report.startswith("Fraud analysis identified"),
    }
