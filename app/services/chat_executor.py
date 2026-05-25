from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.llm import build_llm
from app.agent.agent import build_agent
from app.agent.agent import run_optimized_agent
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
            force_tools=True,
        )

    return {
        "tools": tools,
        "llm": llm,
        "run_fn": run_fn,
        "max_iterations": max_iterations,
        "compress_chars": compress_chars,
        "tool_output_limit": tool_output_limit,
    }


def build_compressed_chat_executor(
    temperature: float,
    max_results: int,
    tool_names: list[str] | None = None,
    model_name: str | None = None,
    max_iterations: int = 5,
    compress_chars: int = 1200,
    tool_output_limit: int = 1500,
) -> dict:
    """Build a chat executor with context compression.

    Replaces LangChain's AgentExecutor with the same optimized loop
    used by /deepthink.
      - Tool outputs are compressed before storing in context
      - Old entries are dropped on token-limit errors
      - Context never grows unboundedly

    Returns a dict with keys:
      - "tools", "llm", "run_fn", "max_iterations"
      - run_fn(prompt, chat_history) -> (answer, steps)
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
    print(f"[CompressedChat] Tools: {tool_names_list}", file=sys.stderr)

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


def build_optimized_executor(
    temperature: float,
    max_results: int,
    tool_names: list[str] | None = None,
    model_name: str | None = None,
    max_iterations: int = 8,
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
