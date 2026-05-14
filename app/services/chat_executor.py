from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.llm import build_llm
from app.agent.agent import build_agent
from app.agent.optimized_agent import run_optimized_agent
from app.tools.search import build_web_search_tool
from app.tools.scraper import fetch_url
from app.tools.image_tool import analyze_image


def build_executor(temperature: float, max_results: int, tool_names: list[str] | None = None, model_name: str | None = None, max_iterations: int = 15):
    settings = get_settings()

    available = {
        "web_search": build_web_search_tool(settings, max_results),
        "fetch_url": fetch_url,
        "analyze_image": analyze_image,
    }

    if tool_names:
        tools = [available[name] for name in tool_names if name in available]
    else:
        tools = [available["web_search"], available["fetch_url"], available["analyze_image"]]

    tool_names_list = [t.name for t in tools]
    print(f"\n[DEBUG] Building executor with tools: {tool_names_list}", file=sys.stderr)

    llm = build_llm(settings, temperature, tools, model_name=model_name)
    executor = build_agent(llm, tools, max_iterations=max_iterations)

    print(f"[DEBUG] Agent tools: {[t.name for t in executor.tools]}", file=sys.stderr)
    return executor


def build_optimized_executor(
    temperature: float,
    max_results: int,
    tool_names: list[str] | None = None,
    model_name: str | None = None,
    max_iterations: int = 4,
    compress_chars: int = 1200,
    tool_output_limit: int = 1500,
) -> dict:
    """Build an optimized executor that compresses tool results to stay under token limits.

    Returns a dict with keys:
      - "tools": list of tools
      - "llm": the compiled LLM (with bound tools)
      - "run_fn": callable(prompt, chat_history) -> (answer, steps)
      - "compress_chars", "tool_output_limit", "max_iterations": configuration
    """
    settings = get_settings()

    available = {
        "web_search": build_web_search_tool(settings, max_results),
        "fetch_url": fetch_url,
        "analyze_image": analyze_image,
    }

    if tool_names:
        tools = [available[name] for name in tool_names if name in available]
    else:
        tools = [available["web_search"], available["fetch_url"], available["analyze_image"]]

    tool_names_list = [t.name for t in tools]
    print(f"[OptimizedExecutor] Tools: {tool_names_list}", file=sys.stderr)

    # Bind tools to LLM for function calling
    llm = build_llm(settings, temperature, tools, model_name=model_name)

    def run_fn(prompt: str, chat_history: str = "") -> tuple[str, list]:
        return run_optimized_agent(
            tools=tools,
            llm=llm,
            prompt=prompt,
            chat_history=chat_history,
            max_iterations=max_iterations,
            compress_chars=compress_chars,
            tool_output_limit=tool_output_limit,
        )

    return {
        "tools": tools,
        "llm": llm,
        "run_fn": run_fn,
        "max_iterations": max_iterations,
        "compress_chars": compress_chars,
        "tool_output_limit": tool_output_limit,
    }
