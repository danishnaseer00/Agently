from __future__ import annotations

import asyncio
import sys
import traceback
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.schemas.chat import ChatRequest, ChatResponse
from app.api.helpers.sse import chunk_text, sse
from app.api.helpers.trace import format_trace
from app.services.chat_executor import build_executor
from app.services.research_service import run_research
from app.services.rag import get_rag_retrieval
from app.memory.db import save_conversation, save_message

router = APIRouter(tags=["chat"])


def _get_rag_context(request: ChatRequest) -> str | None:
    """Retrieve document context if RAG is enabled."""
    if not (request.use_rag and request.document_ids and request.conversation_id):
        print(f"[API] RAG not enabled - use_rag={request.use_rag}, has_docs={bool(request.document_ids)}, has_conv={bool(request.conversation_id)}", file=sys.stderr)
        return None

    try:
        print(f"[API] RAG enabled, retrieving documents...", file=sys.stderr)
        rag = get_rag_retrieval()
        collection_name = (
            request.conversation_id
            if request.conversation_id.startswith("conv-")
            else f"conv-{request.conversation_id}"
        )
        print(f"[API] Collection: {collection_name}, Doc IDs: {request.document_ids}", file=sys.stderr)
        chunks = rag.retrieve(request.message, collection_name, request.document_ids)
        print(f"[API] Retrieved {len(chunks)} chunks", file=sys.stderr)
        doc_context = rag.format_context(chunks)
        print(f"[API] Context length: {len(doc_context) if doc_context else 0}", file=sys.stderr)
        return doc_context
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return None


@router.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
) -> ChatResponse:
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = build_executor(request.temperature, request.max_results, request.tool_names)
    doc_context = _get_rag_context(request)

    answer, trace = run_research(executor, request.message, messages, doc_context)

    conv_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
    now = datetime.now().isoformat()

    save_conversation(conv_id, user_id, request.title or "New chat", now, now)
    save_message(f"user-{datetime.now().timestamp()}", conv_id, user_id, "user", request.message, now)
    save_message(f"assistant-{datetime.now().timestamp()}", conv_id, user_id, "assistant", answer, now)

    trace_payload = format_trace(trace) if request.debug else None
    return ChatResponse(answer=answer, trace=trace_payload)


@router.post("/api/chat/stream")
def chat_stream(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = build_executor(request.temperature, request.max_results, request.tool_names)
    doc_context = _get_rag_context(request)

    conv_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
    now = datetime.now().isoformat()
    save_conversation(conv_id, user_id, request.title or "New chat", now, now)
    save_message(f"user-{datetime.now().timestamp()}", conv_id, user_id, "user", request.message, now)

    async def event_stream():
        yield sse("status", {"state": "thinking"})
        answer, trace = run_research(executor, request.message, messages, doc_context)

        for step in format_trace(trace):
            yield sse("tool", step)

        for chunk in chunk_text(answer):
            yield sse("chunk", {"text": chunk})
            await asyncio.sleep(0)

        save_message(f"assistant-{datetime.now().timestamp()}", conv_id, user_id, "assistant", answer, now)
        yield sse("done", {"answer": answer})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
