import json
import logging
from pathlib import Path

from fastapi import APIRouter
from backend.models.crop_schemas import CropAnalyzeRequest, CropAgentResponse
from backend.services.crop_agent import run_crop_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crop", tags=["Crop Agent"])


@router.post("/analyze", response_model=CropAgentResponse)
def analyze_crop(request: CropAnalyzeRequest):
    return run_crop_agent(request)


@router.get("/farmers")
def list_farmers():
    """Return list of demo farmers for the UI dropdown."""
    try:
        with open(Path("data/mock_db/farmers.json")) as f:
            farmers = json.load(f)
        return [
            {
                "farmer_id": fa["farmer_id"],
                "name":      fa["name"],
                "location":  fa["location"],
                "crop_type": fa["crop_type"],
            }
            for fa in farmers
        ]
    except Exception:
        return []
