from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool


def _resolve_safe_path(path: str) -> Path | None:
    root = Path.cwd().resolve()
    target = (root / path).resolve()
    if root == target or root in target.parents:
        return target
    return None


@tool("read_file")
def read_file(path: str) -> str:
    """Read a local file (relative to project root)."""
    target = _resolve_safe_path(path)
    if not target:
        return "Access denied."
    if not target.exists():
        return "File not found."
    if target.is_dir():
        return "Path is a directory."
    return target.read_text(encoding="utf-8", errors="ignore")[:8000]
