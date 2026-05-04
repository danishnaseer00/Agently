from __future__ import annotations

import asyncio
import json
from functools import lru_cache
from typing import Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse
from app.agent.agent import build_agent
from app.core.config import load_settings
from app.core.llm import build_llm
from app.services.research_service import run_research
from app.tools.search import build_web_search_tool

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


def _build_executor(temperature: float, max_results: int):
    settings = get_settings()
    tools = [build_web_search_tool(settings, max_results)]
    llm = build_llm(settings, temperature, tools)
    return build_agent(llm, tools)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = _build_executor(request.temperature, request.max_results)
    answer, trace = run_research(executor, request.message, messages)
    trace_payload = _format_trace(trace) if request.debug else None
    return ChatResponse(answer=answer, trace=trace_payload)


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    messages = [item.model_dump() for item in request.history]
    messages.append({"role": "user", "content": request.message})

    executor = _build_executor(request.temperature, request.max_results)

    async def event_stream():
        yield _sse("status", {"state": "thinking"})
        answer, trace = run_research(executor, request.message, messages)

        for step in _format_trace(trace):
            yield _sse("tool", step)

        for chunk in _chunk_text(answer):
            yield _sse("chunk", {"text": chunk})
            await asyncio.sleep(0)

        yield _sse("done", {"answer": answer})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
