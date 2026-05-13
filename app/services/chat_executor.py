from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.llm import build_llm
from app.agent.agent import build_agent
from app.tools.search import build_web_search_tool
from app.tools.scraper import fetch_url
from app.tools.image_tool import analyze_image


def build_executor(temperature: float, max_results: int, tool_names: list[str] | None = None):
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

    llm = build_llm(settings, temperature, tools)
    executor = build_agent(llm, tools)

    print(f"[DEBUG] Agent tools: {[t.name for t in executor.tools]}", file=sys.stderr)
    return executor
