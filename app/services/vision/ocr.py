"""Image analysis service using Groq vision model."""

from __future__ import annotations

import base64
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def _detect_mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    elif image_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/png"


def _is_animated_gif(image_bytes: bytes) -> bool:
    """Check if GIF is animated."""
    if image_bytes[:6] not in (b"GIF87a", b"GIF89a"):
        return False
    gce_count = image_bytes.count(b"\x21\xf9")
    return gce_count > 1


def _is_supported_format(image_bytes: bytes) -> tuple[bool, str | None]:
    """Check if format is supported by Groq."""
    mime = _detect_mime(image_bytes)
    
    if mime == "image/gif":
        if _is_animated_gif(image_bytes):
            return False, "Animated GIFs not supported. Use JPEG, PNG, or WebP"
        return False, "GIF format not supported. Use JPEG, PNG, or WebP"
    
    supported = {"image/jpeg", "image/png", "image/webp"}
    if mime in supported:
        return True, None
    
    return False, f"Unsupported: {mime}"


def extract_text_from_bytes(image_bytes: bytes) -> str:
    """Extract text from image bytes using Groq vision model."""
    try:
        from groq import Groq

        from app.core.config import load_settings

        settings = load_settings()
        api_key = settings.groq_api_key
        if not api_key:
            return "Error: Groq API key not configured."

        # Check format support BEFORE sending to API
        is_supported, error_msg = _is_supported_format(image_bytes)
        if not is_supported:
            print(f"[OCR] Format not supported: {error_msg}")
            return f"Cannot extract text: {error_msg}"

        b64 = base64.b64encode(image_bytes).decode()
        mime = _detect_mime(image_bytes)
        data_url = f"data:{mime};base64,{b64}"

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract ALL text from this image. If there is no text, describe the image contents."},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        result = response.choices[0].message.content
        print(f"[OCR] Extracted {len(result)} chars from image")
        return result
    except Exception as exc:
        print(f"[OCR] Error: {exc}")
        return f"Error: {exc}"