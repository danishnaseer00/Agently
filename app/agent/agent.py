from __future__ import annotations

from collections.abc import Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent

from app.agent.parser import build_prompt


def build_agent(llm, tools: Sequence, max_iterations: int = 15) -> AgentExecutor:
    tools_desc = "\n".join(
        f"{tool_obj.name}: {tool_obj.description}" for tool_obj in tools
    )
    tool_names = ", ".join(tool_obj.name for tool_obj in tools)
    prompt = build_prompt().partial(tools=tools_desc, tool_names=tool_names)
    agent = create_tool_calling_agent(llm=llm, tools=list(tools), prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=list(tools),
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        verbose=False,
        max_iterations=max_iterations,
    )
