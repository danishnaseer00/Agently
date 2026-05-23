from __future__ import annotations

import sys

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "Agently API", "version": "0.1.0"}


@router.get("/api/health")
def health() -> dict[str, str]:
    print("[API] Health check received", file=sys.stderr)
    return {"status": "ok"}
