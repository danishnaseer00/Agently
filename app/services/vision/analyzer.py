
from __future__ import annotations
import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def _detect_mime(image_bytes: bytes) -> str:
    """Detect MIME type from image bytes."""
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
    """Check if GIF is animated by looking for multiple image blocks."""
    if image_bytes[:6] not in (b"GIF87a", b"GIF89a"):
        return False
    
    # Look for Graphics Control Extension (0x21F9) which indicates animation
    gce_count = image_bytes.count(b"\x21\xf9")
    return gce_count > 1


def _is_supported_format(image_bytes: bytes) -> tuple[bool, str | None]:
    """Check if image format is supported by Groq vision model.
    
    Returns:
        (is_supported, error_message)
    """
    mime = _detect_mime(image_bytes)
    
    # GIFs are problematic - check if animated
    if mime == "image/gif":
        if _is_animated_gif(image_bytes):
            return False, "Animated GIFs not supported. Use static formats: JPEG, PNG, WebP"
        return False, "GIF format not supported. Please use JPEG, PNG, or WebP"
    
    # Supported formats
    supported = {"image/jpeg", "image/png", "image/webp"}
    if mime in supported:
        return True, None
    
    return False, f"Unsupported format: {mime}"


def analyze_with_vision(image_bytes: bytes, query: str = None) -> str:
    """
    Analyze image using Groq vision model for complex reasoning tasks.
    
    Use when:
    - Identifying objects/scenes
    - Understanding relationships in image
    - Complex visual reasoning
    - Analyzing charts/diagrams
    """
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
            print(f"[Analyzer] Format not supported: {error_msg}")
            return f"Cannot analyze: {error_msg}"

        b64 = base64.b64encode(image_bytes).decode()
        mime = _detect_mime(image_bytes)
        data_url = f"data:{mime};base64,{b64}"

        client = Groq(api_key=api_key)
        
        # Default query for complex reasoning
        if query is None:
            query = """Analyze this image thoroughly:
1. Identify main objects, subjects, or scene
2. Describe spatial relationships and layout
3. Note any text visible (already extracted separately)
4. Identify colors, lighting, and mood
5. Describe any actions or processes occurring
6. Provide context or purpose of the image"""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=2048,
            temperature=0.5,
        )
        result = response.choices[0].message.content
        print(f"[Analyzer] Vision analysis: {len(result)} chars")
        return result
    except Exception as exc:
        print(f"[Analyzer] Error: {exc}")
        return f"Analysis failed: {str(exc)}"


def classify_image_complexity(ocr_text: str, image_size_kb: float) -> str:
    """
    Classify whether image is simple text or complex reasoning task.
    
    Returns: "simple_text" or "complex_reasoning"
    """
    # Simple heuristics:
    # - If mostly text with few words per line → simple text
    # - If large image or complex layout → complex reasoning
    # - If short OCR output → likely simple text
    
    text_length = len(ocr_text.strip())
    
    # If almost no text, it's likely a complex image (no documents)
    if text_length < 20:
        print("[Classifier] Detected as: COMPLEX REASONING (no significant text)")
        return "complex_reasoning"
    
    # If moderate text and reasonable image size, likely simple document
    text_lines = ocr_text.strip().split('\n')
    avg_line_length = sum(len(line) for line in text_lines) / max(len(text_lines), 1)
    
    # Simple text indicators:
    # - Text length: 20-1500 chars (typical document range)
    # - Avg line length < 100 (normal formatted lines)
    # - Image not large (reasonable document size)
    is_simple = (
        text_length >= 20 and
        text_length <= 1500 and
        avg_line_length < 100 and
        image_size_kb < 500
    )
    
    if is_simple:
        print("[Classifier] Detected as: SIMPLE TEXT")
        return "simple_text"
    else:
        print("[Classifier] Detected as: COMPLEX REASONING")
        return "complex_reasoning"
