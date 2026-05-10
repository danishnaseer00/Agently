from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

ALLOWED_ROOT = Path.home() / "AI-workingdir"


def _resolve_safe_write_path(path: str) -> Path | None:
    try:
        ALLOWED_ROOT.mkdir(parents=True, exist_ok=True)
        target = (ALLOWED_ROOT / path).resolve()
        if ALLOWED_ROOT not in target.parents and ALLOWED_ROOT != target:
            return None
        return target
    except Exception:
        return None


@tool("write_file")
def write_file(filename: str, content: str) -> str:
    """Write content to a file in the AI-workingdir folder."""
    target = _resolve_safe_write_path(filename)
    if not target:
        return f"Access denied. Can only write to {ALLOWED_ROOT}"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {target}"
    except Exception as exc:
        return f"Write failed: {exc}"