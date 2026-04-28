from __future__ import annotations

from langchain.agents import AgentExecutor

from app.agent.executor import run_agent
from app.memory.short_term import format_history


def run_research(
    agent_executor: AgentExecutor,
    prompt: str,
    messages: list[dict[str, str]],
) -> tuple[str, list[object]]:
    chat_history = format_history(messages)
    return run_agent(agent_executor, prompt, chat_history)
