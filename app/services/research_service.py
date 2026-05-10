from __future__ import annotations

from langchain.agents import AgentExecutor

from app.agent.executor import run_agent
from app.memory.short_term import format_history


def run_research(
    agent_executor: AgentExecutor,
    prompt: str,
    messages: list[dict[str, str]],
    document_context: str | None = None,
) -> tuple[str, list[object]]:
    chat_history = format_history(messages)

    # Prepend document context if provided
    if document_context:
        chat_history = f"Reference Documents:\n{document_context}\n\n{chat_history}"

    return run_agent(agent_executor, prompt, chat_history)
