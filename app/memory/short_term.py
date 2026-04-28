from __future__ import annotations


def format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "No previous conversation."

    recent_messages = messages[-12:]
    lines: list[str] = []
    for message in recent_messages:
        role = message["role"]
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {message['content']}")
    return "\n".join(lines)
