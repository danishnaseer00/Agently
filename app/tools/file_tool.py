from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

ALLOWED_ROOT = Path.home() / "Desktop" / "AI-workingdir"


def _resolve_safe_path(path: str) -> Path | None:
    try:
        ALLOWED_ROOT.mkdir(parents=True, exist_ok=True)
        target = (ALLOWED_ROOT / path).resolve()
        if ALLOWED_ROOT not in target.parents and ALLOWED_ROOT != target:
            return None
        return target
    except Exception:
        return None


@tool("read_file")
def read_file(path: str) -> str:
    """Read a file from the AI-workingdir folder."""
    target = _resolve_safe_path(path)
    if not target:
        return f"Access denied. Can only read from {ALLOWED_ROOT}"
    if not target.exists():
        return "File not found."
    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
        if len(content) > 15000:
            content = content[:15000] + "\n... (truncated)"
        return content
    except Exception as exc:
        return f"Read failed: {exc}"


@tool("list_files")
def list_files(path: str = ".") -> str:
    """List files and folders in the AI-workingdir."""
    target = _resolve_safe_path(path)
    if not target:
        return f"Access denied. Can only list {ALLOWED_ROOT}"
    if not target.exists():
        return "Path not found."
    if not target.is_dir():
        return "Path is not a directory."
    try:
        items = []
        for item in sorted(target.iterdir()):
            suffix = "/" if item.is_dir() else ""
            items.append(f"{item.name}{suffix}")
        if not items:
            return "(empty)"
        return "\n".join(items)
    except Exception as exc:
        return f"List failed: {exc}"