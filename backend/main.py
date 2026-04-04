import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.routes.chat_routes import router as chat_router
from backend.routes.claims_routes import router as claims_router
from backend.routes.fraud_routes import router as fraud_router
from backend.api.risk_routes import router as risk_router
from backend.services.rag_service import ingest_file
from backend.config import POLICIES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup, auto-ingest any policy documents already present."""
    policies_dir = str(os.path.abspath(POLICIES_DIR))
    if os.path.isdir(policies_dir):
        for fname in os.listdir(policies_dir):
            fpath = str(os.path.join(policies_dir, fname))
            if fname.lower().endswith((".pdf", ".txt", ".md")):
                # Detect insurance type from filename
                name_lower = fname.lower()
                if "motor" in name_lower or "vehicle" in name_lower or "auto" in name_lower:
                    itype = "motor"
                elif "health" in name_lower or "medical" in name_lower:
                    itype = "health"
                elif "travel" in name_lower or "flight" in name_lower:
                    itype = "travel"
                elif "crop" in name_lower or "agri" in name_lower:
                    itype = "crop"
                else:
                    itype = "general"
                try:
                    count = ingest_file(fpath, insurance_type=itype)
                    logger.info("Auto-ingested %s as [%s] (%d chunks)", fname, itype, count)
                except Exception:
                    logger.exception("Failed to auto-ingest %s", fname)
    else:
        logger.info("No policies directory found at %s, skipping auto-ingest", policies_dir)
    yield


app = FastAPI(title="AI Insurance Platform", lifespan=lifespan)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(chat_router, prefix="/api")
app.include_router(claims_router)
app.include_router(fraud_router)
app.include_router(risk_router)


@app.get("/")
def home():
    return {"message": "Insurance AI Platform Running 🚀"}
