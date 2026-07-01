from pydantic import BaseModel, Field
from typing import Optional


class HealthClaimRequest(BaseModel):
    claimant_name:     str
    policy_number:     str
    patient_name:       str
    age:                int
    diagnosis:          str
    treatment_type:     str   = Field(..., description="OPD | IPD | Daycare | Surgery")
    hospital_name:      str
    admission_date:     str
    discharge_date:     str
    room_type:          str   = Field("General", description="General | Semi-Private | Private | ICU")
    total_bill_amount:  float
    sum_insured:        float


class BillItem(BaseModel):
    item:            str
    amount:          float
    eligible_amount: float
    status:          str    # "Covered" | "Capped" | "Excluded"
    reason:          str


class HealthClaimResponse(BaseModel):
    claimant_name:      str
    patient_name:        str
    policy_number:       str
    diagnosis:           str
    hospital_name:        str
    total_bill_amount:    float
    bill_breakdown:       list[BillItem]
    room_rent_cap:        float
    room_rent_excess:     float
    total_deductions:     float
    covered_amount:       float
    deductible:           float
    final_payout:         float
    explanation:          str
    confidence:           str
    degraded:             bool
