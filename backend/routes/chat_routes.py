import os
import shutil
import logging

from fastapi import APIRouter, UploadFile, File

from backend.models.schemas import ChatRequest, ChatResponse, UploadResponse
from backend.services.rag_service import ingest_file, query_rag
from backend.services.chat_service import chat_service
from backend.utils.router import route_query
from backend.config import POLICIES_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Central chat endpoint – routes the query and responds."""
    query = request.query
    route = route_query(query)

    # Record user message
    chat_service.add_message("user", query)

    # ── Route handling ──────────────────────────────────────────────
    confidence = "High"
    degraded = False
    if route == "policy_rag":
        result = query_rag(query)
        answer = result["answer"]
        sources = result["sources"]
        confidence = result.get("confidence", "Medium")
        degraded = result.get("degraded", False)

    elif route == "motor_claim":
        answer = "🚗 Motor Claim Estimator coming in Phase 2! Upload photos of vehicle damage and I'll estimate repair costs."
        sources = []

    elif route == "fraud_detection":
        answer = "🔍 Fraud Detection coming in Phase 3! I'll analyze claims for suspicious patterns."
        sources = []

    elif route == "risk_profiler":
        answer = "📊 Risk Profiler coming in Phase 4! I'll assess health and lifestyle risk factors."
        sources = []

    elif route == "crop_payout":
        answer = "🌾 Crop Insurance Agent coming in Phase 5! I'll check weather data and calculate crop payouts."
        sources = []

    elif route == "renewal_agent":
        answer = "🔄 Renewal Comparison coming in Phase 6! I'll compare policy renewal options for you."
        sources = []

    else:
        answer = "👋 I'm your AI Insurance Assistant! Ask me about your policy coverage, claim procedures, or any insurance question."
        sources = []

    # Record bot response
    chat_service.add_message("assistant", answer)

    return ChatResponse(
        answer=answer, 
        sources=sources, 
        route=route, 
        confidence=confidence,
        degraded=degraded
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF / TXT policy document for RAG ingestion."""
    os.makedirs(POLICIES_DIR, exist_ok=True)

    dest_path = os.path.join(POLICIES_DIR, file.filename)

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunk_count = ingest_file(dest_path)
        chat_service.add_message(
            "system",
            f"📄 Document '{file.filename}' uploaded and indexed ({chunk_count} chunks).",
        )
        return UploadResponse(
            status="success", filename=file.filename, chunks=chunk_count
        )
    except Exception as e:
        logger.exception("Failed to ingest %s", file.filename)
        return UploadResponse(status=f"error: {e}", filename=file.filename, chunks=0)


@router.get("/history")
async def get_history():
    """Return full chat history."""
    return {"history": chat_service.get_history()}


@router.delete("/history")
async def clear_history():
    """Clear chat history."""
    chat_service.clear_history()
    return {"status": "cleared"}
