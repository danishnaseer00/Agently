from __future__ import annotations
from typing import Any
from langchain.agents import AgentExecutor
import sys


def run_agent(
    agent_executor: AgentExecutor,
    prompt: str,
    chat_history: str,
) -> tuple[str, list[Any]]:
    print(f"\n[DEBUG] Running agent with prompt: {prompt[:100]}...", file=sys.stderr)
    print(f"[DEBUG] Available tools: {[tool.name for tool in agent_executor.tools]}", file=sys.stderr)

    result = agent_executor.invoke(
        {
            "input": prompt,
            "chat_history": chat_history,
        }
    )

    output = str(result.get("output", "")).strip()
    intermediate_steps = result.get("intermediate_steps", [])

    print(f"[DEBUG] Agent steps taken: {len(intermediate_steps)}", file=sys.stderr)
    for i, (action, observation) in enumerate(intermediate_steps):
        print(f"[DEBUG] Step {i+1}: Tool={getattr(action, 'tool', 'unknown')}, Input={getattr(action, 'tool_input', '')}", file=sys.stderr)

    return output, intermediate_steps
