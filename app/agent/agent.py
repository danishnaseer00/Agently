from __future__ import annotations
import json
import sys
import time
from collections.abc import Sequence
from typing import Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage
from app.agent.parser import build_prompt


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

# For optimized agent
def _is_token_limit_error(exc: Exception) -> bool:
    err = str(exc).lower()
    return any(kw in err for kw in (
        "413", "request too large",
        "ratelimit", "rate limit",
        "429", "too many requests",
        "tokens per minute", "token limit",
    ))


def _is_tool_error(exc: Exception) -> bool:
    """Check if the error is a Groq tool-call failure (400 / tool_use_failed)."""
    err = str(exc).lower()
    return any(kw in err for kw in (
        "tool_use_failed",
        "failed to call a function",
        "badrequest",
        "400",
    ))


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
        if "Reference Documents:" in user_block:
            parts.append(
                "\n\nAnswer the user's question using the reference documents above."
                " Be concise — give a direct answer. Use tools only if the"
                " documents don't contain the answer."
            )
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
    max_iterations: int = 8,
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

    has_rag_context = "Reference Documents:" in chat_history
    has_image_context = "[System Note:" in prompt

    # ── Direct answer mode: no tools, no loop, just answer from context ──
    if has_rag_context or has_image_context:
        if has_image_context:
            system_msg = (
                "You are a helpful assistant. A vision model has already analyzed the user's attached image.\n"
                "\n"
                "Rules:\n"
                "1. Answer directly from the image analysis provided below. Do NOT use any tools.\n"
                "2. If the question is simple (e.g. 'what is this'), give a concise 1-2 sentence answer.\n"
                "3. Do NOT add extra analysis, summaries, or details unless asked.\n"
                "4. Do NOT mention that you cannot see the image — the analysis is already done for you.\n"
                "5. Format cleanly: use **bold** for key terms or subheadings, bullet points for lists or key takeaways, and paragraphs for explanations. Keep it readable — not excessively formatted.\n"
            )
            context_tag = "Image analysis"
        else:
            system_msg = (
                "You are a helpful assistant answering questions using the provided reference documents.\n"
                "\n"
                "Rules:\n"
                "1. Answer the user's question directly and concisely using the documents.\n"
                "2. If the question is simple (e.g. 'what is this about'), give a one-sentence answer.\n"
                "3. Do NOT add analysis, summaries, or extra details unless asked.\n"
                "4. Format cleanly: use **bold** for key terms or subheadings, bullet points for lists or key takeaways, and paragraphs for explanations. Keep it readable — not excessively formatted.\n"
            )
            context_tag = "Reference documents"
        user_block = prompt
        if chat_history:
            user_block = f"{chat_history}\n\nUser question: {prompt}"
        context_str = system_msg + f"\n\n{context_tag}\n{user_block}"
        messages = [HumanMessage(content=context_str)]
        print(
            f"[OptAgent] Direct mode ({context_tag}) — single LLM call, no tools",
            file=sys.stderr,
        )
        try:
            response = llm.invoke(messages)
            final = response.content if hasattr(response, "content") else str(response)
            return _clean_response(final), []
        except Exception as exc:
            return f"Sorry, I couldn't answer: {exc}", []

    # ── Non-RAG mode: tool-calling agent loop ──────────────────────
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
        "6. Present specific items you found (titles, names, data, dates).\n"
        "7. Do NOT write generic overviews from your training memory.\n"
        "8. Your answer MUST be grounded in what the tools returned.\n"
        "9. Structure your answer like this:\n"
        "   **Topic** — Short paragraph (2-3 sentences).\n"
        "   - Key finding with detail\n"
        "   - Another key finding\n"
        "10. Use **bold** for topic names and key terms. Use bullet points (-) for findings and data. Keep paragraphs short — max 3 sentences. Never write one giant wall of text.\n"
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
            # Re-bind tools each round to ensure they're always in the API request
            # Prevents Groq's 'tool was not in request.tools' rejection
            tool_list = list(tool_map.values())
            round_llm = llm.bind_tools(tool_list, tool_choice="auto")
            response = round_llm.invoke(messages)
        except Exception as exc:
            if _is_token_limit_error(exc):
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
                        round_llm = llm.bind_tools(tool_list, tool_choice="auto")
                        response = round_llm.invoke(messages)
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
                        round_llm = llm.bind_tools(tool_list, tool_choice="auto")
                        response = round_llm.invoke(messages)
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

            elif _is_tool_error(exc):
                print(f"[OptAgent] Tool-call error, retrying with tools…",
                      file=sys.stderr)
                raw_steps.append({
                    "iteration": iteration + 1,
                    "tool": "_tool_error",
                    "error": str(exc),
                })
                if compressed_history:
                    return _synthesize_final(
                        prompt, compressed_history, llm, tools=list(tool_map.values())
                    ), raw_steps
                # No research yet — retry same round with tools (transient Groq issue)
                retried = False
                for retry in range(2):
                    time.sleep(1 + retry)
                    print(f"[OptAgent] Retry {retry + 1}/2 with tools…", file=sys.stderr)
                    try:
                        round_llm = llm.bind_tools(tool_list, tool_choice="auto")
                        response = round_llm.invoke(messages)
                        retried = True
                        break
                    except Exception:
                        continue
                if retried:
                    # If retry returned a final answer, return it. Otherwise process tool calls normally.
                    if not response.tool_calls:
                        final = response.content if hasattr(response, "content") else str(response)
                        return _clean_response(final), raw_steps
                else:
                    return (
                        "We're having trouble processing your request right now. "
                        "Please try again in a moment."
                    ), raw_steps

            else:
                print(f"[OptAgent] Unexpected error, synthesizing from gathered research…",
                      file=sys.stderr)
                raw_steps.append({
                    "iteration": iteration + 1,
                    "tool": "_error",
                    "error": str(exc),
                })
                if compressed_history:
                    return _synthesize_final(
                        prompt, compressed_history, llm, tools=list(tool_map.values())
                    ), raw_steps
                return (
                    "We're having trouble processing your request right now. "
                    "Please try again in a moment."
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
    return _synthesize_final(prompt, compressed_history, llm, tools=list(tool_map.values())), raw_steps


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
    tools: Sequence | None = None,
) -> str:
    if not compressed_history:
        return (
            "I was unable to research this topic. "
            "Please rephrase your question or try a narrower topic."
        )

    synthesis_prompt = (
        "Synthesize a final answer based on the research summaries below.\n\n"
        "Research summaries:\n"
        + "\n".join(f"- {s}" for s in compressed_history)
        + "\n\nInstructions:\n"
        "Write a clean, direct answer that addresses the user's question.\n"
        "Present specific findings (titles, data, facts) from the research.\n"
        "Do NOT write generic background from your training memory.\n"
        "Structure your answer like this:\n"
        "\n"
        "**Topic Name**\n"
        "Short paragraph (2-3 sentences).\n"
        "- Key finding\n"
        "- Key finding\n"
        "\n"
        "**Next Topic**\n"
        "Short paragraph.\n"
        "- Key finding\n"
        "\n"
        "### Sources\n"
        "- Source — description\n"
        "- Source — description\n"
        "\n"
        "Keep paragraphs short (max 3 sentences). Use bullet points for findings.\n"
        "End with a Sources section listing each source on its own line.\n"
    )

    try:
        # Re-bind tools for synthesis call too (no tool calls expected, but defensive)
        if tools:
            synthesis_llm = llm.bind_tools(list(tools), tool_choice="none")
        else:
            synthesis_llm = llm
        resp = synthesis_llm.invoke([HumanMessage(content=synthesis_prompt)])
        text = resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
        return _clean_response(text)
    except Exception:
        lines = "\n".join(f"- {s}" for s in compressed_history)
        return (
            "Based on my research, here are the findings:\n\n"
            f"{lines}\n\n"
            "These were gathered from web searches and source documents."
        )
