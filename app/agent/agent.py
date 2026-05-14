"""Agent building and execution.

Contains:
  - build_agent()         — standard LangChain AgentExecutor builder
  - run_optimized_agent() — custom loop with context compression & 413 retry
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Sequence
from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage

from app.agent.parser import build_prompt


# ═══════════════════════════════════════════════════════════════════════
#  Standard AgentExecutor builder
# ═══════════════════════════════════════════════════════════════════════

def build_agent(llm, tools: Sequence, max_iterations: int = 8) -> AgentExecutor:
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


# ═══════════════════════════════════════════════════════════════════════
#  Optimized context-compressing loop (for deepThink / token-sensitive use)
# ═══════════════════════════════════════════════════════════════════════

def _is_token_limit_error(exc: Exception) -> bool:
    err = str(exc).lower()
    return any(kw in err for kw in ("413", "request too large", "ratelimit",
                                    "tokens per minute", "token limit"))


def _build_context_block(
    system_msg: str,
    user_block: str,
    compressed_history: list[str],
) -> str:
    parts = [system_msg, f"\n\n## User question\n{user_block}"]
    if compressed_history:
        parts.append("\n\n## Research so far (compressed)")
        for i, step in enumerate(compressed_history, 1):
            parts.append(f"  {i}. {step}")
        parts.append("\n\nContinue researching or provide your final answer.")
    else:
        parts.append(
            "\n\nResearch this question using the available tools."
            " Start by searching the web."
        )
    return "".join(parts)


def run_optimized_agent(
    tools: Sequence,
    llm: Any,
    prompt: str,
    chat_history: str = "",
    max_iterations: int = 4,
    compress_chars: int = 1200,
    tool_output_limit: int = 1500,
) -> tuple[str, list[dict[str, Any]]]:
    """Run an agent loop that compresses tool outputs instead of appending them.

    Key differences from LangChain's AgentExecutor:
      - Each tool result is compressed to ~*compress_chars* chars before storage
      - Old compressed entries are dropped on 413 errors (context shrinks, never grows unbounded)
      - Full raw output is logged but only the summary enters the LLM context
      - The LLM decides when it has enough and returns a final answer
    """
    tool_map = {t.name: t for t in tools}
    tool_descs = "\n".join(f"  {t.name}: {t.description}" for t in tools)
    tool_names = ", ".join(t.name for t in tools)

    compressed_history: list[str] = []
    raw_steps: list[dict[str, Any]] = []

    system_msg = (
        f"You are a research assistant with access to these tools:\n"
        f"{tool_descs}\n\n"
        f"Available tools: {tool_names}\n\n"
        "### Rules\n"
        "1. Use tools to research the user's question. Be strategic — you have limited steps.\n"
        "2. After each tool call you will receive a **compressed summary** of the result.\n"
        "3. Decide: call another tool to gather more, OR provide your final answer.\n"
        "4. When you have enough information, answer the user directly.\n"
        "5. Do NOT ask the user for permission — just proceed.\n"
        "6. Present **specific items** you found (titles, names, data, dates).\n"
        "7. Do NOT write generic overviews from your training memory.\n"
        "8. Your answer MUST be grounded in what the tools returned.\n"
    )

    user_block = prompt
    if chat_history:
        user_block = f"{chat_history}\n\nUser question: {prompt}"

    for iteration in range(max_iterations):
        context_str = _build_context_block(system_msg, user_block, compressed_history)
        messages = [HumanMessage(content=context_str)]

        total_chars = len(context_str)
        print(
            f"[OptAgent] Round {iteration + 1}/{max_iterations}"
            f" | ctx_chars={total_chars}"
            f" | steps_in_ctx={len(compressed_history)}",
            file=sys.stderr,
        )

        try:
            response = llm.invoke(messages)
        except Exception as exc:
            if not _is_token_limit_error(exc):
                raise

            print(f"[OptAgent] Token-limit error (413/TPM), reducing context…",
                  file=sys.stderr)

            # Retry 1: keep last 2 compressed steps only
            if len(compressed_history) > 2:
                compressed_history[:] = compressed_history[-2:]
                context_str = _build_context_block(
                    system_msg, user_block, compressed_history,
                )
                messages = [HumanMessage(content=context_str)]
                print(f"[OptAgent] Retry with last 2 steps only", file=sys.stderr)
                time.sleep(1)
                try:
                    response = llm.invoke(messages)
                except Exception:
                    response = None

            # Retry 2: clear all history
            if response is None:
                compressed_history.clear()
                context_str = _build_context_block(
                    system_msg, user_block, compressed_history,
                )
                messages = [HumanMessage(content=context_str)]
                print(f"[OptAgent] Retry with zero history", file=sys.stderr)
                time.sleep(2)
                try:
                    response = llm.invoke(messages)
                except Exception:
                    response = None

            # Retry 3: graceful fallback
            if response is None:
                lines = "\n".join(
                    f"- {s}" for s in compressed_history[-3:] if compressed_history
                ) or "No results were obtained before the limit was reached."
                raw_steps.append({
                    "iteration": iteration + 1,
                    "tool": "_fallback",
                    "error": str(exc),
                })
                return (
                    "I hit a token limit while researching your question. "
                    "Here is what I gathered so far. "
                    "Try a shorter or more specific query:\n\n"
                    + lines
                ), raw_steps

        # ── no tool call → final answer ───────────────────────────────
        if not response.tool_calls:
            final = response.content if hasattr(response, "content") else str(response)
            print(
                f"[OptAgent] Final answer received at round {iteration + 1}",
                file=sys.stderr,
            )
            return _clean_response(final), raw_steps

        # ── process each tool call ────────────────────────────────────
        for tc in response.tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})

            if tool_name not in tool_map:
                compressed_history.append(
                    f"Tried unknown tool '{tool_name}' – skipped"
                )
                continue

            print(
                f"[OptAgent] Step {iteration + 1}: {tool_name}"
                f"({_safe_args(tool_args)})",
                file=sys.stderr,
            )

            try:
                raw_result = tool_map[tool_name].invoke(tool_args)
            except Exception as tool_err:
                raw_result = f"[Tool error] {tool_err}"

            raw_str = str(raw_result)
            summary = _compress(raw_str, max_chars=compress_chars)
            compressed_history.append(
                f"{tool_name}({_safe_args(tool_args)}) → {summary}"
            )
            raw_steps.append({
                "iteration": iteration + 1,
                "tool": tool_name,
                "args": tool_args,
                "result": raw_str[:tool_output_limit],
                "summary": summary,
            })

    # ── max iterations reached without final answer ───────────────────
    print(
        f"[OptAgent] Max iterations ({max_iterations}) reached."
        " Asking LLM to synthesize final answer.",
        file=sys.stderr,
    )
    return _synthesize_final(prompt, compressed_history, llm), raw_steps


# ═══════════════════════════════════════════════════════════════════════
#  Optimized agent helpers
# ═══════════════════════════════════════════════════════════════════════

def _compress(text: str, max_chars: int = 1200) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n…[truncated]…\n" + text[-half:]


def _safe_args(args: dict, limit: int = 80) -> str:
    s = json.dumps(args)
    return s[:limit] + "…" if len(s) > limit else s


def _clean_response(text: str) -> str:
    """Strip LLM citation markers like 【web_search†L5-L6】 from the answer."""
    import re
    text = re.sub(r"【[^】]*】", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _synthesize_final(
    prompt: str,
    compressed_history: list[str],
    llm: Any,
) -> str:
    if not compressed_history:
        return (
            "I was unable to research this topic. "
            "Please rephrase your question or try a narrower topic."
        )

    synthesis_prompt = (
        "Synthesize a final answer based on the research summaries below.\n\n"
        "### Research summaries\n"
        + "\n".join(f"- {s}" for s in compressed_history)
        + "\n\n### Instructions\n"
        "Write a well-structured answer that directly addresses the user's question. "
        "Present specific findings (titles, data, facts) from the research. "
        "Do NOT write generic background from your training memory."
    )

    try:
        resp = llm.invoke([HumanMessage(content=synthesis_prompt)])
        text = resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
        return _clean_response(text)
    except Exception:
        lines = "\n".join(f"- {s}" for s in compressed_history)
        return (
            "Based on my research, here are the findings:\n\n"
            f"{lines}\n\n"
            "These were gathered from web searches and source documents."
        )
