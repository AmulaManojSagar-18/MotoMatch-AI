"""A tiny in-memory vector store (pure Python, no extra dependencies).

For 10 short bike documents this is more than enough. It exposes a minimal
interface (`add`, `search`) so it could be swapped for ChromaDB or another
local vector database later without touching the retriever's callers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class _Entry:
    key: int
    vector: list[float]
    payload: object


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._entries: list[_Entry] = []

    def add(self, key: int, vector: list[float], payload: object) -> None:
        self._entries.append(_Entry(key=key, vector=vector, payload=payload))

    def search(self, query_vector: list[float], k: int = 3) -> list[tuple[float, object]]:
        scored = [
            (cosine_similarity(query_vector, e.vector), e.payload)
            for e in self._entries
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        return len(self._entries)
