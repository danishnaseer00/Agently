from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


# ─── Conversations ───────────────────────────────────────────────────────────


def save_conversation(
    conv_id: str,
    user_id: str,
    title: str,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    supabase = get_supabase()
    result = supabase.table("conversations").upsert({
        "id": conv_id,
        "user_id": user_id,
        "title": title,
        "created_at": created_at,
        "updated_at": updated_at,
    }).execute()
    return result.data[0] if result.data else {}


def get_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    supabase = get_supabase()
    result = supabase.table("conversations") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("updated_at", desc=True) \
        .limit(limit) \
        .execute()
    return result.data if result.data else []


def get_conversation(conv_id: str, user_id: str) -> dict[str, Any] | None:
    supabase = get_supabase()
    result = supabase.table("conversations") \
        .select("*") \
        .eq("id", conv_id) \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()
    return result.data[0] if result.data else None


def delete_conversation(conv_id: str, user_id: str) -> None:
    supabase = get_supabase()
    # Messages and documents are deleted cascade by Supabase FK
    supabase.table("conversations") \
        .delete() \
        .eq("id", conv_id) \
        .eq("user_id", user_id) \
        .execute()


def update_conversation_title(conv_id: str, user_id: str, title: str) -> None:
    supabase = get_supabase()
    supabase.table("conversations") \
        .update({"title": title, "updated_at": datetime.now().isoformat()}) \
        .eq("id", conv_id) \
        .eq("user_id", user_id) \
        .execute()


# ─── Messages ────────────────────────────────────────────────────────────────


def save_message(
    msg_id: str,
    conv_id: str,
    user_id: str,
    role: str,
    content: str,
    created_at: str,
) -> dict[str, Any]:
    supabase = get_supabase()
    result = supabase.table("messages").insert({
        "id": msg_id,
        "conversation_id": conv_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": created_at,
    }).execute()

    # Update conversation's updated_at
    supabase.table("conversations") \
        .update({"updated_at": created_at}) \
        .eq("id", conv_id) \
        .execute()

    return result.data[0] if result.data else {}


def get_conversation_messages(conv_id: str, user_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase()
    result = supabase.table("messages") \
        .select("*") \
        .eq("conversation_id", conv_id) \
        .eq("user_id", user_id) \
        .order("created_at") \
        .execute()
    return result.data if result.data else []


# ─── Documents ───────────────────────────────────────────────────────────────


def save_document(
    doc_id: str,
    conversation_id: str,
    user_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    supabase = get_supabase()
    result = supabase.table("documents").insert({
        "id": doc_id,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "upload_date": datetime.now().isoformat(),
    }).execute()
    return result.data[0] if result.data else {}


def get_documents(conversation_id: str, user_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase()
    result = supabase.table("documents") \
        .select("*") \
        .eq("conversation_id", conversation_id) \
        .eq("user_id", user_id) \
        .order("upload_date", desc=True) \
        .execute()
    return result.data if result.data else []


def delete_document(document_id: str, user_id: str) -> None:
    supabase = get_supabase()
    supabase.table("documents") \
        .delete() \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()


def save_document_chunk(
    chunk_id: str,
    document_id: str,
    chunk_index: int,
    content: str,
    chunk_size: int,
) -> dict[str, Any]:
    supabase = get_supabase()
    result = supabase.table("document_chunks").insert({
        "id": chunk_id,
        "document_id": document_id,
        "chunk_index": chunk_index,
        "content": content,
        "chunk_size": chunk_size,
    }).execute()
    return result.data[0] if result.data else {}


def get_document_chunks(document_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase()
    result = supabase.table("document_chunks") \
        .select("*") \
        .eq("document_id", document_id) \
        .order("chunk_index") \
        .execute()
    return result.data if result.data else []
