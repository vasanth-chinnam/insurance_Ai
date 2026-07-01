import logging
from backend.models.health_claim_schemas import (
    HealthClaimRequest, HealthClaimResponse, BillItem
)
from backend.services.rag_service import _try_llm_chain
from backend.prompts.health_claim_prompt import HEALTH_CLAIM_PROMPT

logger = logging.getLogger(__name__)

# ── Room rent caps by room type (% of sum insured per day) ────────────
ROOM_RENT_CAPS_PCT = {
    "General":      0.01,    # 1% of sum insured per day
    "Semi-Private":  0.015,
    "Private":       0.02,
    "ICU":           0.03,
}

# ── Standard exclusions ────────────────────────────────────────────────
EXCLUDED_ITEMS = ["cosmetic", "dental routine", "spectacles", "vitamins",
                   "registration fee", "admin charge", "telephone"]

DEDUCTIBLE_PCT = 0.05  # 5% standard deductible


def _calculate_stay_days(admission: str, discharge: str) -> int:
    from datetime import datetime
    try:
        a = datetime.strptime(admission, "%d-%m-%Y")
        d = datetime.strptime(discharge, "%d-%m-%Y")
        return max((d - a).days, 1)
    except Exception:
        return 1


def _calculate_room_rent_cap(
    sum_insured: float, room_type: str, stay_days: int
) -> float:
    pct = ROOM_RENT_CAPS_PCT.get(room_type, ROOM_RENT_CAPS_PCT["General"])
    return round(sum_insured * pct * stay_days, 2)


def _build_bill_breakdown(
    total_bill: float, room_cap: float, room_excess: float
) -> list[BillItem]:
    """Simulate a realistic bill breakdown from the total amount."""
    room_rent_pct      = 0.25
    medicines_pct      = 0.30
    doctor_fees_pct    = 0.20
    diagnostics_pct    = 0.15
    other_pct          = 0.10

    items = [
        BillItem(
            item="Room Rent",
            amount=round(total_bill * room_rent_pct, 2),
            eligible_amount=round(total_bill * room_rent_pct - room_excess, 2),
            status="Capped" if room_excess > 0 else "Covered",
            reason=f"Room rent capped at policy limit" if room_excess > 0 else "Within policy limit",
        ),
        BillItem(
            item="Medicines",
            amount=round(total_bill * medicines_pct, 2),
            eligible_amount=round(total_bill * medicines_pct, 2),
            status="Covered",
            reason="Fully covered under policy",
        ),
        BillItem(
            item="Doctor Fees",
            amount=round(total_bill * doctor_fees_pct, 2),
            eligible_amount=round(total_bill * doctor_fees_pct, 2),
            status="Covered",
            reason="Fully covered under policy",
        ),
        BillItem(
            item="Diagnostics",
            amount=round(total_bill * diagnostics_pct, 2),
            eligible_amount=round(total_bill * diagnostics_pct, 2),
            status="Covered",
            reason="Fully covered under policy",
        ),
        BillItem(
            item="Other Charges",
            amount=round(total_bill * other_pct, 2),
            eligible_amount=round(total_bill * other_pct * 0.5, 2),
            status="Excluded",
            reason="Admin/registration charges partially excluded",
        ),
    ]
    return items


def _generate_explanation(
    request: HealthClaimRequest,
    breakdown: list[BillItem],
    room_cap: float,
    room_excess: float,
    final_payout: float,
) -> tuple[str, bool]:

    context = f"""
Patient: {request.patient_name} | Age: {request.age}
Diagnosis: {request.diagnosis}
Hospital: {request.hospital_name}
Treatment: {request.treatment_type} | Room Type: {request.room_type}
Total Bill: ₹{request.total_bill_amount:,.0f}
Room Rent Cap: ₹{room_cap:,.0f} | Excess: ₹{room_excess:,.0f}

Bill Breakdown:
{chr(10).join(f'- {b.item}: ₹{b.amount:,.0f} → Eligible: ₹{b.eligible_amount:,.0f} ({b.status}) — {b.reason}' for b in breakdown)}

Final Payout: ₹{final_payout:,.0f}
"""
    question = "Explain this health insurance claim payout decision."

    answer = _try_llm_chain(
        context=context, question=question,
        prompt_template=HEALTH_CLAIM_PROMPT,
    )

    if answer is None:
        return (
            f"Your claim for {request.diagnosis} treatment at {request.hospital_name} "
            f"has been processed. Total bill of ₹{request.total_bill_amount:,.0f} was reviewed "
            f"against your policy limits. "
            + (f"Room rent excess of ₹{room_excess:,.0f} was deducted as your room type exceeded "
               f"the policy's room rent cap. " if room_excess > 0 else "")
            + f"Final approved payout: ₹{final_payout:,.0f}."
        ), True

    return answer, False


def process_health_claim(request: HealthClaimRequest) -> HealthClaimResponse:
    stay_days   = _calculate_stay_days(request.admission_date, request.discharge_date)
    room_cap    = _calculate_room_rent_cap(request.sum_insured, request.room_type, stay_days)
    room_billed = request.total_bill_amount * 0.25
    room_excess = max(0, round(room_billed - room_cap, 2))

    breakdown = _build_bill_breakdown(request.total_bill_amount, room_cap, room_excess)

    total_eligible    = sum(b.eligible_amount for b in breakdown)
    deductible        = round(total_eligible * DEDUCTIBLE_PCT, 2)
    final_payout      = round(min(total_eligible - deductible, request.sum_insured), 2)
    total_deductions  = round(request.total_bill_amount - final_payout, 2)

    explanation, degraded = _generate_explanation(
        request, breakdown, room_cap, room_excess, final_payout
    )

    confidence = "High" if room_excess == 0 else "Medium"

    return HealthClaimResponse(
        claimant_name      = request.claimant_name,
        patient_name        = request.patient_name,
        policy_number       = request.policy_number,
        diagnosis           = request.diagnosis,
        hospital_name       = request.hospital_name,
        total_bill_amount   = request.total_bill_amount,
        bill_breakdown      = breakdown,
        room_rent_cap       = room_cap,
        room_rent_excess    = room_excess,
        total_deductions    = total_deductions,
        covered_amount      = total_eligible,
        deductible          = deductible,
        final_payout        = final_payout,
        explanation         = explanation,
        confidence          = confidence,
        degraded            = degraded,
    )
