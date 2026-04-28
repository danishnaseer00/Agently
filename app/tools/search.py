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
            max_results=max_results,
            include_answer=True,
            search_depth="advanced",
        )

        sections: list[str] = []
        answer = response.get("answer")
        if answer:
            sections.append(f"Answer: {answer}")

        results = response.get("results", [])
        if not results:
            sections.append("No search results were returned.")
            return "\n\n".join(sections)

        for index, result in enumerate(results, start=1):
            title = result.get("title", "Untitled result")
            url = result.get("url", "")
            content = result.get("content", "")
            sections.append(f"{index}. {title}\nURL: {url}\nSnippet: {content}")

        return "\n\n".join(sections)

    return web_search
