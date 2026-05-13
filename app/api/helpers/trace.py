from __future__ import annotations


def format_trace(steps: list[object]) -> list[dict[str, str]]:
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
