from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime
from functools import lru_cache
from typing import Iterable, Optional

from dotenv import load_dotenv
from pathlib import Path

# Load .env immediately at module import
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse, UpdateTitleRequest, DocumentMetadata
from app.agent.agent import build_agent
from app.core.config import load_settings
from app.core.llm import build_llm
from app.memory.db import (
    delete_conversation,
    get_conversation_messages,
    get_conversations,
    init_db,
    save_conversation,
    save_message,
    update_conversation_title,
    save_document,
    save_document_chunk,
    get_documents,
    get_document_chunks,
    delete_document,
)
from app.services.research_service import run_research
from app.services.document_service import (
    parse_document,
    recursive_chunk_text,
)
from app.services.rag import get_rag_retrieval
from app.tools.search import build_web_search_tool
from app.tools.scraper import fetch_url
from app.tools.file_tool import read_file, list_files
from app.tools.write_file import write_file

app = FastAPI(title="ReAct Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@lru_cache(maxsize=1)
def get_settings():
    return load_settings()


def _format_trace(steps: list[object]) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for action, observation in steps:
        formatted.append(
            {
                "tool": str(getattr(action, "tool", "unknown")),
                "tool_input": str(getattr(action, "tool_input", "")),
                "observation": str(observation),
            }
        )
    return formatted


def _chunk_text(text: str, size: int = 80) -> Iterable[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]


def _sse(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=True)
    return f"event: {event}\ndata: {payload}\n\n"


def _build_executor(temperature: float, max_results: int, tool_names: list[str] | None = None):
    import sys
    settings = get_settings()

    available = {
        "web_search": build_web_search_tool(settings, max_results),
        "fetch_url": fetch_url,
        "read_file": read_file,
        "list_files": list_files,
        "write_file": write_file,
    }

    if tool_names:
        tools = [available[name] for name in tool_names if name in available]
    else:
        tools = [available["web_search"], available["fetch_url"], available["read_file"], available["list_files"], available["write_file"]]

    tool_names_list = [t.name for t in tools]
    print(f"\n[DEBUG] Building executor with tools: {tool_names_list}", file=sys.stderr)

    llm = build_llm(settings, temperature, tools)
    executor = build_agent(llm, tools)

    print(f"[DEBUG] Agent tools: {[t.name for t in executor.tools]}", file=sys.stderr)
    return executor


@app.get("/api/tools")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": "web_search", "description": "Search the web for current information, news, facts"},
            {"name": "fetch_url", "description": "Fetch content from a URL"},
            {"name": "read_file", "description": "Read files from AI-workingdir folder"},
            {"name": "list_files", "description": "List files in AI-workingdir folder"},
            {"name": "write_file", "description": "Write files to AI-workingdir folder"},
        ]
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    import sys
    print("[API] Health check received", file=sys.stderr)
    return {"status": "ok"}


@app.post("/api/test-upload")
async def test_upload(file: UploadFile) -> dict:
    import sys
    print(f"[API] Test upload called with file: {file.filename}", file=sys.stderr)
    return {"status": "ok", "filename": file.filename}


async def _index_document_background(doc_id: str, conversation_id: str, chunks: list[str]) -> None:
    """Index document in background."""
    try:
        import sys
        print(f"[API] Starting background indexing for {doc_id}", file=sys.stderr)
        rag = get_rag_retrieval()
        # Don't add "conv-" prefix if it already exists
        collection_name = conversation_id if conversation_id.startswith("conv-") else f"conv-{conversation_id}"
        print(f"[API] Using collection: {collection_name}", file=sys.stderr)
        print(f"[API] Indexing {len(chunks)} chunks", file=sys.stderr)
        rag.index_document(collection_name, doc_id, chunks)
        print(f"[API] Document {doc_id} indexed successfully", file=sys.stderr)
    except Exception as exc:
        import sys
        import traceback
        print(f"[API] Background indexing error for {doc_id}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile, conversation_id: str) -> dict:
    """Upload and index a document for RAG."""
    import sys
    try:
        print(f"[API] Upload started: file={file.filename}, conv_id={conversation_id}", file=sys.stderr)

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
        print(f"[API] Document parsed, length: {len(text)}", file=sys.stderr)

        # Recursive chunking
        from app.services.rag.config import RAGConfig
        chunks = recursive_chunk_text(
            text,
            chunk_size=RAGConfig.CHUNK_SIZE,
            overlap=RAGConfig.CHUNK_OVERLAP,
        )
        print(f"[API] Created {len(chunks)} chunks", file=sys.stderr)

        # Generate document ID
        doc_id = f"doc-{datetime.now().timestamp()}"
        print(f"[API] Generated doc_id: {doc_id}", file=sys.stderr)

        # Save to database
        metadata = json.dumps({
            "original_name": file.filename,
            "chunk_count": len(chunks),
        })
        save_document(doc_id, conversation_id, file.filename, content_type, len(content), metadata)
        print(f"[API] Saved to database", file=sys.stderr)

        # Save chunks
        for idx, chunk in enumerate(chunks):
            chunk_id = f"chunk-{doc_id}-{idx}"
            save_document_chunk(chunk_id, doc_id, idx, chunk, len(chunk))
        print(f"[API] Saved all chunk metadata", file=sys.stderr)

        # Index in background (non-blocking)
        print(f"[API] Creating background task for indexing", file=sys.stderr)
        asyncio.create_task(_index_document_background(doc_id, conversation_id, chunks))
        print(f"[API] Background task created", file=sys.stderr)

        import os
        os.unlink(tmp_path)

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "chunk_count": len(chunks),
            "status": "uploading",
        }
    except Exception as exc:
        import sys
        import traceback
        print(f"[API] Upload error: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"error": str(exc), "status": "failed"}


@app.get("/api/documents")
def list_documents(conversation_id: str) -> list[dict]:
    """List documents for a conversation."""
    docs = get_documents(conversation_id)
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


@app.delete("/api/documents/{doc_id}")
def delete_doc(doc_id: str, conversation_id: str) -> dict[str, str]:
    """Delete a document and its embeddings."""
    try:
        # Delete from vector DB
        collection_name = conversation_id if conversation_id.startswith("conv-") else f"conv-{conversation_id}"
        rag = get_rag_retrieval()
        rag.vector_store.delete_by_doc_id(collection_name, doc_id)

        # Delete from database
        delete_document(doc_id)

        return {"status": "deleted"}
    except Exception as exc:
        return {"error": str(exc), "status": "failed"}



@app.on_event("startup")
def startup():
    from app.services.rag.config import RAGConfig
    init_db()
    get_settings()  # Load .env file
    RAGConfig.validate()  # Validate Qdrant configuration


@app.get("/api/conversations")
def list_conversations() -> list[dict]:
    return get_conversations()


@app.get("/api/conversations/{conv_id}/messages")
def list_messages(conv_id: str) -> list[dict]:
    return get_conversation_messages(conv_id)


@app.delete("/api/conversations/{conv_id}")
def delete_conv(conv_id: str) -> dict[str, str]:
    delete_conversation(conv_id)
    return {"status": "deleted"}


@app.patch("/api/conversations/{conv_id}")
def update_title(conv_id: str, request: UpdateTitleRequest) -> dict[str, str]:
    update_conversation_title(conv_id, request.title)
    return {"status": "updated"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    import sys
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = _build_executor(request.temperature, request.max_results, request.tool_names)

    # Retrieve documents if RAG is enabled
    doc_context = None
    print(f"[API] Chat request: use_rag={request.use_rag}, doc_ids={request.document_ids}, conv_id={request.conversation_id}", file=sys.stderr)

    if request.use_rag and request.document_ids and request.conversation_id:
        try:
            print(f"[API] RAG enabled, retrieving documents...", file=sys.stderr)
            rag = get_rag_retrieval()
            # Don't add "conv-" prefix if it already exists
            collection_name = request.conversation_id if request.conversation_id.startswith("conv-") else f"conv-{request.conversation_id}"
            print(f"[API] Collection: {collection_name}, Doc IDs: {request.document_ids}", file=sys.stderr)
            chunks = rag.retrieve(
                request.message,
                collection_name,
                request.document_ids,
            )
            print(f"[API] Retrieved {len(chunks)} chunks", file=sys.stderr)
            doc_context = rag.format_context(chunks)
            print(f"[API] Context length: {len(doc_context) if doc_context else 0}", file=sys.stderr)
        except Exception as exc:
            import traceback
            print(f"[API] RAG retrieval error: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    else:
        print(f"[API] RAG not enabled - use_rag={request.use_rag}, has_docs={bool(request.document_ids)}, has_conv={bool(request.conversation_id)}", file=sys.stderr)

    answer, trace = run_research(executor, request.message, messages, doc_context)

    conv_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
    now = datetime.now().isoformat()

    save_conversation(conv_id, request.title or "New chat", now, now)
    save_message(f"user-{datetime.now().timestamp()}", conv_id, "user", request.message, now)
    save_message(f"assistant-{datetime.now().timestamp()}", conv_id, "assistant", answer, now)

    trace_payload = _format_trace(trace) if request.debug else None
    return ChatResponse(answer=answer, trace=trace_payload)


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    import sys
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = _build_executor(request.temperature, request.max_results, request.tool_names)

    # Retrieve documents if RAG is enabled
    doc_context = None
    print(f"[API] Chat stream request: use_rag={request.use_rag}, doc_ids={request.document_ids}, conv_id={request.conversation_id}", file=sys.stderr)

    if request.use_rag and request.document_ids and request.conversation_id:
        try:
            print(f"[API] RAG enabled, retrieving documents...", file=sys.stderr)
            rag = get_rag_retrieval()
            # Don't add "conv-" prefix if it already exists
            collection_name = request.conversation_id if request.conversation_id.startswith("conv-") else f"conv-{request.conversation_id}"
            print(f"[API] Collection: {collection_name}, Doc IDs: {request.document_ids}", file=sys.stderr)
            chunks = rag.retrieve(
                request.message,
                collection_name,
                request.document_ids,
            )
            print(f"[API] Retrieved {len(chunks)} chunks", file=sys.stderr)
            doc_context = rag.format_context(chunks)
            print(f"[API] Context length: {len(doc_context) if doc_context else 0}", file=sys.stderr)
        except Exception as exc:
            import traceback
            print(f"[API] RAG retrieval error: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    else:
        print(f"[API] RAG not enabled - use_rag={request.use_rag}, has_docs={bool(request.document_ids)}, has_conv={bool(request.conversation_id)}", file=sys.stderr)

    conv_id = request.conversation_id or f"conv-{datetime.now().timestamp()}"
    now = datetime.now().isoformat()
    save_conversation(conv_id, request.title or "New chat", now, now)
    save_message(f"user-{datetime.now().timestamp()}", conv_id, "user", request.message, now)

    async def event_stream():
        yield _sse("status", {"state": "thinking"})
        answer, trace = run_research(executor, request.message, messages, doc_context)

        for step in _format_trace(trace):
            yield _sse("tool", step)

        for chunk in _chunk_text(answer):
            yield _sse("chunk", {"text": chunk})
            await asyncio.sleep(0)

        save_message(f"assistant-{datetime.now().timestamp()}", conv_id, "assistant", answer, now)
        yield _sse("done", {"answer": answer})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
