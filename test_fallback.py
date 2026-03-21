import json
import logging
from backend.models.claim_schemas import ClaimRequest
from backend.services.claims_service import _build_fallback_response

# Mock Claim
claim = ClaimRequest(
    claimant_name="Sneha Patil",
    vehicle_number="KA-01-AB-1234",
    vehicle_make="Hyundai",
    vehicle_model="i20",
    year=2021,
    incident_date="20-03-2026",
    incident_description="Got rear-ended in traffic.",
    policy_number="POL-2025-002"
)

# Mock Vision Output (as if Gemini Vision succeeded)
mock_vision_text = """
The image shows a car with the following damages:
- The rear bumper has severe cracks and needs replacement.
- The taillight (right side) is completely shattered (severe).
- The trunk has a moderate dent.
"""

response = _build_fallback_response(claim, mock_vision_text)

print(json.dumps(response.model_dump(), indent=2))
