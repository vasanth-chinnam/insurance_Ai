import json
import logging
import base64
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI  # pyre-ignore
from langchain_core.messages import HumanMessage  # pyre-ignore

from backend.config import GOOGLE_API_KEY, VISION_MODEL
from backend.services.rag_service import query_rag, _try_llm_chain
from backend.models.claim_schemas import ClaimRequest, ClaimResponse, DamageDetail
from backend.prompts.motor_prompt import MOTOR_CLAIMS_PROMPT, VISION_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

# ── Vision LLM singleton (gemini-1.5-flash — free tier) ───────────────
# ── Vision LLM singleton (gemini-1.5-flash — free tier) ───────────────
_vision_llm = None

# ── Filename-based damage hints ───────────────────────────────────
FILENAME_HINTS = {
    "front":  ["Bumper", "Hood", "Headlight", "Radiator"],
    "rear":   ["Trunk", "Taillight", "Bumper"],
    "side":   ["Door", "Fender", "Mirror"],
    "left":   ["Door", "Fender", "Mirror"],
    "right":  ["Door", "Fender", "Mirror"],
    "roof":   ["Roof"],
    "wind":   ["Windshield"],
    "wheel":  ["Tyre"],
    "full":   ["Bumper", "Hood", "Door", "Fender"],
}

def _detect_area_from_filename(filename: str) -> tuple[str, list[str]]:
    """
    Extract damage area and likely parts from image filename.
    Returns (area_label, list_of_likely_parts)
    """
    name = Path(filename).stem.lower()
    
    for keyword, parts in FILENAME_HINTS.items():
        if keyword in name:
            area = keyword.replace("wind", "windshield").title()
            return f"{area} area", parts
    
    return "General area", []


def _get_vision_llm() -> ChatGoogleGenerativeAI | None:
    global _vision_llm
    if _vision_llm is not None:
        return _vision_llm
    if not GOOGLE_API_KEY:
        logger.warning("No GOOGLE_API_KEY — vision analysis unavailable")
        return None
    _vision_llm = ChatGoogleGenerativeAI(
        model=VISION_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        max_retries=1,
    )
    logger.info("Vision LLM (%s) initialized", VISION_MODEL)
    return _vision_llm


def _encode_image(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_string, mime_type)."""
    path = Path(image_path)
    ext = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, mime_type


def analyze_damage_photo(image_path: str) -> tuple[str, str, list[str]]:
    """
    Returns (vision_text, detected_area, hinted_parts)
    """
    filename = Path(image_path).name
    detected_area, hinted_parts = _detect_area_from_filename(filename)

    llm = _get_vision_llm()
    if llm is None:
        return "Vision analysis unavailable — no API key configured.", detected_area, hinted_parts

    try:
        b64_image, mime_type = _encode_image(image_path)
        message = HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}
            },
            {"type": "text", "text": VISION_ANALYSIS_PROMPT}
        ])
        response = llm.invoke([message])
        logger.info("Vision analysis complete")
        return str(response.content), detected_area, hinted_parts

    except Exception as e:
        logger.warning("Vision LLM failed: %s", str(e)[:100])
        return f"Vision analysis failed: {str(e)[:100]}", detected_area, hinted_parts


def _parse_claim_response(raw_json: str, claim: ClaimRequest) -> ClaimResponse:
    """Parse the LLM's JSON output into a typed ClaimResponse."""
    clean = raw_json.strip()
    # Strip markdown code fences if present
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    data = json.loads(clean)

    damaged_parts = [
        DamageDetail(
            part=d["part"],
            severity=d["severity"],
            repair_type=d["repair_type"],
            estimated_cost=float(d["estimated_cost"]),
        )
        for d in data.get("damaged_parts", [])
    ]

    return ClaimResponse(
        claimant_name=claim.claimant_name,
        vehicle=f"{claim.vehicle_make} {claim.vehicle_model} {claim.year}",
        incident_date=claim.incident_date,
        damaged_parts=damaged_parts,
        total_repair_estimate=float(data.get("total_repair_estimate", 0.0)),
        covered_amount=float(data.get("covered_amount", 0.0)),
        deductible=float(data.get("deductible", 0.0)),
        confidence=data.get("confidence", "Low"),
        degraded=False,
        notes=data.get("notes"),
    )


# ── Rule-based fallback estimator ─────────────────────────────────
# Indian market average repair costs (INR)
PART_COST_MAP = {
    "bumper":       {"minor": 3000,  "moderate": 8500,  "severe": 15000},
    "hood":         {"minor": 4000,  "moderate": 12000, "severe": 22000},
    "door":         {"minor": 3500,  "moderate": 10000, "severe": 18000},
    "headlight":    {"minor": 2000,  "moderate": 5000,  "severe": 9000},
    "taillight":    {"minor": 1500,  "moderate": 4000,  "severe": 7000},
    "windshield":   {"minor": 3000,  "moderate": 8000,  "severe": 14000},
    "fender":       {"minor": 3000,  "moderate": 9000,  "severe": 16000},
    "roof":         {"minor": 4000,  "moderate": 13000, "severe": 24000},
    "tyre":         {"minor": 2000,  "moderate": 5000,  "severe": 8000},
    "mirror":       {"minor": 800,   "moderate": 2000,  "severe": 4000},
    "trunk":        {"minor": 3000,  "moderate": 9000,  "severe": 16000},
    "radiator":     {"minor": 4000,  "moderate": 11000, "severe": 20000},
}

DEFAULT_PART_COST = {"minor": 2000, "moderate": 6000, "severe": 12000}


def _get_severity_from_cost(cost: float) -> str:
    if cost >= 10000:
        return "Severe"
    elif cost >= 4000:
        return "Moderate"
    else:
        return "Minor"

def _extract_damages_from_vision(
    vision_output: str, 
    description: str = "",
    hinted_parts: list[str] | None = None
) -> list[DamageDetail]:
    """
    Parse vision LLM text output and user description into DamageDetail list.
    Used as fallback when main LLM chain is rate limited.
    """
    damages = []
    combined_text = vision_output.lower() + "\n" + description.lower()
    lines = combined_text.splitlines()
    matched_keys = set()
    
    for line in lines:
        if not line.strip() or "damaged parts" in line:
            continue

        if "severe" in line.lower():
            severity_key = "severe"
        elif "moderate" in line.lower():
            severity_key = "moderate"
        else:
            severity_key = "minor"

        repair_type = "Replace" if any(
            w in line.lower() for w in ["replace", "replacement", "severe"]
        ) else "Repair"

        for part_key in PART_COST_MAP:
            if part_key in line.lower() and part_key not in matched_keys:
                cost = float(PART_COST_MAP[part_key][severity_key])
                severity = _get_severity_from_cost(cost)
                damages.append(DamageDetail(
                    part=part_key.title(),
                    severity=severity,
                    repair_type=repair_type,
                    estimated_cost=cost,
                ))
                matched_keys.add(part_key)

    if hinted_parts:
        for part_name in hinted_parts:
            part_key = part_name.lower()
            if part_key in PART_COST_MAP and part_key not in matched_keys:
                cost = float(PART_COST_MAP[part_key]["minor"])
                damages.append(DamageDetail(
                    part=part_name.title(),
                    severity=_get_severity_from_cost(cost),
                    repair_type="Repair",
                    estimated_cost=cost,
                ))
                matched_keys.add(part_key)

    return damages


def _build_fallback_response(
    claim: ClaimRequest, 
    vision_output: str,
    hinted_parts: list[str] | None = None
) -> ClaimResponse:
    """
    Build a best-effort ClaimResponse from vision text alone
    when all LLMs are rate limited — mirrors Phase 1 extractive fallback.
    """
    from backend.config import MOTOR_DEDUCTIBLE_PCT

    damaged_parts = _extract_damages_from_vision(vision_output, claim.incident_description, hinted_parts)

    if not damaged_parts:
        # Fallback to a default generic damage if nothing could be matched
        damaged_parts = [
            DamageDetail(
                part="General Body Damage",
                severity="Moderate",
                repair_type="Repair",
                estimated_cost=float(DEFAULT_PART_COST["moderate"]),
            )
        ]

    total = sum(d.estimated_cost for d in damaged_parts)
    deductible = round(total * MOTOR_DEDUCTIBLE_PCT, 2)
    covered = round(total - deductible, 2)

    return ClaimResponse(
        claimant_name=claim.claimant_name,
        vehicle=f"{claim.vehicle_make} {claim.vehicle_model} {claim.year}",
        incident_date=claim.incident_date,
        damaged_parts=damaged_parts,
        total_repair_estimate=round(total, 2),
        covered_amount=covered,
        deductible=deductible,
        confidence="Medium",
        degraded=True,
        notes=(
            "⚠️ AI providers busy — estimate based on offline rules and incident description. "
            "Resubmit for a full AI vision assessment."
        ),
    )


def process_motor_claim(claim: ClaimRequest, image_path: str) -> ClaimResponse:
    # ── Step 1: Vision analysis ─────────────────────────────────────
    vision_output, detected_area, hinted_parts = analyze_damage_photo(image_path)
    logger.info("Vision output preview: %s", vision_output[:120])

    if vision_output.startswith("Vision analysis"):
        image_analysis = "High traffic delayed the full visual assessment. Falling back to offline estimation rules."
    else:
        image_analysis = " ".join(
            vision_output.strip().splitlines()[:2]
        )[:200]

    # ── Step 2: Policy context via RAG ──────────────────────────────
    rag_query = (
        f"What does the policy cover for motor vehicle damage? "
        f"Policy number: {claim.policy_number}. "
        f"Vehicle: {claim.vehicle_make} {claim.vehicle_model}."
    )
    rag_result = query_rag(rag_query)
    policy_context = rag_result.get("answer", "No policy context found.")

    # ── Step 3: Build two-slot inputs for _try_llm_chain() ──────────
    context = (
        f"DAMAGE PHOTO ANALYSIS:\n{vision_output}\n\n"
        f"POLICY COVERAGE:\n{policy_context}"
    )
    question = (
        f"Claimant: {claim.claimant_name}\n"
        f"Vehicle: {claim.vehicle_make} {claim.vehicle_model} {claim.year}\n"
        f"Incident Date: {claim.incident_date}\n"
        f"Description: {claim.incident_description}"
    )

    raw_answer = _try_llm_chain(
        context=context,
        question=question,
        prompt_template=MOTOR_CLAIMS_PROMPT,
    )

    # ── Step 4: Parse or degrade ─────────────────────────────────────
    if raw_answer is None:
        logger.warning("LLM chain exhausted — using rule-based fallback")
        result = _build_fallback_response(claim, vision_output, hinted_parts)
    else:
        try:
            result = _parse_claim_response(raw_answer, claim)
        except Exception as e:
            logger.warning("Failed to parse claim response: %s", e)
            result = _build_fallback_response(claim, vision_output, hinted_parts)

    result.detected_area = detected_area
    result.image_analysis = image_analysis
    return result
