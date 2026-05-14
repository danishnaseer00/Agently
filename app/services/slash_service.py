from __future__ import annotations

import sys
from typing import Any

from app.core.config import get_settings
from app.core.llm import build_llm
from app.memory.db import get_conversation_messages
from app.memory.short_term import format_history
from app.services.chat_executor import build_optimized_executor


# ─── /summarize ────────────────────────────────────────────────────────

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
        "Start with 'Here is the summary:' then list the key points as bullet points.And Highlight the main words.\n\n"
        "Rules:\n"
        "- Focus ONLY on the content and information that was discussed — NOT on who said what\n"
        "- Do NOT write things like 'The user asked...' or 'The assistant replied...'\n"
        "- Just capture the facts, topics, questions, and conclusions directly\n"
        "- Each bullet should be one complete point highlighting a key topic or theme from the conversation\n"
        "- Keep it concise — 3 to 6 bullet points max\n"
        "- Bold or emphasize the main topics so they stand out (e.g. **Topic Name**: explanation)\n\n"
        "Conversation:\n"
        "---\n"
        f"{transcript}\n"
        "---"
    )

    response = llm.invoke(summary_prompt)
    return response.content


# ─── /deepThink ─────────────────────────────────────────────────────────

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
        max_iterations=4,      # Max 4 tool call rounds
        compress_chars=1200,   # Compress each tool result to ~300 tokens
        tool_output_limit=1500,# Limit raw output logged
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
        "3. Present the SPECIFIC items you found (paper titles, findings, data, names, dates — whatever is relevant)\n"
        "4. Cross-reference information from multiple sources\n"
        "5. If the user asks for a list, give them the actual list — not an essay about the topic\n\n"
        "Guidelines:\n"
        "- Search for at least 3 different queries to get diverse perspectives\n"
        "- Prioritize recent and authoritative sources\n"
        "- If sources disagree, note the different viewpoints\n"
        "- Be thorough but stay within the token limit\n\n"
        "Research and provide your answer."
    )
