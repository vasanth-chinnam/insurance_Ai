from pydantic import BaseModel, Field
from typing import Optional


class FraudRequest(BaseModel):
    claim_type:          str   = Field(..., description="motor | health | travel | crop")
    policy_number:       str   = Field(..., description="Policy number to validate")
    claim_amount:        float = Field(..., description="Claimed amount in INR")
    days_after_incident: int   = Field(..., description="Days between incident and claim filing")
    previous_claims:     int   = Field(0,   description="Number of previous claims by this customer")
    incident_date:       str   = Field(..., description="DD-MM-YYYY")
    description:         str   = Field(..., description="Incident description in claimant's words")
    
    # Optional fields for data cross-referencing
    flight_number:       Optional[str] = Field(None, description="For travel claims (e.g. AI-101)")
    hospital_name:       Optional[str] = Field(None, description="For health claims")
    workshop_name:       Optional[str] = Field(None, description="For motor claims")


class FraudResponse(BaseModel):
    fraud_score:          int            # 0–100
    risk_level:           str            # Low | Medium | High
    verdict:              str            # Genuine | Suspicious | Fraudulent
    reasons:              list[str]      # list of red flags
    investigation_report: str            # LLM-generated report
    recommended_action:   str            # Auto Approve | Manual Review | Reject & Escalate
    confidence:           str            # Low | Medium | High
    degraded:             bool           # True if LLM unavailable
