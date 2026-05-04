from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="New user message")
    history: list[ChatMessage] = Field(default_factory=list)
    temperature: float = 0.2
    max_results: int = 5
    debug: bool = False


class ChatResponse(BaseModel):
    answer: str
    trace: list[dict[str, str]] | None = None
