from __future__ import annotations


def format_trace(steps: list[object]) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for step in steps:
        if isinstance(step, dict):
            # Compressed executor format (list of dicts from run_optimized_agent)
            formatted.append(
                {
                    "tool": step.get("tool", "unknown"),
                    "tool_input": str(step.get("args", {})),
                    "observation": step.get("summary", "")
                    or step.get("result", "")[:500]
                    or step.get("error", ""),
                }
            )
        else:
            # LangChain AgentExecutor format (tuple of action, observation)
            action, observation = step
            formatted.append(
                {
                    "tool": str(getattr(action, "tool", "unknown")),
                    "tool_input": str(getattr(action, "tool_input", "")),
                    "observation": str(observation),
                }
            )
    return formatted
