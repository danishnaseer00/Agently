from __future__ import annotations

"""
Supabase-backed database layer.
All functions require a user_id for row-level security.
Delegates to app.memory.supabase_db for the actual Supabase operations.
"""

from typing import Any

from app.memory.supabase_db import (
    get_supabase as _get_supabase,
    save_conversation as _save_conversation,
    get_conversations as _get_conversations,
    get_conversation as _get_conversation,
    delete_conversation as _delete_conversation,
    update_conversation_title as _update_conversation_title,
    save_message as _save_message,
    get_conversation_messages as _get_conversation_messages,
    save_document as _save_document,
    get_documents as _get_documents,
    delete_document as _delete_document,
    save_document_chunk as _save_document_chunk,
    get_document_chunks as _get_document_chunks,
)


# ─── Conversations ───────────────────────────────────────────────────────────

def save_conversation(
    conv_id: str,
    user_id: str,
    title: str,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    """Save/upsert a conversation for the given user."""
    return _save_conversation(conv_id, user_id, title, created_at, updated_at)


def get_conversations(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Get all conversations for a user."""
    return _get_conversations(user_id, limit)


def get_conversation_messages(conv_id: str, user_id: str) -> list[dict[str, Any]]:
    """Get messages for a conversation, scoped to user."""
    return _get_conversation_messages(conv_id, user_id)


def delete_conversation(conv_id: str, user_id: str) -> None:
    """Delete a conversation and its cascade, scoped to user."""
    _delete_conversation(conv_id, user_id)


def update_conversation_title(conv_id: str, user_id: str, title: str) -> None:
    """Update conversation title, scoped to user."""
    _update_conversation_title(conv_id, user_id, title)


# ─── Messages ────────────────────────────────────────────────────────────────

def save_message(
    msg_id: str,
    conv_id: str,
    user_id: str,
    role: str,
    content: str,
    created_at: str,
) -> dict[str, Any]:
    """Save a message for the given user."""
    return _save_message(msg_id, conv_id, user_id, role, content, created_at)


# ─── Documents ───────────────────────────────────────────────────────────────

def save_document(
    doc_id: str,
    conversation_id: str,
    user_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    """Save document metadata, scoped to user."""
    return _save_document(doc_id, conversation_id, user_id, filename, content_type, size_bytes)


def get_documents(conversation_id: str, user_id: str) -> list[dict[str, Any]]:
    """Get all documents for a conversation, scoped to user."""
    return _get_documents(conversation_id, user_id)


def delete_document(document_id: str, user_id: str) -> None:
    """Delete a document and its cascade, scoped to user."""
    _delete_document(document_id, user_id)


def save_document_chunk(
    chunk_id: str,
    document_id: str,
    chunk_index: int,
    content: str,
    chunk_size: int,
) -> dict[str, Any]:
    """Save a document chunk."""
    return _save_document_chunk(chunk_id, document_id, chunk_index, content, chunk_size)


def get_document_chunks(document_id: str) -> list[dict[str, Any]]:
    """Get all chunks for a document."""
    return _get_document_chunks(document_id)


def init_db() -> None:
    """No-op: Supabase schema is managed via migrations."""
    pass