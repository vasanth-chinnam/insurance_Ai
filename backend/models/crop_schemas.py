from pydantic import BaseModel, Field
from typing import Optional


class CropAnalyzeRequest(BaseModel):
    farmer_id:        str  = Field(..., description="Farmer ID e.g. F001")
    location:         str  = Field(..., description="Location for weather simulation")
    crop_type:        str  = Field(..., description="cotton | wheat | rice | bajra | sugarcane")
    policy_number:    str  = Field(..., description="Policy number")
    season:           str  = Field("kharif", description="kharif | rabi | zaid")
    simulate_drought: bool = Field(False, description="Force drought simulation for demo")


class WeatherData(BaseModel):
    rainfall_mm:        float   # monthly rainfall
    temperature_max_c:  float   # max temperature
    humidity_pct:       float   # humidity %
    wind_speed_kmh:     float   # wind speed
    ndvi_index:         float   # 0.0-1.0 (satellite crop health)
    soil_moisture_pct:  float   # soil moisture %


class ThresholdBreach(BaseModel):
    parameter:    str    # e.g. "Rainfall"
    actual_value: str    # e.g. "12mm"
    threshold:    str    # e.g. "< 20mm"
    severity:     str    # "Mild" | "Moderate" | "Severe"
    yield_impact: float  # % yield loss from this breach


class CropAgentResponse(BaseModel):
    farmer_id:            str
    farmer_name:          str
    location:             str
    crop_type:            str
    policy_number:        str
    sum_insured:          float
    weather_data:         WeatherData
    weather_source:       str         # "Live — Open-Meteo" | "Estimated — API unavailable" | "Simulated — Drought Mode"
    thresholds_breached:  list[ThresholdBreach]
    yield_loss_pct:       float       # 0-100
    payout_triggered:     bool
    payout_amount:        float       # in INR
    payout_status:        str         # "No Payout" | "Partial Payout" | "Full Payout"
    assessment_report:    str         # LLM or rule-based
    farmer_notification:  str         # SMS-style message to farmer
    confidence:           str
    degraded:             bool
