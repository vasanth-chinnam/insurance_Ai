import json
import random
import logging
import httpx
from pathlib import Path

from backend.models.crop_schemas import (
    CropAnalyzeRequest, CropAgentResponse,
    WeatherData, ThresholdBreach
)
from backend.services.rag_service import _try_llm_chain
from backend.prompts.crop_prompt import CROP_AGENT_PROMPT, FARMER_NOTIFICATION_TEMPLATE

logger = logging.getLogger(__name__)

FARMERS_DB_PATH = Path("data/mock_db/farmers.json")


# ── Farmer DB ─────────────────────────────────────────────────────────

def _load_farmer(farmer_id: str) -> dict | None:
    try:
        with open(FARMERS_DB_PATH) as f:
            farmers = json.load(f)
        return next((fa for fa in farmers if fa["farmer_id"] == farmer_id), None)
    except Exception as e:
        logger.warning("Could not load farmers DB: %s", e)
        return None


# ── Geocoding ─────────────────────────────────────────────────────────

def _geocode_location(location: str) -> tuple[float, float]:
    """
    Convert location name -> (latitude, longitude)
    Uses Open-Meteo Geocoding API — free, no key needed.
    Falls back to center of India if not found.
    """
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": location, "count": 1, "language": "en", "format": "json"}
        with httpx.Client(timeout=10) as client:
            res = client.get(url, params=params)
            data = res.json()

        if data.get("results"):
            result = data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            logger.info("Geocoded '%s' -> lat=%s lon=%s", location, lat, lon)
            return lat, lon
        else:
            logger.warning("Location '%s' not found — using India center", location)
            return 20.5937, 78.9629  # center of India

    except Exception as e:
        logger.warning("Geocoding failed: %s — using India center", e)
        return 20.5937, 78.9629


# ── Real weather from Open-Meteo ──────────────────────────────────────

def _fetch_real_weather(lat: float, lon: float) -> dict:
    """
    Fetch real current weather from Open-Meteo.
    Free, no API key, no rate limits.
    Returns raw weather dict.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
        ],
        "daily": [
            "precipitation_sum",
            "temperature_2m_max",
            "soil_moisture_0_to_1cm",
        ],
        "timezone":       "Asia/Kolkata",
        "forecast_days":  7,
    }

    with httpx.Client(timeout=15) as client:
        res = client.get(url, params=params)
        data = res.json()

    logger.info("Open-Meteo response received for lat=%s lon=%s", lat, lon)
    return data


def _parse_weather(raw: dict) -> tuple[float, float, float, float, float]:
    """
    Extract key values from Open-Meteo response.
    Returns (rainfall_7day_mm, temp_max_c, humidity_pct, wind_kmh, soil_moisture_pct)
    """
    try:
        daily   = raw.get("daily", {})
        current = raw.get("current", {})

        # 7-day total rainfall
        precip_list = daily.get("precipitation_sum", [0])
        rainfall_7d = round(sum(p for p in precip_list if p is not None), 2)

        # Max temperature over 7 days
        temp_list = daily.get("temperature_2m_max", [30])
        temp_max  = round(max(t for t in temp_list if t is not None), 1)

        # Current humidity
        humidity = float(current.get("relative_humidity_2m", 50))

        # Current wind speed
        wind_speed = float(current.get("wind_speed_10m", 15))

        # Soil moisture — Open-Meteo returns 0-1, convert to %
        soil_list = daily.get("soil_moisture_0_to_1cm", [0.3])
        valid_soil = [s for s in soil_list if s is not None]
        soil_raw  = sum(valid_soil) / max(len(valid_soil), 1)
        soil_pct  = round(soil_raw * 100, 1)

        return rainfall_7d, temp_max, humidity, wind_speed, soil_pct

    except Exception as e:
        logger.warning("Weather parsing failed: %s — using safe defaults", e)
        return 45.0, 32.0, 55.0, 15.0, 35.0


def _estimate_ndvi(rainfall_mm: float, temp_max_c: float, soil_pct: float) -> float:
    """
    Estimate NDVI from weather parameters.
    Real NDVI needs satellite imagery — this is a realistic proxy.
    NDVI range: 0.0 (bare/dead) to 1.0 (lush vegetation)
    """
    base = 0.75

    # Rainfall impact
    if rainfall_mm < 10:
        base -= 0.35
    elif rainfall_mm < 25:
        base -= 0.20
    elif rainfall_mm < 40:
        base -= 0.10

    # Heat stress impact
    if temp_max_c > 44:
        base -= 0.25
    elif temp_max_c > 40:
        base -= 0.15
    elif temp_max_c > 38:
        base -= 0.05

    # Soil moisture impact
    if soil_pct < 15:
        base -= 0.20
    elif soil_pct < 25:
        base -= 0.10

    # Small natural variance
    base += random.uniform(-0.03, 0.03)

    return round(max(0.05, min(base, 0.95)), 2)


def _get_weather(
    location: str,
    simulate_drought: bool,
) -> tuple[WeatherData, str]:
    """
    Main weather fetch function.
    Returns (WeatherData, source_label)
    source_label: "Live — Open-Meteo" or "Simulated — Drought Mode"
    """
    if simulate_drought:
        # Forced drought simulation for demo
        weather = WeatherData(
            rainfall_mm       = round(random.uniform(2, 14), 2),
            temperature_max_c = round(random.uniform(41, 47), 1),
            humidity_pct      = round(random.uniform(12, 28), 1),
            wind_speed_kmh    = round(random.uniform(22, 45), 1),
            ndvi_index        = round(random.uniform(0.08, 0.22), 2),
            soil_moisture_pct = round(random.uniform(4, 16), 1),
        )
        return weather, "Simulated — Drought Mode"

    try:
        # Step 1 — Geocode location
        lat, lon = _geocode_location(location)

        # Step 2 — Fetch real weather
        raw = _fetch_real_weather(lat, lon)

        # Step 3 — Parse
        rainfall, temp_max, humidity, wind, soil = _parse_weather(raw)

        # Step 4 — Estimate NDVI
        ndvi = _estimate_ndvi(rainfall, temp_max, soil)

        weather = WeatherData(
            rainfall_mm       = rainfall,
            temperature_max_c = temp_max,
            humidity_pct      = humidity,
            wind_speed_kmh    = wind,
            ndvi_index        = ndvi,
            soil_moisture_pct = soil,
        )
        return weather, "Live — Open-Meteo"

    except Exception as e:
        logger.warning("Real weather fetch failed: %s — using seasonal estimate", e)

        # Fallback seasonal estimate
        weather = WeatherData(
            rainfall_mm       = round(random.uniform(20, 80), 2),
            temperature_max_c = round(random.uniform(28, 38), 1),
            humidity_pct      = round(random.uniform(45, 70), 1),
            wind_speed_kmh    = round(random.uniform(10, 25), 1),
            ndvi_index        = round(random.uniform(0.4, 0.7), 2),
            soil_moisture_pct = round(random.uniform(30, 55), 1),
        )
        return weather, "Estimated — API unavailable"


# ── Threshold engine ──────────────────────────────────────────────────

def _check_thresholds(weather: WeatherData, crop_type: str) -> list[ThresholdBreach]:
    breaches = []

    # Rainfall
    if weather.rainfall_mm < 10:
        breaches.append(ThresholdBreach(
            parameter    = "7-day Rainfall",
            actual_value = f"{weather.rainfall_mm}mm",
            threshold    = "< 10mm (Severe drought)",
            severity     = "Severe",
            yield_impact = 40.0,
        ))
    elif weather.rainfall_mm < 25:
        breaches.append(ThresholdBreach(
            parameter    = "7-day Rainfall",
            actual_value = f"{weather.rainfall_mm}mm",
            threshold    = "< 25mm (Moderate drought)",
            severity     = "Moderate",
            yield_impact = 25.0,
        ))
    elif weather.rainfall_mm < 40:
        breaches.append(ThresholdBreach(
            parameter    = "7-day Rainfall",
            actual_value = f"{weather.rainfall_mm}mm",
            threshold    = "< 40mm (Mild drought)",
            severity     = "Mild",
            yield_impact = 10.0,
        ))

    # NDVI
    if weather.ndvi_index < 0.2:
        breaches.append(ThresholdBreach(
            parameter    = "NDVI Crop Health",
            actual_value = f"{weather.ndvi_index:.2f}",
            threshold    = "< 0.20 (Severe crop stress)",
            severity     = "Severe",
            yield_impact = 35.0,
        ))
    elif weather.ndvi_index < 0.3:
        breaches.append(ThresholdBreach(
            parameter    = "NDVI Crop Health",
            actual_value = f"{weather.ndvi_index:.2f}",
            threshold    = "< 0.30 (Moderate crop stress)",
            severity     = "Moderate",
            yield_impact = 20.0,
        ))

    # Temperature
    if weather.temperature_max_c > 44:
        breaches.append(ThresholdBreach(
            parameter    = "Maximum Temperature",
            actual_value = f"{weather.temperature_max_c}°C",
            threshold    = "> 44°C (Severe heat stress)",
            severity     = "Severe",
            yield_impact = 30.0,
        ))
    elif weather.temperature_max_c > 40:
        breaches.append(ThresholdBreach(
            parameter    = "Maximum Temperature",
            actual_value = f"{weather.temperature_max_c}°C",
            threshold    = "> 40°C (Moderate heat stress)",
            severity     = "Moderate",
            yield_impact = 15.0,
        ))

    # Soil moisture
    if weather.soil_moisture_pct < 15:
        breaches.append(ThresholdBreach(
            parameter    = "Soil Moisture",
            actual_value = f"{weather.soil_moisture_pct}%",
            threshold    = "< 15% (Critically dry)",
            severity     = "Severe",
            yield_impact = 25.0,
        ))
    elif weather.soil_moisture_pct < 25:
        breaches.append(ThresholdBreach(
            parameter    = "Soil Moisture",
            actual_value = f"{weather.soil_moisture_pct}%",
            threshold    = "< 25% (Dry conditions)",
            severity     = "Moderate",
            yield_impact = 12.0,
        ))

    return breaches


# ── Yield loss + payout ───────────────────────────────────────────────

def _calculate_yield_loss(breaches: list[ThresholdBreach]) -> float:
    if not breaches:
        return 0.0
    total = sum(b.yield_impact for b in breaches)
    if len(breaches) > 1:
        total *= 0.85   # diminishing returns
    return min(round(total, 1), 100.0)


def _calculate_payout(yield_loss_pct: float, sum_insured: float) -> tuple[float, str]:
    if yield_loss_pct < 20:
        return 0.0, "No Payout"
    elif yield_loss_pct < 50:
        return round((yield_loss_pct / 100) * sum_insured, 2), "Partial Payout"
    else:
        return round((yield_loss_pct / 100) * sum_insured, 2), "Full Payout"


# ── Farmer notification ───────────────────────────────────────────────

def _build_notification(
    farmer: dict,
    payout_status: str,
    payout_amount: float,
    breaches: list[ThresholdBreach],
) -> str:
    if payout_status == "No Payout":
        payout_line = "No payout has been triggered at this time."
        reason      = "Weather conditions are within acceptable thresholds."
    else:
        payout_line = (
            f"Payout Amount: ₹{payout_amount:,.0f} will be credited "
            f"to your account {farmer.get('bank_account', 'on file')}."
        )
        top_breach = max(breaches, key=lambda b: b.yield_impact)
        reason = (
            f"{top_breach.parameter} recorded at {top_breach.actual_value} "
            f"— {top_breach.threshold}."
        )

    return FARMER_NOTIFICATION_TEMPLATE.format(
        farmer_name   = farmer.get("name", "Farmer"),
        crop_type     = farmer.get("crop_type", "crop").title(),
        location      = farmer.get("location", "your location"),
        payout_status = payout_status,
        payout_line   = payout_line,
        reason        = reason,
    )


# ── LLM assessment ────────────────────────────────────────────────────

def _generate_assessment(
    farmer: dict,
    weather: WeatherData,
    breaches: list[ThresholdBreach],
    yield_loss_pct: float,
    payout_amount: float,
    payout_status: str,
    weather_source: str,
) -> tuple[str, bool]:

    context = f"""
Farmer: {farmer.get('name')} | Location: {farmer.get('location')}
Crop: {farmer.get('crop_type', '').title()} | Land: {farmer.get('land_area_acres')} acres
Season: {farmer.get('season', '').title()} | Sum Insured: ₹{farmer.get('sum_insured', 0):,}
Weather Source: {weather_source}

Real-time Weather Data (7-day):
- Rainfall:      {weather.rainfall_mm}mm
- Max Temp:      {weather.temperature_max_c}°C
- Humidity:      {weather.humidity_pct}%
- Wind Speed:    {weather.wind_speed_kmh} km/h
- NDVI Index:    {weather.ndvi_index:.2f}
- Soil Moisture: {weather.soil_moisture_pct}%

Threshold Breaches:
{chr(10).join(
    f'- {b.parameter}: {b.actual_value} ({b.threshold}) — {b.severity} — {b.yield_impact}% yield impact'
    for b in breaches
) or 'None detected'}

Yield Loss: {yield_loss_pct}%
Payout: {payout_status} — ₹{payout_amount:,.0f}
"""

    question = "Generate a crop insurance assessment report for this farmer."
    answer = _try_llm_chain(
        context         = context,
        question        = question,
        prompt_template = CROP_AGENT_PROMPT,
    )

    if answer is None:
        if not breaches:
            return (
                f"Real-time weather monitoring ({weather_source}) for "
                f"{farmer.get('name')}'s {farmer.get('crop_type')} at "
                f"{farmer.get('location')} shows conditions within normal parameters. "
                f"Rainfall: {weather.rainfall_mm}mm, Temp: {weather.temperature_max_c}°C, "
                f"NDVI: {weather.ndvi_index:.2f}. No payout triggered."
            ), True

        top = max(breaches, key=lambda b: b.yield_impact)
        return (
            f"Real-time monitoring ({weather_source}) detected "
            f"{len(breaches)} threshold breach(es) for {farmer.get('name')}'s "
            f"{farmer.get('crop_type')} at {farmer.get('location')}. "
            f"Primary concern: {top.parameter} at {top.actual_value} ({top.severity}). "
            f"Estimated yield loss: {yield_loss_pct}%. "
            f"Payout decision: {payout_status} of ₹{payout_amount:,.0f}."
        ), True

    return answer, False


# ── Main entry point ──────────────────────────────────────────────────

def run_crop_agent(request: CropAnalyzeRequest) -> CropAgentResponse:
    """
    Real-time crop agent pipeline:
    1. Load farmer data
    2. Fetch REAL weather from Open-Meteo
    3. Check thresholds
    4. Calculate yield loss + payout
    5. Generate assessment report
    6. Build farmer notification
    """

    # Step 1 — Load farmer
    farmer = _load_farmer(request.farmer_id)
    if not farmer:
        farmer = {
            "farmer_id":       request.farmer_id,
            "name":            f"Farmer {request.farmer_id}",
            "location":        request.location,
            "crop_type":       request.crop_type,
            "policy_number":   request.policy_number,
            "sum_insured":     50000,
            "land_area_acres": 5.0,
            "bank_account":    "XXXX-XXXX-0000",
            "season":          request.season,
        }

    # Step 2 — Real weather fetch
    weather, weather_source = _get_weather(
        location         = request.location or farmer.get("location", "India"),
        simulate_drought = request.simulate_drought,
    )
    logger.info("Weather source: %s", weather_source)

    # Step 3 — Thresholds
    breaches = _check_thresholds(weather, request.crop_type)

    # Step 4 — Yield loss + payout
    yield_loss_pct               = _calculate_yield_loss(breaches)
    payout_amount, payout_status = _calculate_payout(
        yield_loss_pct, farmer.get("sum_insured", 50000)
    )
    payout_triggered = payout_status != "No Payout"

    # Step 5 — Assessment
    assessment, degraded = _generate_assessment(
        farmer, weather, breaches,
        yield_loss_pct, payout_amount, payout_status, weather_source,
    )

    # Step 6 — Notification
    notification = _build_notification(
        farmer, payout_status, payout_amount, breaches,
    )

    confidence = (
        "High"   if len(breaches) >= 2 else
        "Medium" if len(breaches) == 1 else
        "High"
    )

    return CropAgentResponse(
        farmer_id           = request.farmer_id,
        farmer_name         = farmer.get("name", "Unknown"),
        location            = farmer.get("location", request.location),
        crop_type           = farmer.get("crop_type", request.crop_type),
        policy_number       = farmer.get("policy_number", request.policy_number),
        sum_insured         = float(farmer.get("sum_insured", 50000)),
        weather_data        = weather,
        weather_source      = weather_source,
        thresholds_breached = breaches,
        yield_loss_pct      = yield_loss_pct,
        payout_triggered    = payout_triggered,
        payout_amount       = payout_amount,
        payout_status       = payout_status,
        assessment_report   = assessment,
        farmer_notification = notification,
        confidence          = confidence,
        degraded            = degraded,
    )
