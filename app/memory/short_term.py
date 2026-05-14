from __future__ import annotations


def format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No previous conversation."

    recent_messages = messages[-6:]
    lines: list[str] = []
    for message in recent_messages:
        role = message["role"]
        label = "User" if role == "user" else "Assistant"
        content = message["content"]
        if len(content) > 1000:
            content = content[:1000] + "\n... (truncated)"
        lines.append(f"{label}: {content}")
    return "\n".join(lines)
