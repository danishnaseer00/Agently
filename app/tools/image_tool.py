"""Image analysis tool — hybrid OCR + vision model approach."""

from __future__ import annotations

import base64
import re

import requests
from langchain_core.tools import tool

from app.services.vision.pipeline import (
    process_image_hybrid,
    process_image_force_vision,
)


def _decode_base64(data_url: str) -> bytes:
    """Decode base64 image data URL."""
    match = re.match(r"data:image/[^;]+;base64,(.+)", data_url)
    if not match:
        raise ValueError("Invalid base64 image data URL")
    return base64.b64decode(match.group(1))


def _fetch_image(url: str) -> bytes:
    """Fetch image from URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, timeout=20, headers=headers)
    resp.raise_for_status()
    return resp.content


@tool("analyze_image")
def analyze_image(
    image_source: str,
    query: str = None,
    force_vision: str = "false",
) -> str:
    """
    Analyze an image using hybrid approach (OCR + conditional vision).
    
    Accepts either a URL (http:// or https://) or a base64 data URL
    (data:image/png;base64,...).
    
    Returns concise analysis suitable for agent processing.
    
    Args:
        image_source: Image URL or base64 data URL
        query: Optional custom query for vision analysis (complex images)
        force_vision: Set to "true" to always use vision model, even for simple text
    
    Returns:
        Formatted analysis result focused on content, not extraction steps
    """
    try:
        # Decode/fetch image
        if image_source.startswith("data:image"):
            image_bytes = _decode_base64(image_source)
            image_url = None
        elif image_source.startswith(("http://", "https://")):
            image_bytes = _fetch_image(image_source)
            image_url = image_source
        else:
            return "Error: image_source must be a valid URL or base64 data URL."

        # Choose processing mode
        force = force_vision.lower() == "true"
        
        if force:
            result = process_image_force_vision(
                image_bytes,
                image_url=image_url,
                custom_query=query,
            )
        else:
            result = process_image_hybrid(
                image_bytes,
                image_url=image_url,
                custom_query=query,
            )

        # Return simplified output for agent processing
        if result.complexity == "simple_text":
            # For simple text, just return the OCR text for agent processing
            return result.ocr_text if result.ocr_text else "No text found in image."
        else:
            # For complex images, return vision analysis + relevant OCR
            output_parts = []
            if result.vision_analysis and "failed" not in result.vision_analysis.lower():
                output_parts.append(result.vision_analysis)
            if result.ocr_text and "cannot" not in result.ocr_text.lower():
                output_parts.append(f"Text in image: {result.ocr_text}")
            return "\n\n".join(output_parts) if output_parts else "Unable to analyze image."

    except requests.RequestException as exc:
        return f"Failed to fetch image: {exc}"
    except Exception as exc:
        print(f"[Image Tool] Error: {exc}")
        return f"Image analysis failed: {exc}"
