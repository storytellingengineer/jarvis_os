"""Local personal knowledge store backed by SQLite FTS5."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class KnowledgeStore:
    """Store and retrieve local text documents without an external vector DB."""

    def __init__(self, path: str | Path = "data/knowledge.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, source TEXT NOT NULL UNIQUE, content TEXT NOT NULL)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS document_search USING fts5(source, content)")

    def add_document(self, source: str, content: str) -> None:
        """Insert or replace a local knowledge document."""
        text = content.strip()
        if not text:
            raise ValueError("Knowledge content cannot be empty.")
        with self._connect() as db:
            db.execute("DELETE FROM documents WHERE source = ?", (source,))
            db.execute("DELETE FROM document_search WHERE source = ?", (source,))
            cursor = db.execute("INSERT INTO documents(source, content) VALUES (?, ?)", (source, text))
            db.execute("INSERT INTO document_search(rowid, source, content) VALUES (?, ?, ?)", (cursor.lastrowid, source, text))

    def search(self, query: str, limit: int = 5) -> str:
        """Return the most relevant local documents for a query."""
        terms = " ".join(part for part in query.replace('"', ' ').split() if part)
        if not terms:
            return "No knowledge query provided."
        limit = max(1, min(limit, 10))
        with self._connect() as db:
            rows = db.execute(
                "SELECT source, snippet(document_search, 1, '[', ']', ' … ', 32) AS snippet "
                "FROM document_search WHERE document_search MATCH ? ORDER BY rank LIMIT ?",
                (terms, limit),
            ).fetchall()
        if not rows:
            return "No matching local knowledge was found."
        return "\n\n".join(f"[{row['source']}]\n{row['snippet']}" for row in rows)
