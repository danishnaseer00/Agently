from __future__ import annotations

import requests
from langchain_core.tools import tool


@tool("fetch_url")
def fetch_url(url: str) -> str:
    """Fetch the main text content of a URL, stripped of HTML tags.
    Returns up to 1500 characters of readable text.
    """
    import re

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        # Remove HTML tags
        text = response.text
        text = re.sub(r"<script[^>]*?>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Decode common entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&nbsp;", " ").replace("&quot;", "\"")

        if not text.strip():
            return "Page loaded but contains no readable text content."

        # Limit to 1500 chars for token efficiency
        if len(text) > 1500:
            text = text[:1400] + "\n\n[…content truncated…]"

        return text

    except requests.Timeout:
        return "Timeout: The request took too long to complete."
    except requests.ConnectionError:
        return "Connection Error: Unable to reach the URL."
    except requests.HTTPError as exc:
        return f"HTTP Error {exc.response.status_code}: {exc.response.reason}"
    except requests.RequestException as exc:
        return f"Request failed: {exc}"
