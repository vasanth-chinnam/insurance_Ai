from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class SourceInfo(BaseModel):
    text: str
    section: str = ""
    page: str = ""


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
