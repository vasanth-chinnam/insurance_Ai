from pydantic import BaseModel, Field
from typing import Optional, Literal

InsuranceType = Literal["health", "motor", "travel", "crop"]


# ── Domain-specific input models ──────────────────────────────────────

class HealthRiskInput(BaseModel):
    age:                int   = Field(..., description="Age in years")
    bmi:                float = Field(..., description="Body Mass Index")
    smoker:             bool  = Field(False)
    diabetic:           bool  = Field(False)
    hypertension:       bool  = Field(False)
    heart_condition:    bool  = Field(False)
    family_history:     bool  = Field(False, description="Family history of critical illness")
    exercise_frequency: int   = Field(0, description="Days per week of exercise")
    alcohol_units:      int   = Field(0, description="Units of alcohol per week")


class MotorRiskInput(BaseModel):
    age:                  int   = Field(..., description="Driver age")
    vehicle_age:          int   = Field(..., description="Vehicle age in years")
    accidents_last_5yr:   int   = Field(0,  description="Accidents in last 5 years")
    traffic_violations:   int   = Field(0,  description="Traffic violations in last 3 years")
    annual_km:            int   = Field(..., description="Annual kilometers driven")
    vehicle_type:         str   = Field("sedan", description="sedan | suv | bike | truck")
    night_driving:        bool  = Field(False, description="Regularly drives at night")
    parking:              str   = Field("street", description="garage | street | open")


class TravelRiskInput(BaseModel):
    trips_per_year:       int   = Field(..., description="Number of trips per year")
    avg_trip_duration:    int   = Field(..., description="Average trip duration in days")
    destinations:         list[str] = Field(default_factory=list, description="List of destination countries")
    adventure_sports:     bool  = Field(False)
    pre_existing:         bool  = Field(False, description="Pre-existing medical conditions")
    age:                  int   = Field(..., description="Traveller age")
    business_travel:      bool  = Field(False)


class CropRiskInput(BaseModel):
    crop_type:            str   = Field("wheat", description="wheat | rice | cotton | sugarcane | vegetables")
    land_area_acres:      float = Field(..., description="Total land area in acres")
    location_state:       str   = Field(..., description="Indian state")
    irrigation:           str   = Field("rainfed", description="rainfed | partial | full")
    season:               str   = Field("kharif", description="kharif | rabi | zaid")
    past_crop_losses:     int   = Field(0,  description="Number of crop losses in last 5 years")
    soil_quality:         str   = Field("medium", description="poor | medium | good")


# ── Main request ──────────────────────────────────────────────────────

class RiskProfileRequest(BaseModel):
    insurance_type: InsuranceType
    policy_number:  Optional[str] = None
    health:         Optional[HealthRiskInput]  = None
    motor:          Optional[MotorRiskInput]   = None
    travel:         Optional[TravelRiskInput]  = None
    crop:           Optional[CropRiskInput]    = None


# ── Response ──────────────────────────────────────────────────────────

class RiskFactor(BaseModel):
    factor:      str    # e.g. "High BMI"
    impact:      str    # "High" | "Medium" | "Low"
    points:      int    # score contribution
    suggestion:  str    # what to do about it


class RiskResponse(BaseModel):
    insurance_type:      str
    risk_score:          int              # 0–100
    risk_category:       str              # Low | Medium | High | Very High
    risk_factors:        list[RiskFactor]
    premium_adjustment:  str              # e.g. "+25%" or "-10%" or "Standard"
    base_premium_range:  str              # e.g. "₹8,000 – ₹12,000/year"
    recommendation:      str              # LLM-generated advice
    confidence:          str
    degraded:            bool
