from __future__ import annotations

import sys
import traceback

from fastapi import APIRouter, UploadFile

from app.services.vision.ocr import extract_text_from_bytes

router = APIRouter(tags=["images"])


@router.post("/api/images/upload")
async def upload_image(file: UploadFile) -> dict:
    """Upload an image, run OCR, and return extracted text."""
    try:
        print(f"[API] Image upload: {file.filename}", file=sys.stderr)
        content = await file.read()
        print(f"[API] Image size: {len(content)} bytes", file=sys.stderr)

        # Validate image type
        allowed = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
        content_type = file.content_type or ""
        if content_type not in allowed:
            return {"error": f"Unsupported image type: {content_type}. Use PNG, JPG, WEBP, or GIF."}

        # Run OCR
        text = extract_text_from_bytes(content)
        print(f"[API] OCR extracted {len(text)} chars", file=sys.stderr)

        return {
            "filename": file.filename,
            "content_type": content_type,
            "extracted_text": text,
            "char_count": len(text),
            "status": "success",
        }
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return {"error": str(exc), "status": "failed"}
