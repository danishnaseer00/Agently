from __future__ import annotations

import sys
import traceback

from app.services.rag import get_rag_retrieval


async def index_document_background(doc_id: str, conversation_id: str, chunks: list[str]) -> None:
    """Index document chunks into the RAG vector store in the background."""
    try:
        print(f"[API] Starting background indexing for {doc_id}", file=sys.stderr)
        rag = get_rag_retrieval()
        # Don't add "conv-" prefix if it already exists
        collection_name = (
            conversation_id
            if conversation_id.startswith("conv-")
            else f"conv-{conversation_id}"
        )
        print(f"[API] Using collection: {collection_name}", file=sys.stderr)
        print(f"[API] Indexing {len(chunks)} chunks", file=sys.stderr)
        rag.index_document(collection_name, doc_id, chunks)
        print(f"[API] Document {doc_id} indexed successfully", file=sys.stderr)
    except Exception as exc:
        print(f"[API] Background indexing error for {doc_id}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
