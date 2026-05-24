from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.api.schemas.documents import DocumentMetadata
from app.memory.db import (
    delete_document,
    get_document_chunks,
    get_documents,
    save_conversation,
    save_document,
    save_document_chunk,
)
from app.services.document_indexer import index_document_background
from app.services.document_service import parse_document, recursive_chunk_text
from app.services.rag.config import RAGConfig

router = APIRouter(tags=["documents"])


@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile,
    conversation_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Upload and index a document for RAG."""
    try:
        print(f"[API] Upload started: file={file.filename}, user={user_id}, conv_id={conversation_id}", file=sys.stderr)

        # Save file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        print(f"[API] File saved to temp: {tmp_path}", file=sys.stderr)

        # Detect content type
        content_type = file.content_type or "text/plain"
        print(f"[API] Content type: {content_type}", file=sys.stderr)

        # Parse document
        text = parse_document(tmp_path, content_type)
        # Sanitize null bytes — PostgreSQL rejects \u0000 in TEXT columns
        text = text.replace('\0', '')
        print(f"[API] Document parsed, length: {len(text)}", file=sys.stderr)

        # Recursive chunking
        chunks = recursive_chunk_text(
            text,
            chunk_size=RAGConfig.get_chunk_size(),
            overlap=RAGConfig.get_chunk_overlap(),
        )
        print(f"[API] Created {len(chunks)} chunks", file=sys.stderr)

        # Generate document ID
        doc_id = f"doc-{datetime.now().timestamp()}"
        print(f"[API] Generated doc_id: {doc_id}", file=sys.stderr)

        # Ensure conversation exists before saving document (FK constraint)
        now = datetime.now().isoformat()
        save_conversation(conversation_id, user_id, "New chat", now, now)

        # Save to database
        save_document(doc_id, conversation_id, user_id, file.filename, content_type, len(content))
        print(f"[API] Saved to database", file=sys.stderr)

        # Save chunks
        for idx, chunk in enumerate(chunks):
            chunk_id = f"chunk-{doc_id}-{idx}"
            save_document_chunk(chunk_id, doc_id, idx, chunk, len(chunk))
        print(f"[API] Saved all chunk metadata", file=sys.stderr)

        # Index in background (non-blocking)
        print(f"[API] Creating background task for indexing", file=sys.stderr)
        asyncio.create_task(index_document_background(doc_id, conversation_id, chunks))
        print(f"[API] Background task created", file=sys.stderr)

        os.unlink(tmp_path)

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "chunk_count": len(chunks),
            "status": "uploading",
        }
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/documents")
def list_documents(
    conversation_id: str,
    user_id: str = Depends(get_current_user),
) -> list[dict]:
    """List documents for a conversation."""
    docs = get_documents(conversation_id, user_id)
    result = []
    for doc in docs:
        chunks = get_document_chunks(doc["id"])
        result.append(
            DocumentMetadata(
                id=doc["id"],
                filename=doc["filename"],
                content_type=doc["content_type"],
                size_bytes=doc["size_bytes"],
                upload_date=doc["upload_date"],
                chunk_count=len(chunks),
            ).model_dump()
        )
    return result


@router.delete("/api/documents/{doc_id}")
def delete_doc(
    doc_id: str,
    conversation_id: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, str]:
    """Delete a document and its embeddings."""
    try:
        collection_name = (
            conversation_id
            if conversation_id.startswith("conv-")
            else f"conv-{conversation_id}"
        )
        from app.services.rag import get_rag_retrieval
        rag = get_rag_retrieval()
        rag.vector_store.delete_by_doc_id(collection_name, doc_id)

        delete_document(doc_id, user_id)
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
