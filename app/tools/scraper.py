from __future__ import annotations

import requests
from langchain_core.tools import tool


@tool("fetch_url")
def fetch_url(url: str) -> str:
    """Fetch the raw text content of a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        text = response.text[:8000]
        if not text.strip():
            return "Page loaded but contains no readable text content."
        return text
    except requests.Timeout:
        return "Timeout: The request took too long to complete. Please try again or use a shorter URL."
    except requests.ConnectionError:
        return "Connection Error: Unable to reach the URL. Please check if the URL is correct and the website is accessible."
    except requests.HTTPError as exc:
        return f"HTTP Error {exc.response.status_code}: {exc.response.reason}"
    except requests.RequestException as exc:
        return f"Request failed: {exc}"
