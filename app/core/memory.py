"""SQLite-backed persistent conversation memory for JARVIS."""

import sqlite3
from pathlib import Path

from app.core.history import Message


class PersistentMemory:
    """Persist conversation messages locally using SQLite."""

    def __init__(self, path: str | Path = "data/jarvis.db") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save(self, message: Message) -> None:
        """Persist one conversation message."""
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (message.role, message.content),
            )

    def load_recent(self, limit: int = 20) -> list[Message]:
        """Load the most recent messages in conversation order."""
        if limit < 1:
            raise ValueError("limit must be at least 1")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Message(role=role, content=content) for role, content in reversed(rows)]

    def clear(self) -> None:
        """Delete all persisted conversation messages."""
        with self._connect() as connection:
            connection.execute("DELETE FROM messages")
