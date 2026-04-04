from pydantic import BaseModel, Field
from typing import Optional, Literal

InsuranceType = Literal["motor", "health", "travel", "crop"]


class ClaimRequest(BaseModel):
    insurance_type:       InsuranceType = Field("motor", description="motor | health | travel | crop")
    claimant_name:        str = Field(..., description="Full name of the person filing the claim")
    vehicle_number:       str = Field("", description="Vehicle registration number (motor only)")
    vehicle_make:         str = Field("", description="e.g. Honda, Toyota (motor only)")
    vehicle_model:        str = Field("", description="e.g. City, Innova (motor only)")
    year:                 int = Field(0, description="Year of manufacture (motor only)")
    incident_date:        str = Field(..., description="Date of incident DD-MM-YYYY")
    incident_description: str = Field(..., description="Brief description of what happened")
    policy_number:        str = Field(..., description="Insurance policy number")


class DamageDetail(BaseModel):
    part: str           # e.g. "Front bumper"
    severity: str       # "Minor" | "Moderate" | "Severe"
    repair_type: str    # "Repair" | "Replace"
    estimated_cost: float  # in INR


class ClaimResponse(BaseModel):
    insurance_type:        str = "motor"
    claimant_name:         str
    vehicle:               str                      # "Honda City 2020"
    incident_date:         str
    damaged_parts:         list[DamageDetail]
    total_repair_estimate: float                     # sum of all parts in INR
    covered_amount:        float                     # after policy deductions
    deductible:            float                     # amount claimant pays
    confidence:            str                       # "High" | "Medium" | "Low"
    degraded:              bool                      # True if Vision LLM or LLM chain failed
    notes:                 Optional[str] = None
    detected_area:         Optional[str] = None
    image_analysis:        Optional[str] = None
    fraud_check:           Optional[dict] = None
