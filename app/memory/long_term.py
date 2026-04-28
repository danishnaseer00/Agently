from __future__ import annotations


class LongTermMemory:
    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, text: str) -> None:
        self._items.append(text)

    def search(self, query: str, limit: int = 5) -> list[str]:
        return self._items[:limit]
