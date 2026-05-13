from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.schemas.documents import UpdateTitleRequest
from app.memory.db import (
    get_conversation_messages,
    get_conversations,
    update_conversation_title,
    delete_conversation,
)

router = APIRouter(tags=["conversations"])


@router.get("/api/conversations")
def list_conversations(
    user_id: str = Depends(get_current_user),
) -> list[dict]:
    return get_conversations(user_id)


@router.get("/api/conversations/{conv_id}/messages")
def list_messages(
    conv_id: str,
    user_id: str = Depends(get_current_user),
) -> list[dict]:
    return get_conversation_messages(conv_id, user_id)


@router.delete("/api/conversations/{conv_id}")
def delete_conv(
    conv_id: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, str]:
    delete_conversation(conv_id, user_id)
    return {"status": "deleted"}


@router.patch("/api/conversations/{conv_id}")
def update_title(
    conv_id: str,
    request: UpdateTitleRequest,
    user_id: str = Depends(get_current_user),
) -> dict[str, str]:
    update_conversation_title(conv_id, user_id, request.title)
    return {"status": "updated"}
