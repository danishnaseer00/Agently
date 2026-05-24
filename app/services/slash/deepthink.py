"""Deep research on a topic using the optimized agent with search tools."""

from __future__ import annotations

import sys
from typing import Any

from app.core.config import get_settings
from app.memory.db import get_conversation_messages
from app.memory.short_term import format_history
from app.services.chat_executor import build_optimized_executor


def run_deep_think(
    conversation_id: str,
    user_id: str,
    topic: str | None = None,
    messages: list[dict[str, Any]] | None = None,
) -> tuple[str, list[object]]:
    """Run deep research on a topic using the agent with search tools."""
    settings = get_settings()

    # If no explicit topic, derive it from conversation history
    if not topic and not messages:
        if conversation_id:
            messages = get_conversation_messages(conversation_id, user_id)

    depth_prompt = _build_deep_prompt(topic, messages)

    print(f"[Slash] deepThink starting{' with topic: ' + topic if topic else ' from conversation'}",
          file=sys.stderr)

    # Use optimized executor: compresses tool results, retries 413 errors
    executor = build_optimized_executor(
        temperature=0.3,
        max_results=8,
        tool_names=["web_search", "fetch_url"],
        model_name=settings.deep_think_model,
        max_iterations=8,
        compress_chars=1200,
        tool_output_limit=1500,
    )

    chat_history = ""
    if messages:
        chat_history = format_history(
            [{"role": m["role"], "content": m["content"]} for m in messages[-3:]]
        )

    answer, steps = executor["run_fn"](depth_prompt, chat_history)
    return answer, steps


def _build_deep_prompt(topic: str | None, messages: list | None) -> str:
    context = ""

    if topic:
        context = f"Topic: {topic}"
    elif messages and len(messages) > 1:
        last_user_msgs = [
            m["content"] for m in messages if m.get("role") == "user"
        ][-3:]
        context = "Based on the conversation so far, the user wants deep research on:\n" + "\n".join(
            f"- {msg}" for msg in last_user_msgs
        )
    else:
        context = "The user requested deep research but didn't specify a topic."

    return (
        "You are a deep research agent. Your task is to conduct thorough research on the following topic.\n\n"
        f"{context}\n\n"
        "CRITICAL RULE — DO NOT IGNORE:\n"
        "Your answer MUST be based on what you find via the search tools.\n"
        "Do NOT write a generic overview from your training memory.\n"
        "The user wants SPECIFIC, CONCRETE findings — not general background.\n\n"
        "Instructions:\n"
        "1. Search the web for the topic using the web_search tool — search for at least 3 different queries\n"
        "2. Fetch and read the most promising sources using fetch_url to get full details\n"
        "3. Cross-reference information from multiple sources\n"
        "4. If sources disagree, note the different viewpoints\n\n"
        "### RESPONSE FORMAT\n"
        "Structure your answer EXACTLY like this template:\n"
        "\n"
        "**Topic Name**\n"
        "Short paragraph explaining this topic (2-3 sentences max).\n"
        "- Key finding with specific detail\n"
        "- Another key finding with data or names\n"
        "\n"
        "**Next Topic Name**\n"
        "Short paragraph explaining this topic.\n"
        "- Key finding with specific detail\n"
        "- Another key finding\n"
        "\n"
        "---\n"
        "### Sources\n"
        "- Source Name — description or title\n"
        "- Source Name — description or title\n"
        "- Source Name — description or title\n"
        "\n"
        "RULES:\n"
        "1. Start each topic with **bold name** then a **short paragraph** (2-3 sentences), then \"bullet points\" for specific findings.\n"
        "2. Use bullet points for listing findings, data points, and key facts.\n"
        "3. Keep paragraphs SHORT — no more than 3 sentences each.\n"
        "4. End with a \"### Sources\" section listing each source on its own line.\n"
        "5. Focus on concrete findings (names, data, facts) — no generic overview from memory.\n"
        "6. Do NOT write everything in one long paragraph. Break it into sections.\n"
    )
