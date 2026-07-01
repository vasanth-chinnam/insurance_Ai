import logging
from backend.models.travel_claim_schemas import TravelClaimRequest, TravelClaimResponse
from backend.services.rag_service import _try_llm_chain
from backend.prompts.travel_claim_prompt import TRAVEL_CLAIM_PROMPT

logger = logging.getLogger(__name__)

# ── Flight delay payout tiers ───────────────────────────────────────
DELAY_TIERS = [
    (2,  0,     "No payout — delay under 2 hours"),
    (4,  2000,  "Tier 1 — 2-4 hour delay"),
    (8,  5000,  "Tier 2 — 4-8 hour delay"),
    (24, 10000, "Tier 3 — 8-24 hour delay"),
    (999,20000, "Tier 4 — over 24 hour delay / cancellation"),
]

CANCELLATION_PAYOUT_PCT = 0.80   # 80% of sum insured
BAGGAGE_PAYOUT_CAP_PCT  = 0.50   # max 50% of sum insured for baggage


def _calculate_delay_payout(delay_hours: float, sum_insured: float) -> tuple[float, str]:
    for max_hours, payout, tier_label in DELAY_TIERS:
        if delay_hours <= max_hours:
            capped_payout = min(payout, sum_insured)
            return capped_payout, tier_label
    return 0.0, "No payout"


def _calculate_baggage_payout(baggage_value: float, sum_insured: float) -> tuple[float, str]:
    cap = sum_insured * BAGGAGE_PAYOUT_CAP_PCT
    payout = min(baggage_value, cap)
    tier = f"Baggage loss — capped at {int(BAGGAGE_PAYOUT_CAP_PCT*100)}% of sum insured" if baggage_value > cap else "Baggage loss — fully covered"
    return round(payout, 2), tier


def _calculate_cancellation_payout(sum_insured: float, reason: str) -> tuple[float, str]:
    valid_reasons = ["illness", "death", "visa rejection", "natural disaster", "medical emergency"]
    if any(r in reason.lower() for r in valid_reasons):
        payout = round(sum_insured * CANCELLATION_PAYOUT_PCT, 2)
        return payout, f"Trip cancellation — {int(CANCELLATION_PAYOUT_PCT*100)}% payout (valid reason)"
    else:
        payout = round(sum_insured * 0.30, 2)
        return payout, "Trip cancellation — 30% payout (reason needs verification)"


def _generate_explanation(
    request: TravelClaimRequest,
    payout: float,
    tier: str,
) -> tuple[str, bool]:

    context = f"""
Claim Type: {request.claim_type}
Route: {request.origin} → {request.destination}
Departure: {request.departure_date}
Delay Hours: {request.delay_hours}
Baggage Value: ₹{request.baggage_value:,.0f}
Sum Insured: ₹{request.sum_insured:,.0f}
Description: {request.description}

Payout Tier Applied: {tier}
Final Payout: ₹{payout:,.0f}
"""
    question = "Explain this travel insurance claim payout decision."

    answer = _try_llm_chain(
        context=context, question=question,
        prompt_template=TRAVEL_CLAIM_PROMPT,
    )

    if answer is None:
        return (
            f"Your {request.claim_type.replace('_', ' ')} claim for the "
            f"{request.origin} → {request.destination} trip has been processed. "
            f"{tier}. Final payout: ₹{payout:,.0f}. "
            f"Please submit supporting documents (boarding pass, delay certificate, "
            f"or baggage report) to finalize the claim."
        ), True

    return answer, False


def process_travel_claim(request: TravelClaimRequest) -> TravelClaimResponse:
    if request.claim_type == "flight_delay":
        payout, tier = _calculate_delay_payout(request.delay_hours or 0, request.sum_insured)
    elif request.claim_type == "baggage_loss":
        payout, tier = _calculate_baggage_payout(request.baggage_value or 0, request.sum_insured)
    elif request.claim_type == "trip_cancellation":
        payout, tier = _calculate_cancellation_payout(request.sum_insured, request.cancellation_reason or "")
    else:
        payout, tier = round(request.sum_insured * 0.5, 2), "Medical emergency — standard 50% advance"

    explanation, degraded = _generate_explanation(request, payout, tier)

    confidence = "High" if payout > 0 else "Medium"

    return TravelClaimResponse(
        claimant_name = request.claimant_name,
        policy_number  = request.policy_number,
        claim_type     = request.claim_type,
        route          = f"{request.origin} → {request.destination}",
        payout_tier    = tier,
        base_payout    = payout,
        deductions     = 0.0,
        final_payout   = payout,
        explanation    = explanation,
        confidence     = confidence,
        degraded       = degraded,
    )
