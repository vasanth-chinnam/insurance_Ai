from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    query: str
    insurance_type: Optional[str] = None  # motor | health | travel | crop


class SourceInfo(BaseModel):
    text: str
    section: str = ""
    page: str = ""
    insurance_type: str = ""
    source: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = []
    route: str = "general_chat"
    confidence: str = "Medium"
    degraded: bool = False


class UploadResponse(BaseModel):
    status: str
    filename: str
    chunks: int
