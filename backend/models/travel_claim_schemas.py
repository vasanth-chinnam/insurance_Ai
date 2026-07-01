from pydantic import BaseModel, Field
from typing import Optional


class TravelClaimRequest(BaseModel):
    claimant_name:    str
    policy_number:    str
    claim_type:       str   = Field(..., description="flight_delay | baggage_loss | trip_cancellation | medical_emergency")
    origin:           str
    destination:      str
    departure_date:   str
    delay_hours:       Optional[float] = 0
    baggage_value:     Optional[float] = 0
    cancellation_reason: Optional[str] = ""
    sum_insured:       float
    description:       str


class TravelClaimResponse(BaseModel):
    claimant_name:       str
    policy_number:        str
    claim_type:           str
    route:                str       # "Delhi → Singapore"
    payout_tier:          str       # description of which tier applied
    base_payout:          float
    deductions:           float
    final_payout:         float
    explanation:          str
    confidence:           str
    degraded:             bool
