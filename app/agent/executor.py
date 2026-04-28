from __future__ import annotations

from typing import Any

from langchain.agents import AgentExecutor


def run_agent(
    agent_executor: AgentExecutor,
    prompt: str,
    chat_history: str,
) -> tuple[str, list[Any]]:
    result = agent_executor.invoke(
        {
            "input": prompt,
            "chat_history": chat_history,
        }
    )
    output = str(result.get("output", "")).strip()
    intermediate_steps = result.get("intermediate_steps", [])
    return output, intermediate_steps
