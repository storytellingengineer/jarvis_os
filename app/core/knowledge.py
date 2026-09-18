from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    source: str
    file_type: str
    size_bytes: int
    ingested_at: str


class KnowledgeStore:
    def __init__(self, db_path: str | Path = "jarvis_knowledge.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    source TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    document_id TEXT,
                    file_type TEXT,
                    size_bytes INTEGER,
                    ingested_at TEXT
                )
                """
            )

            # Migrate databases created before metadata support was introduced.
            existing_columns = {
                row[1] for row in db.execute("PRAGMA table_info(documents)").fetchall()
            }
            metadata_columns = {
                "document_id": "TEXT",
                "file_type": "TEXT",
                "size_bytes": "INTEGER",
                "ingested_at": "TEXT",
            }
            for column_name, column_type in metadata_columns.items():
                if column_name not in existing_columns:
                    db.execute(
                        f"ALTER TABLE documents ADD COLUMN {column_name} {column_type}"
                    )

            db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS document_search
                USING fts5(source, content)
                """
            )

    @staticmethod
    def stable_document_id(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def add_document(
        self,
        source: str,
        content: str,
        *,
        file_type: str = "text",
        size_bytes: int | None = None,
        ingested_at: str | None = None,
    ) -> DocumentMetadata:
        source = source.strip()
        if not source:
            raise ValueError("source must not be empty")
        if not content.strip():
            raise ValueError("content must not be empty")

        document_id = self.stable_document_id(content)
        timestamp = ingested_at or datetime.now(timezone.utc).isoformat()
        byte_size = size_bytes if size_bytes is not None else len(content.encode("utf-8"))

        with self._connect() as db:
            db.execute("DELETE FROM document_search WHERE source = ?", (source,))
            db.execute("DELETE FROM documents WHERE source = ?", (source,))
            db.execute(
                """
                INSERT INTO documents
                    (source, content, document_id, file_type, size_bytes, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, content, document_id, file_type, byte_size, timestamp),
            )
            db.execute(
                "INSERT INTO document_search(source, content) VALUES (?, ?)",
                (source, content),
            )

        return DocumentMetadata(document_id, source, file_type, byte_size, timestamp)

    def ingest_file(self, path: str | Path) -> DocumentMetadata:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md"}:
            content = file_path.read_text(encoding="utf-8")
        elif suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError("PDF ingestion requires pypdf") from exc
            reader = PdfReader(str(file_path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == ".docx":
            try:
                from docx import Document
            except ImportError as exc:
                raise RuntimeError("DOCX ingestion requires python-docx") from exc
            document = Document(str(file_path))
            content = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            raise ValueError(f"Unsupported file type: {suffix or '<none>'}")

        return self.add_document(
            str(file_path),
            content,
            file_type=suffix,
            size_bytes=file_path.stat().st_size,
        )

    def get_metadata(self, source: str) -> DocumentMetadata | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT document_id, source, file_type, size_bytes, ingested_at
                FROM documents WHERE source = ?
                """,
                (source,),
            ).fetchone()
        if row is None:
            return None
        return DocumentMetadata(
            document_id=row["document_id"],
            source=row["source"],
            file_type=row["file_type"],
            size_bytes=row["size_bytes"],
            ingested_at=row["ingested_at"],
        )

    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT source, content
                FROM document_search
                WHERE document_search MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [dict(row) for row in rows]
