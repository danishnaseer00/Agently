from __future__ import annotations

from collections.abc import Sequence

from langchain_groq import ChatGroq

from app.core.config import Settings


def build_llm(settings: Settings, temperature: float, tools: Sequence | None = None, model_name: str | None = None):
    if not settings.groq_api_key:
        raise RuntimeError(
            "Groq API key is missing. Set GROQ_API_KEY or Groq_API_KEY in the environment."
        )

    actual_model = model_name or settings.model_name

    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=actual_model,
        temperature=temperature,
        max_retries=2,
    )

    if tools:
        tools_list = list(tools)
        print(f"[LLM] Binding {len(tools_list)} tools: {[t.name for t in tools_list]}")
        llm = llm.bind_tools(tools_list, tool_choice="auto")

    return llm
