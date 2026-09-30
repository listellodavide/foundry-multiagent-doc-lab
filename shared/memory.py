"""Small, auditable memory stores used by the workshop.

The long-term store deliberately uses only the Python standard library. It stores
deterministic term-frequency vectors in SQLite so participants can inspect every
part of retrieval before replacing it with a managed embedding/vector service.
"""

import json
import math
import re
import sqlite3
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]{2,}")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){10,30}\b", re.I)
SECRET = re.compile(r"(?i)(bearer|api[_ -]?key|token)\s*[:= ]\s*[^\s,;]+")


def redact(text: str) -> str:
    """Remove common credentials and full IBANs before persistence."""
    return SECRET.sub(r"\1=[REDACTED]", IBAN.sub("[REDACTED_IBAN]", text))


def vectorize(text: str) -> dict[str, float]:
    counts = Counter(TOKEN.findall(text.lower()))
    length = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {term: value / length for term, value in counts.items()}


def similarity(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(value * right.get(term, 0.0) for term, value in left.items())


@dataclass(frozen=True)
class MemoryHit:
    text: str
    score: float
    metadata: dict[str, str]


class ConversationMemory:
    """A bounded, process-local window: short-term memory."""

    def __init__(self, limit: int = 6):
        if limit < 1:
            raise ValueError("limit must be positive")
        self._turns: deque[tuple[str, str]] = deque(maxlen=limit)

    def add(self, role: str, text: str) -> None:
        self._turns.append((role, text))

    def context(self) -> list[tuple[str, str]]:
        return list(self._turns)


class SQLiteVectorMemory:
    """Session-scoped persistent summaries: long-term memory."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY, tenant TEXT NOT NULL, session TEXT NOT NULL,
                text TEXT NOT NULL, vector TEXT NOT NULL, metadata TEXT NOT NULL)""")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def add(self, tenant: str, session: str, text: str,
            metadata: dict[str, str] | None = None) -> int:
        safe = redact(text)
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO memories(tenant, session, text, vector, metadata) VALUES (?, ?, ?, ?, ?)",
                (tenant, session, safe, json.dumps(vectorize(safe)), json.dumps(metadata or {})),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a memory id")
            return cursor.lastrowid

    def search(self, tenant: str, session: str, query: str, limit: int = 5) -> list[MemoryHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        query_vector = vectorize(query)
        with self._connect() as db:
            rows = db.execute(
                "SELECT text, vector, metadata FROM memories WHERE tenant = ? AND session = ?",
                (tenant, session),
            ).fetchall()
        hits = [MemoryHit(text, similarity(query_vector, json.loads(vector)), json.loads(metadata))
                for text, vector, metadata in rows]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]

    def clear(self, tenant: str, session: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM memories WHERE tenant = ? AND session = ?", (tenant, session))
