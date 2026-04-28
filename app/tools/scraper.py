from __future__ import annotations

import requests
from langchain_core.tools import tool


@tool("fetch_url")
def fetch_url(url: str) -> str:
    """Fetch the raw text content of a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text[:8000]
    except requests.RequestException as exc:
        return f"Request failed: {exc}"
