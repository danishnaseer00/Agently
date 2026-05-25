"""Deep research on a topic using the optimized agent with search tools."""

from __future__ import annotations

import sys
from datetime import datetime
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

    _today = datetime.now().strftime("%B %d, %Y")
    return f"""You are an advanced deep research agent.

Your job is to find, verify, and synthesize up-to-date, factual information using web search tools.

You must behave like a professional research analyst — not a general AI assistant.

{context}

Current date: {_today}

────────────────────────
CORE RULES (MANDATORY)
────────────────────────

1. NO GENERIC ANSWERS
- Do NOT rely on prior knowledge or training data alone.
- Every important claim MUST come from web search results.

2. MULTI-STEP RESEARCH REQUIRED
- You MUST perform at least 3 different search queries before answering.
- Each query must explore a different angle of the topic.
  (e.g., latest developments, real-world use, limitations, comparisons)

3. RECENCY PRIORITY
- Prioritize results from 2026.
- If limited, include 2025.
- Always include dates in findings.

4. DEPTH OVER BREADTH
- Extract specific details: names, numbers, benchmarks, companies, papers, dates.
- Avoid definitions, explanations, or filler.

5. SOURCE VALIDATION
- Cross-check multiple sources.
- If sources disagree, explicitly mention the disagreement.

6. NO EARLY ANSWERING
- Do NOT produce the final answer after a single search.
- Only answer after completing multiple searches and reviewing sources.

7. PROFESSIONAL TONE
- Write like a research analyst or consultant.
- Clear, precise, and structured — not conversational or vague.

────────────────────────
SEARCH STRATEGY
────────────────────────

For every task:

Step 1: Run multiple queries (>=3), such as:
- "[topic] 2026 latest developments"
- "[topic] real world applications 2026"
- "[topic] benchmark results or comparison 2025 2026"

Step 2: Identify high-quality sources:
- Research papers
- Official company announcements
- Trusted publications

Step 3: Extract concrete findings:
- Metrics (%, accuracy, speed, cost)
- Names (models, companies, researchers)
- Dates (month/year when possible)

Step 4: Cross-reference findings before writing.

────────────────────────
OUTPUT FORMAT (MANDATORY)
────────────────────────

Your final answer MUST follow this exact structure:

### 1. Executive Summary
- 4-6 bullet points
- Directly answer the question
- Include specific facts (numbers, names, dates)

---

### 2. Key Findings

Organize into sections based on themes.

Each point MUST include:
- What was found
- Who/where it came from
- When (date)
- Any measurable result

Example format:
- [Finding]
  Source: [Name / Organization]
  Date: [Year or Month-Year]
  Data: [Specific metric or result]

---

### 3. Cross-Source Comparison

- Highlight agreements or contradictions
- Explain possible reasons (dataset, scale, methodology)

---

### 4. Real-World Examples

- Companies, products, or deployments
- Include measurable outcomes if available

---

### 5. Limitations / Gaps

- What is unclear, missing, or overstated
- Any technical or practical constraints

---

### 6. Final Takeaways

- 3-5 concise, opinionated insights
- Focus on what actually matters going forward

────────────────────────
STRICT PROHIBITIONS
────────────────────────

- No generic introductions
- No textbook explanations
- No filler sentences
- No answering without multiple searches
- No claims without specific details

If sufficient recent data is NOT found:
Explicitly say: "Limited recent data available (2026), using best available sources from 2025." Then proceed with the best available."""
