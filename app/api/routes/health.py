from __future__ import annotations

import sys

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict[str, str]:
    print("[API] Health check received", file=sys.stderr)
    return {"status": "ok"}
