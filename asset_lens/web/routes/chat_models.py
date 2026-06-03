from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    context: dict[str, Any] | None = None
    use_rag: bool = True
    use_signals: bool = False
    use_portfolio: bool = False
    fast_mode: bool = True


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    confidence: float
    suggestions: list[str]
    related_questions: list[str]


class SignalsRequest(BaseModel):
    signal_type: str | None = None
    min_score: int = 50
    limit: int = 10


class RAGRequest(BaseModel):
    query: str
    k: int = 5


class RAGResponse(BaseModel):
    results: list[dict[str, Any]]
    total: int
