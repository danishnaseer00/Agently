from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.documents import UpdateTitleRequest
from app.memory.db import (
    delete_conversation,
    get_conversation_messages,
    get_conversations,
    save_conversation,
    update_conversation_title,
)

router = APIRouter(tags=["conversations"])


@router.get("/api/conversations")
def list_conversations() -> list[dict]:
    return get_conversations()


@router.get("/api/conversations/{conv_id}/messages")
def list_messages(conv_id: str) -> list[dict]:
    return get_conversation_messages(conv_id)


@router.delete("/api/conversations/{conv_id}")
def delete_conv(conv_id: str) -> dict[str, str]:
    delete_conversation(conv_id)
    return {"status": "deleted"}


@router.patch("/api/conversations/{conv_id}")
def update_title(conv_id: str, request: UpdateTitleRequest) -> dict[str, str]:
    update_conversation_title(conv_id, request.title)
    return {"status": "updated"}
