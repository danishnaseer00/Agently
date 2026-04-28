from __future__ import annotations


def trace_to_text(intermediate_steps: list[object]) -> str:
    if not intermediate_steps:
        return "No tool calls were needed."

    lines: list[str] = []
    for index, (action, observation) in enumerate(intermediate_steps, start=1):
        tool_name = getattr(action, "tool", "unknown tool")
        tool_input = getattr(action, "tool_input", "")
        lines.append(f"Step {index}: {tool_name}")
        lines.append(f"Input: {tool_input}")
        lines.append(f"Observation: {observation}")
        lines.append("")
    return "\n".join(lines).rstrip()
