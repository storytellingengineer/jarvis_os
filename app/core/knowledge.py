"""Local personal knowledge store backed by SQLite FTS5.

The ingestion helpers intentionally keep file-format dependencies optional so
JARVIS remains usable as a lightweight local application.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    source: str
    file_type: str
    size_bytes: int
    ingested_at: str


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
            db.execute(
                "CREATE TABLE IF NOT EXISTS documents ("
                "id INTEGER PRIMARY KEY, source TEXT NOT NULL UNIQUE, "
                "content TEXT NOT NULL, document_id TEXT, file_type TEXT, "
                "size_bytes INTEGER, ingested_at TEXT"
                ")"
            )
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS document_search USING fts5(source, content)")

    @staticmethod
    def stable_document_id(content: str) -> str:
        """Return a deterministic content identifier suitable for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def add_document(self, source: str, content: str, metadata: DocumentMetadata | None = None) -> None:
        """Insert or replace a document atomically, including its search index."""
        text = content.strip()
        if not source.strip():
            raise ValueError("Knowledge source cannot be empty.")
        if not text:
            raise ValueError("Knowledge content cannot be empty.")
        document_id = metadata.document_id if metadata else self.stable_document_id(text)
        file_type = metadata.file_type if metadata else Path(source).suffix.lower() or ".txt"
        size_bytes = metadata.size_bytes if metadata else len(text.encode("utf-8"))
        ingested_at = metadata.ingested_at if metadata else datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("DELETE FROM document_search WHERE source = ?", (source,))
            db.execute("DELETE FROM documents WHERE source = ?", (source,))
            cursor = db.execute(
                "INSERT INTO documents(source, content, document_id, file_type, size_bytes, ingested_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (source, text, document_id, file_type, size_bytes, ingested_at),
            )
            db.execute(
                "INSERT INTO document_search(rowid, source, content) VALUES (?, ?, ?)",
                (cursor.lastrowid, source, text),
            )

    def ingest_file(self, path: str | Path, source: str | None = None) -> DocumentMetadata:
        """Extract and atomically ingest a TXT, PDF, or DOCX file."""
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Knowledge file not found: {file_path}")
        file_type = file_path.suffix.lower()
        extractors: dict[str, Callable[[Path], str]] = {
            ".txt": lambda p: p.read_text(encoding="utf-8"),
            ".md": lambda p: p.read_text(encoding="utf-8"),
            ".pdf": self._extract_pdf,
            ".docx": self._extract_docx,
        }
        extractor = extractors.get(file_type)
        if extractor is None:
            raise ValueError(f"Unsupported knowledge file type: {file_type or 'unknown'}")
        content = extractor(file_path)
        text = content.strip()
        if not text:
            raise ValueError(f"Knowledge file contains no extractable text: {file_path}")
        metadata = DocumentMetadata(
            document_id=self.stable_document_id(text),
            source=source or str(file_path),
            file_type=file_type,
            size_bytes=file_path.stat().st_size,
            ingested_at=datetime.now(timezone.utc).isoformat(),
        )
        self.add_document(metadata.source, text, metadata)
        return metadata

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF ingestion requires the optional 'pypdf' dependency.") from exc
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)

    @staticmethod
    def _extract_docx(path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX ingestion requires the optional 'python-docx' dependency.") from exc
        return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)

    def get_metadata(self, source: str) -> DocumentMetadata | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT document_id, source, file_type, size_bytes, ingested_at "
                "FROM documents WHERE source = ?", (source,)
            ).fetchone()
        if row is None:
            return None
        return DocumentMetadata(
            document_id=row["document_id"], source=row["source"], file_type=row["file_type"],
            size_bytes=row["size_bytes"], ingested_at=row["ingested_at"],
        )

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
