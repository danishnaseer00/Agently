from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentTraceStep:
    tool: str
    tool_input: str
    observation: Any


@dataclass
class AgentResponse:
    answer: str
    steps: list[AgentTraceStep]
