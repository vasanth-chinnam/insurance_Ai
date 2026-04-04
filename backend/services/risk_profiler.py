import logging
from backend.models.risk_schemas import (
    RiskProfileRequest, RiskResponse, RiskFactor,
    HealthRiskInput, MotorRiskInput, TravelRiskInput, CropRiskInput
)
from backend.services.rag_service import _try_llm_chain
from backend.prompts.risk_prompt import RISK_PROFILER_PROMPT

logger = logging.getLogger(__name__)


# ── High-risk travel destinations ────────────────────────────────────
HIGH_RISK_COUNTRIES  = {"afghanistan", "syria", "iraq", "somalia", "yemen",
                        "libya", "sudan", "ukraine", "myanmar"}
MED_RISK_COUNTRIES   = {"pakistan", "bangladesh", "nepal", "kenya",
                        "egypt", "indonesia", "philippines"}


# ── Domain rule engines ───────────────────────────────────────────────

def _health_rules(h: HealthRiskInput) -> list[RiskFactor]:
    factors = []

    # Age
    if h.age >= 60:
        factors.append(RiskFactor(
            factor="Senior age group (60+)",
            impact="High", points=25,
            suggestion="Consider annual health checkups and preventive care plans."
        ))
    elif h.age >= 45:
        factors.append(RiskFactor(
            factor="Middle age group (45–59)",
            impact="Medium", points=15,
            suggestion="Regular health screenings recommended."
        ))

    # BMI
    if h.bmi >= 35:
        factors.append(RiskFactor(
            factor=f"Severely obese BMI ({h.bmi:.1f})",
            impact="High", points=20,
            suggestion="Structured weight management program recommended."
        ))
    elif h.bmi >= 30:
        factors.append(RiskFactor(
            factor=f"Obese BMI ({h.bmi:.1f})",
            impact="Medium", points=12,
            suggestion="Diet and exercise plan can significantly reduce risk."
        ))
    elif h.bmi >= 25:
        factors.append(RiskFactor(
            factor=f"Overweight BMI ({h.bmi:.1f})",
            impact="Low", points=6,
            suggestion="Maintain healthy weight through regular exercise."
        ))

    # Conditions
    if h.smoker:
        factors.append(RiskFactor(
            factor="Active smoker",
            impact="High", points=20,
            suggestion="Quitting smoking for 1+ year can reduce premium loading."
        ))
    if h.diabetic:
        factors.append(RiskFactor(
            factor="Diabetic",
            impact="High", points=15,
            suggestion="Maintain HbA1c below 7% to demonstrate controlled diabetes."
        ))
    if h.hypertension:
        factors.append(RiskFactor(
            factor="Hypertension",
            impact="Medium", points=12,
            suggestion="Controlled BP below 130/80 mmHg reduces risk loading."
        ))
    if h.heart_condition:
        factors.append(RiskFactor(
            factor="Heart condition",
            impact="High", points=20,
            suggestion="Cardiologist clearance letter can support claim validity."
        ))
    if h.family_history:
        factors.append(RiskFactor(
            factor="Family history of critical illness",
            impact="Medium", points=10,
            suggestion="Genetic screening and early detection plans recommended."
        ))

    # Positive factors (reduce score)
    if h.exercise_frequency >= 4:
        factors.append(RiskFactor(
            factor="Active lifestyle (4+ days/week exercise)",
            impact="Low", points=-8,
            suggestion="Keep it up — this positively impacts your premium."
        ))
    alcohol = min(h.alcohol_units, 100)
    if alcohol > 14:
        factors.append(RiskFactor(
            factor=f"High alcohol consumption ({alcohol} units/week)",
            impact="Medium", points=10,
            suggestion="Reducing to under 14 units/week improves risk profile."
        ))

    return factors


def _motor_rules(m: MotorRiskInput) -> list[RiskFactor]:
    factors = []

    # Driver age
    if m.age < 25:
        factors.append(RiskFactor(
            factor="Young driver (under 25)",
            impact="High", points=20,
            suggestion="Defensive driving course can reduce premium loading."
        ))
    elif m.age > 70:
        factors.append(RiskFactor(
            factor="Senior driver (70+)",
            impact="Medium", points=15,
            suggestion="Annual driving assessment recommended."
        ))

    # Vehicle age
    if m.vehicle_age > 10:
        factors.append(RiskFactor(
            factor=f"Old vehicle ({m.vehicle_age} years)",
            impact="High", points=20,
            suggestion="Older vehicles have higher breakdown and safety risk."
        ))
    elif m.vehicle_age > 5:
        factors.append(RiskFactor(
            factor=f"Ageing vehicle ({m.vehicle_age} years)",
            impact="Medium", points=10,
            suggestion="Regular servicing records reduce risk loading."
        ))

    # Accidents
    if m.accidents_last_5yr >= 3:
        factors.append(RiskFactor(
            factor=f"High accident history ({m.accidents_last_5yr} in 5 years)",
            impact="High", points=25,
            suggestion="Advanced driver training and dashcam installation recommended."
        ))
    elif m.accidents_last_5yr >= 1:
        factors.append(RiskFactor(
            factor=f"Accident history ({m.accidents_last_5yr} in 5 years)",
            impact="Medium", points=12,
            suggestion="Claim-free years progressively reduce your premium."
        ))

    # Violations
    if m.traffic_violations >= 3:
        factors.append(RiskFactor(
            factor=f"Multiple traffic violations ({m.traffic_violations})",
            impact="High", points=20,
            suggestion="Traffic violations directly increase premium loading."
        ))
    elif m.traffic_violations >= 1:
        factors.append(RiskFactor(
            factor=f"Traffic violations ({m.traffic_violations})",
            impact="Medium", points=10,
            suggestion="Clean driving record for 2 years resets loading."
        ))

    # Annual km
    if m.annual_km > 30000:
        factors.append(RiskFactor(
            factor=f"Very high mileage ({m.annual_km:,} km/year)",
            impact="Medium", points=12,
            suggestion="High mileage increases wear and accident probability."
        ))

    # Vehicle type
    if m.vehicle_type == "bike":
        factors.append(RiskFactor(
            factor="Two-wheeler (higher risk category)",
            impact="High", points=15,
            suggestion="Helmet usage and defensive riding reduce claim risk."
        ))
    elif m.vehicle_type == "truck":
        factors.append(RiskFactor(
            factor="Commercial vehicle",
            impact="Medium", points=10,
            suggestion="Commercial use attracts higher premium category."
        ))

    # Night driving
    if m.night_driving:
        factors.append(RiskFactor(
            factor="Regular night driving",
            impact="Medium", points=8,
            suggestion="Night driving increases accident risk by 3x statistically."
        ))

    # Parking
    if m.parking == "street":
        factors.append(RiskFactor(
            factor="Street parking",
            impact="Low", points=5,
            suggestion="Garage parking reduces theft and damage risk."
        ))

    return factors


def _travel_rules(t: TravelRiskInput) -> list[RiskFactor]:
    factors = []

    # Trip frequency
    if t.trips_per_year > 10:
        factors.append(RiskFactor(
            factor=f"Very frequent traveller ({t.trips_per_year} trips/year)",
            impact="High", points=20,
            suggestion="Annual multi-trip policy is more cost-effective."
        ))
    elif t.trips_per_year > 5:
        factors.append(RiskFactor(
            factor=f"Frequent traveller ({t.trips_per_year} trips/year)",
            impact="Medium", points=10,
            suggestion="Consider multi-trip annual cover."
        ))

    # Duration
    if t.avg_trip_duration > 30:
        factors.append(RiskFactor(
            factor=f"Long trip duration ({t.avg_trip_duration} days avg)",
            impact="Medium", points=12,
            suggestion="Extended stays increase health and liability exposure."
        ))

    # Destinations
    dest_lower = [d.lower() for d in t.destinations]
    high_risk  = [d for d in dest_lower if d in HIGH_RISK_COUNTRIES]
    med_risk   = [d for d in dest_lower if d in MED_RISK_COUNTRIES]

    if high_risk:
        factors.append(RiskFactor(
            factor=f"High-risk destinations: {', '.join(high_risk)}",
            impact="High", points=25,
            suggestion="Travel advisories should be checked before each trip."
        ))
    elif med_risk:
        factors.append(RiskFactor(
            factor=f"Medium-risk destinations: {', '.join(med_risk)}",
            impact="Medium", points=12,
            suggestion="Ensure medical evacuation cover is included."
        ))

    # Adventure sports
    if t.adventure_sports:
        factors.append(RiskFactor(
            factor="Adventure sports participation",
            impact="High", points=20,
            suggestion="Ensure adventure sports rider is added to policy."
        ))

    # Pre-existing conditions
    if t.pre_existing:
        factors.append(RiskFactor(
            factor="Pre-existing medical conditions",
            impact="High", points=18,
            suggestion="Declare all conditions — non-disclosure voids claims."
        ))

    # Age
    if t.age >= 70:
        factors.append(RiskFactor(
            factor="Senior traveller (70+)",
            impact="High", points=20,
            suggestion="Senior travel plans with higher medical limits recommended."
        ))
    elif t.age >= 60:
        factors.append(RiskFactor(
            factor="Senior traveller (60–69)",
            impact="Medium", points=12,
            suggestion="Medical cover of minimum $100,000 recommended."
        ))

    return factors


def _crop_rules(c: CropRiskInput) -> list[RiskFactor]:
    factors = []

    # Irrigation
    if c.irrigation == "rainfed":
        factors.append(RiskFactor(
            factor="Rainfed irrigation (weather dependent)",
            impact="High", points=25,
            suggestion="Drip irrigation investment significantly reduces weather risk."
        ))
    elif c.irrigation == "partial":
        factors.append(RiskFactor(
            factor="Partial irrigation",
            impact="Medium", points=12,
            suggestion="Full irrigation system reduces premium loading."
        ))

    # Past losses
    if c.past_crop_losses >= 3:
        factors.append(RiskFactor(
            factor=f"High crop loss history ({c.past_crop_losses} in 5 years)",
            impact="High", points=25,
            suggestion="Crop diversification and soil health improvement recommended."
        ))
    elif c.past_crop_losses >= 1:
        factors.append(RiskFactor(
            factor=f"Previous crop losses ({c.past_crop_losses})",
            impact="Medium", points=12,
            suggestion="Loss-free seasons progressively reduce loading."
        ))

    # Soil quality
    if c.soil_quality == "poor":
        factors.append(RiskFactor(
            factor="Poor soil quality",
            impact="High", points=20,
            suggestion="Soil treatment and organic farming practices reduce risk."
        ))

    # High risk crops
    high_risk_crops = {"vegetables", "cotton"}
    if c.crop_type.lower() in high_risk_crops:
        factors.append(RiskFactor(
            factor=f"High-risk crop type ({c.crop_type})",
            impact="Medium", points=12,
            suggestion=f"{c.crop_type.title()} is highly weather-sensitive — ensure weather index cover."
        ))

    # Season
    if c.season == "kharif":
        factors.append(RiskFactor(
            factor="Kharif season (monsoon dependent)",
            impact="Medium", points=10,
            suggestion="Monsoon variability is the primary risk factor for kharif crops."
        ))

    # Large land area
    if c.land_area_acres > 50:
        factors.append(RiskFactor(
            factor=f"Large land area ({c.land_area_acres} acres)",
            impact="Low", points=5,
            suggestion="Large farms benefit from diversified crop portfolio."
        ))

    return factors


# ── Score aggregator ──────────────────────────────────────────────────

def _aggregate_score(factors: list[RiskFactor]) -> int:
    total = sum(f.points for f in factors)
    return max(0, min(total, 100))


def _get_risk_category(score: int) -> str:
    if score >= 70:
        return "Very High"
    elif score >= 50:
        return "High"
    elif score >= 30:
        return "Medium"
    else:
        return "Low"


def _get_premium_adjustment(score: int) -> tuple[str, str]:
    """Returns (adjustment_pct, base_premium_range) by score."""
    if score >= 70:
        return "+40% to +60%", "₹18,000 – ₹30,000/year"
    elif score >= 50:
        return "+20% to +40%", "₹12,000 – ₹18,000/year"
    elif score >= 30:
        return "+5% to +20%",  "₹8,000 – ₹12,000/year"
    else:
        return "Standard or -5%", "₹5,000 – ₹8,000/year"


# ── LLM recommendation ────────────────────────────────────────────────

def _generate_recommendation(
    insurance_type: str,
    score: int,
    category: str,
    factors: list[RiskFactor],
    input_data: dict,
) -> tuple[str, bool]:
    """Returns (recommendation_text, degraded)"""

    context = f"""
Insurance Type: {insurance_type.title()}
Risk Score: {score}/100
Risk Category: {category}
Risk Factors Identified:
{chr(10).join(f'- {f.factor} (Impact: {f.impact}, +{f.points} pts): {f.suggestion}' for f in factors) or 'None detected'}
Customer Data: {input_data}
"""
    question = f"Generate a personalized risk profile recommendation for this {insurance_type} insurance customer."

    answer = _try_llm_chain(
        context=context,
        question=question,
        prompt_template=RISK_PROFILER_PROMPT,
    )

    if answer is None:
        # Rule-based fallback recommendation
        if not factors:
            return (
                f"Your {insurance_type} risk profile is clean with a score of {score}/100. "
                "You qualify for standard or discounted premium rates. "
                "Maintain your current lifestyle to keep premiums low."
            ), True

        top_factors = sorted(factors, key=lambda f: f.points, reverse=True)[:3]
        suggestions = " ".join(f.suggestion for f in top_factors)
        return (
            f"Your {insurance_type} risk score is {score}/100 ({category} risk). "
            f"Key concerns: {', '.join(f.factor for f in top_factors)}. "
            f"Suggestions: {suggestions}"
        ), True

    return answer, False


# ── Main entry point ──────────────────────────────────────────────────

def profile_risk(request: RiskProfileRequest) -> RiskResponse:
    itype = request.insurance_type

    # Route to correct domain engine
    if itype == "health" and request.health:
        factors    = _health_rules(request.health)
        input_dict = request.health.model_dump()
    elif itype == "motor" and request.motor:
        factors    = _motor_rules(request.motor)
        input_dict = request.motor.model_dump()
    elif itype == "travel" and request.travel:
        factors    = _travel_rules(request.travel)
        input_dict = request.travel.model_dump()
    elif itype == "crop" and request.crop:
        factors    = _crop_rules(request.crop)
        input_dict = request.crop.model_dump()
    else:
        return RiskResponse(
            insurance_type     = itype,
            risk_score         = 0,
            risk_category      = "Low",
            risk_factors       = [],
            premium_adjustment = "Standard",
            base_premium_range = "₹5,000 – ₹8,000/year",
            recommendation     = f"⚠️ Please provide {itype} risk data.",
            confidence         = "Low",
            degraded           = False,
        )

    score                        = _aggregate_score(factors)
    category                     = _get_risk_category(score)
    adjustment, premium_range    = _get_premium_adjustment(score)
    recommendation, degraded     = _generate_recommendation(
        itype, score, category, factors, input_dict
    )
    confidence = (
        "High"   if len(factors) >= 4 else
        "Medium" if len(factors) >= 2 else
        "Low"
    )

    return RiskResponse(
        insurance_type     = itype,
        risk_score         = score,
        risk_category      = category,
        risk_factors       = factors,
        premium_adjustment = adjustment,
        base_premium_range = premium_range,
        recommendation     = recommendation,
        confidence         = confidence,
        degraded           = degraded,
    )
