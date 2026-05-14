from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from tavily import TavilyClient

from app.core.config import Settings


def build_web_search_tool(settings: Settings, max_results: int = 5):
    @tool("web_search")
    def web_search(query: str) -> str:
        """Search the web for up-to-date information, news, facts, and verification."""
        api_key = settings.tavily_api_key
        if not api_key:
            return "Tavily API key is missing. Set TAVILY_API_KEY or Tavily_API_KEY in the environment."

        client = TavilyClient(api_key=api_key)
        response: dict[str, Any] = client.search(
            query=query,
            max_results=min(max_results, 5),  # hard cap at 5 to save tokens
            include_answer=True,
            search_depth="advanced",
        )

        sections: list[str] = []
        answer = response.get("answer")
        if answer:
            # Truncate answer to 500 chars
            answer = answer[:500] + "…" if len(answer) > 500 else answer
            sections.append(f"Answer: {answer}")

        results = response.get("results", [])
        if not results:
            sections.append("No search results were returned.")
            return "\n\n".join(sections)

        for index, result in enumerate(results[:5], start=1):  # max 5 results
            title = result.get("title", "Untitled result")
            url = result.get("url", "")
            content = result.get("content", "")
            # Truncate each snippet to 300 chars
            if len(content) > 300:
                content = content[:300] + "…"
            sections.append(f"{index}. {title}\nURL: {url}\nSnippet: {content}")

        return "\n\n".join(sections)

    return web_search
