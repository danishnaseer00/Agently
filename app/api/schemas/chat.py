from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="New user message")
    history: list[ChatMessage] = Field(default_factory=list)
    conversation_id: str | None = Field(default=None, description="Conversation ID for persistence")
    title: str | None = Field(default=None, description="Conversation title")
    tool_names: list[str] | None = Field(default=None, description="List of tools to use")
    temperature: float = 0.2
    max_results: int = 5
    debug: bool = False
    document_ids: list[str] | None = Field(default=None, description="IDs of documents to search in")
    use_rag: bool = Field(default=False, description="Enable RAG for document retrieval")


class ChatResponse(BaseModel):
    answer: str
    trace: list[dict[str, str]] | None = None
