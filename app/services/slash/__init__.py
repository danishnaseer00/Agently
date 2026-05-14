"""Slash command handlers — /summarize and /deepThink."""

from app.services.slash.summarize import run_summarize
from app.services.slash.deepthink import run_deep_think

__all__ = ["run_summarize", "run_deep_think"]
