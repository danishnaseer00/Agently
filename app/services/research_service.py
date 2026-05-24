from __future__ import annotations

from langchain.agents import AgentExecutor

from app.agent.executor import run_agent
from app.memory.short_term import format_history

# Maximum chars for RAG context (top chunks only, saves tokens)
_MAX_RAG_CHARS = 3000


def run_research(
    executor: AgentExecutor | dict,
    prompt: str,
    messages: list[dict[str, str]],
    document_context: str | None = None,
) -> tuple[str, list[object]]:
    chat_history = format_history(messages)

    # Prepend document context if provided (compressed)
    if document_context:
        if len(document_context) > _MAX_RAG_CHARS:
            document_context = document_context[:_MAX_RAG_CHARS] + "\n... (additional context truncated)"
        chat_history = f"Reference Documents:\n{document_context}\n\n{chat_history}"

    # Support both compressed executor (dict with run_fn) and legacy AgentExecutor
    if isinstance(executor, dict) and "run_fn" in executor:
        return executor["run_fn"](prompt, chat_history)

    return run_agent(executor, prompt, chat_history)
