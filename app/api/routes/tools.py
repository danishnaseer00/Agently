from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["tools"])


@router.get("/api/tools")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": "web_search", "description": "Search the web for current information, news, facts"},
            {"name": "fetch_url", "description": "Fetch content from a URL"},
            {"name": "analyze_image", "description": "Extract text from an image via URL or base64"},
        ]
    }
