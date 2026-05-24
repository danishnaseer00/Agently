"""Summarize the entire conversation using the LLM."""

from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.llm import build_llm
from app.memory.db import get_conversation_messages


def run_summarize(conversation_id: str, user_id: str) -> str:
    """Summarize the entire conversation using the LLM."""
    messages = get_conversation_messages(conversation_id, user_id)

    if not messages:
        return "No conversation to summarize. Start a conversation first."

    # Build a chat transcript from all messages
    transcript_lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        transcript_lines.append(f"[{role.upper()}]: {content}")

    transcript = "\n\n".join(transcript_lines)
    print(f"[Slash] Summarizing conversation with {len(messages)} messages", file=sys.stderr)

    settings = get_settings()

    # Use a simple LLM call for summarization (no tools needed)
    llm = build_llm(settings, temperature=0.3)

    summary_prompt = (
        "Summarize the conversation below.\n\n"
        "Format:\n"
        "Use **bold** for key topics or themes, bullet points for listing\n"
        "the main takeaways, and a short introductory sentence to set context.\n\n"
        "Rules:\n"
        "- Focus ONLY on the content and information that was discussed — NOT on who said what\n"
        "- Do NOT write things like 'The user asked...' or 'The assistant replied...'\n"
        "- Just capture the facts, topics, questions, and conclusions directly\n"
        "- Each bullet should be one complete point highlighting a key topic or theme from the conversation\n"
        "- Keep it concise — 3 to 6 bullet points max\n"
        "- Use **bold** for topic names so they stand out (e.g. **Topic Name**: explanation)\n\n"
        "Conversation:\n"
        "---\n"
        f"{transcript}\n"
        "---"
    )

    response = llm.invoke(summary_prompt)
    return response.content
