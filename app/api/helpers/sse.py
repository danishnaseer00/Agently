from __future__ import annotations

import json
from typing import Iterable

def chunk_text(text: str, size: int = 80) -> Iterable[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]


def sse(event: str, data: dict[str, object]) -> str:
    payload = json.dumps(data, ensure_ascii=True)
    return f"event: {event}\ndata: {payload}\n\n"
