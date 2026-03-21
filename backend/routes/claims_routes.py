import os
import shutil
import logging

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.services.claims_service import process_motor_claim
from backend.models.claim_schemas import ClaimRequest, ClaimResponse
from backend.config import CLAIMS_UPLOAD_DIR, MAX_IMAGE_SIZE_MB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/claims", tags=["Motor Claims"])

UPLOAD_DIR = CLAIMS_UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/motor", response_model=ClaimResponse)
async def submit_motor_claim(
    # ── Claim form fields ──────────────────────────────────────────
    claimant_name: str        = Form(..., description="Full name of the claimant"),
    vehicle_number: str       = Form(..., description="Vehicle registration number"),
    vehicle_make: str         = Form(..., description="e.g. Honda, Toyota"),
    vehicle_model: str        = Form(..., description="e.g. City, Innova"),
    year: int                 = Form(..., description="Year of manufacture"),
    incident_date: str        = Form(..., description="Date of incident DD-MM-YYYY"),
    incident_description: str = Form(..., description="Brief description of what happened"),
    policy_number: str        = Form(..., description="Insurance policy number"),
    # ── File uploads ───────────────────────────────────────────────
    damage_photo: UploadFile  = File(..., description="Photo of the vehicle damage (JPG/PNG)"),
    claim_pdf: UploadFile     = File(None, description="(Optional) Policy/claim PDF to ingest into RAG"),
):
    """
    Submit a motor insurance claim for AI-powered damage assessment.

    Returns a structured cost estimate with per-part breakdown,
    total repair estimate, covered amount, and confidence score.
    """
    # Validate image type early
    if not damage_photo.content_type or not damage_photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"damage_photo must be an image file (got: {damage_photo.content_type})",
        )

    # Validate image size
    if damage_photo.size and damage_photo.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum allowed size is {MAX_IMAGE_SIZE_MB}MB.",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save damage photo
    safe_photo_name = os.path.basename(damage_photo.filename or "damage.jpg")
    image_path = os.path.join(UPLOAD_DIR, safe_photo_name)
    with open(image_path, "wb") as f:
        shutil.copyfileobj(damage_photo.file, f)
    logger.info("Saved damage photo: %s", image_path)

    # Optionally ingest a claim/policy PDF into RAG
    if claim_pdf and claim_pdf.filename:
        safe_pdf_name = os.path.basename(claim_pdf.filename)
        pdf_path = os.path.join(UPLOAD_DIR, safe_pdf_name)
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(claim_pdf.file, f)
        try:
            from backend.services.rag_service import ingest_file
            chunks = ingest_file(pdf_path)
            logger.info("Claim PDF ingested: %s (%d chunks)", safe_pdf_name, chunks)
        except Exception as e:
            logger.warning("Could not ingest claim PDF '%s': %s", safe_pdf_name, e)

    # Build typed claim object
    claim = ClaimRequest(
        claimant_name=claimant_name,
        vehicle_number=vehicle_number,
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        year=year,
        incident_date=incident_date,
        incident_description=incident_description,
        policy_number=policy_number,
    )

    return process_motor_claim(claim, image_path)
