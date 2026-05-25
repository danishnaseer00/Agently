from __future__ import annotations
import json
import sys
import time
from collections.abc import Sequence
from datetime import datetime
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
    force_tools: bool = False,
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
                ("\n\nResearch this question using the available tools. Start by searching the web."
                 if force_tools else
                 "\n\nIf this question needs fresh or external data, use the tools to research it."
                 " Otherwise answer directly from what you know.")
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
    force_tools: bool = False,
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
                "5. Format cleanly: use **bold** for key terms, bullet points for lists, and paragraphs for explanations. Keep it readable.\n"
            )
            context_tag = "Image analysis"
        else:
            system_msg = (
                "You are a helpful assistant answering questions using the provided reference documents.\n"
                "\n"
                "Rules:\n"
                "1. Answer the user's question based on the provided documents.\n"
                "2. If the question is simple (e.g. 'what is this about'), give to the point answer in 3-4 lines.\n"
                "3. Do NOT add analysis, summaries, or extra details unless asked.\n"
                "4. Format cleanly: use **bold** for key terms, bullet points for lists, and paragraphs for explanations. Keep it readable.\n"
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
    _today = datetime.now().strftime("%B %d, %Y")
    system_msg = (
        f"You are a research assistant with access to these tools:\n"
        f"{tool_descs}\n\n"
        f"Available tools: {tool_names}\n\n"
        f"CURRENT DATE: {_today}.\n"
        "Search for the MOST RECENT information — try 2026 first, then 2025.\n"
        "Include the year in your search queries (e.g. \"2026 computer vision\") to get fresh results.\n"
        + ("You MUST search before answering — do NOT write an answer without first calling at least one tool.\n\n"
           if force_tools else
           "Only use tools when you need fresh/external data — for simple conversation answer directly.\n\n")
        + "### Rules\n"
        "1. Use tools to research the user's question. Be strategic — you have limited steps.\n"
        "2. After each tool call you will receive a **compressed summary** of the result.\n"
        "3. Decide: call another tool to gather more, OR provide your final answer.\n"
        "4. When you have enough information, answer the user directly.\n"
        "5. Do NOT ask the user for permission — just proceed.\n"
        "6. When using tools: present specific items (titles, names, data, dates).\n"
        "7. When answering without tools: be concise and direct — give the answer briefly unless asked for detail.\n"
        "8. Your answer MUST be grounded in what the tools returned.\n"
    )

    user_block = prompt
    if chat_history:
        user_block = f"{chat_history}\n\nUser question: {prompt}"

    for iteration in range(max_iterations):
        context_str = _build_context_block(system_msg, user_block, compressed_history, force_tools=force_tools)
        messages = [HumanMessage(content=context_str)]

        total_chars = len(context_str)
        print(
            f"[OptAgent] Round {iteration + 1}/{max_iterations}"
            f" | ctx_chars={total_chars}"
            f" | steps_in_ctx={len(compressed_history)}",
            file=sys.stderr,
        )

        try:
            # First attempt WITHOUT bind_tools — the model will output text-based
            # tool calls which Groq rejects, triggering _is_tool_error → retry with
            # bind_tools. This forces the model to actually call tools vs. skipping.
            tool_list = list(tool_map.values())
            response = llm.invoke(messages)
        except Exception as exc:
            if _is_token_limit_error(exc):
                print(f"[OptAgent] Token-limit error (413/TPM), reducing context…",
                      file=sys.stderr)

                # Retry 1: keep last 2 compressed steps only
                if len(compressed_history) > 2:
                    compressed_history[:] = compressed_history[-2:]
                    context_str = _build_context_block(
                        system_msg, user_block, compressed_history, force_tools=force_tools,
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
                        system_msg, user_block, compressed_history, force_tools=force_tools,
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
                # Retry same round with bind_tools (transient Groq issue with text-based tool calls)
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
                    if not response.tool_calls:
                        final = response.content if hasattr(response, "content") else str(response)
                        return _clean_response(final), raw_steps
                    # Has tool_calls — fall through to processing below
                else:
                    # Both retries failed — synthesize from existing research if any
                    if compressed_history:
                        return _synthesize_final(
                            prompt, compressed_history, llm, tools=list(tool_map.values())
                        ), raw_steps
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
            # On first round with no research yet and force_tools is set
            # (deepThink), the model may not call tools without bind_tools.
            # Retry with tool_choice="any" to force a tool call.
            if force_tools and iteration == 0 and not compressed_history:
                print(
                    f"[OptAgent] Round 1: no tool calls, retrying with bind_tools…",
                    file=sys.stderr,
                )
                tool_list = list(tool_map.values())
                try:
                    round_llm = llm.bind_tools(tool_list, tool_choice="any")
                    response = round_llm.invoke(messages)
                    if response.tool_calls:
                        # bind_tools produced tool calls — fall through to processing
                        pass
                    else:
                        final = response.content if hasattr(response, "content") else str(response)
                        cleaned = _clean_response(final)
                        print(
                            "[OptAgent] Still no tool calls after bind_tools, accepting as final",
                            file=sys.stderr,
                        )
                        return cleaned, raw_steps
                except Exception as bind_err:
                    print(
                        f"[OptAgent] bind_tools retry failed: {bind_err}",
                        file=sys.stderr,
                    )
                    return (
                        "I'm having trouble researching this topic right now. "
                        "Please try again."
                    ), raw_steps
            else:
                final = response.content if hasattr(response, "content") else str(response)
                cleaned = _clean_response(final)

                # Detect model hallucinating tool calls in text instead of real content
                if compressed_history and (
                    not cleaned.strip()
                    or cleaned.strip().startswith('{"query"')
                    or "<websearch" in final.lower()
                ):
                    print(
                        f"[OptAgent] Round {iteration + 1}: model output contained "
                        "hallucinated tool calls instead of real content — synthesizing from research",
                        file=sys.stderr,
                    )
                    return _synthesize_final(
                        prompt, compressed_history, llm, tools=list(tool_map.values())
                    ), raw_steps

                print(
                    f"[OptAgent] Final answer received at round {iteration + 1}",
                    file=sys.stderr,
                )
                return cleaned, raw_steps

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
    """Strip LLM hallucinated tool call tags and citation markers from the answer."""
    import re
    text = re.sub(r"</?(?:websearch|function|tool|search|invoke)[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<function=[^>]*>", "", text)
    text = re.sub(r"【[^】]*】", "", text)
    text = re.sub(r" {2,}", " ", text)       # collapse multiple spaces only
    text = re.sub(r"\n{3,}", "\n\n", text)   # cap consecutive newlines at 2
    return text.strip()


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
        "### Research summaries\n"
        + "\n".join(f"- {s}" for s in compressed_history)
        + "\n\n### Instructions\n"
        "Write a well-structured answer that directly addresses the user's question. "
        "Present specific findings (titles, data, facts) from the research. "
        "Do NOT write generic background from your training memory."
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
