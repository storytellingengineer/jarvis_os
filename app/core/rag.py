"""Local RAG pipeline: chunking, embeddings, hybrid retrieval, and citations."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from openai import OpenAI


@dataclass(frozen=True)
class Chunk:
    source: str
    chunk_index: int
    content: str


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75) -> list[str]:
    """Split text into deterministic word-based chunks with overlap."""
    words = text.split()
    if not words:
        return []
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

    step = chunk_size - overlap
    return [" ".join(words[start : start + chunk_size]) for start in range(0, len(words), step)]


class EmbeddingProvider:
    """Generate embeddings through the OpenAI embeddings endpoint."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("LLM_API_KEY is not configured. Add it to your .env file.")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=list(texts))
        return [item.embedding for item in response.data]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


class RAGStore:
    """SQLite-backed chunk store with FTS5 + vector hybrid retrieval."""

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
                "CREATE TABLE IF NOT EXISTS rag_documents ("
                "id INTEGER PRIMARY KEY, source TEXT NOT NULL UNIQUE"
                ")"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS rag_chunks ("
                "id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, "
                "chunk_index INTEGER NOT NULL, content TEXT NOT NULL, embedding TEXT NOT NULL, "
                "UNIQUE(document_id, chunk_index), FOREIGN KEY(document_id) REFERENCES rag_documents(id)"
                ")"
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_rag_chunks_document ON rag_chunks(document_id)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS rag_search USING fts5(source, content)")

    def replace_document(self, source: str, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]) -> None:
        if not chunks or len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must be non-empty and have equal lengths")
        with self._connect() as db:
            old = db.execute("SELECT id FROM rag_documents WHERE source = ?", (source,)).fetchone()
            if old:
                db.execute("DELETE FROM rag_chunks WHERE document_id = ?", (old["id"],))
                db.execute("DELETE FROM rag_documents WHERE id = ?", (old["id"],))
            db.execute("DELETE FROM rag_search WHERE source = ?", (source,))
            document_id = db.execute(
                "INSERT INTO rag_documents(source) VALUES (?)", (source,)
            ).lastrowid
            for chunk, embedding in zip(chunks, embeddings):
                db.execute(
                    "INSERT INTO rag_chunks(document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                    (document_id, chunk.chunk_index, chunk.content, json.dumps(list(embedding))),
                )
                db.execute(
                    "INSERT INTO rag_search(rowid, source, content) VALUES (?, ?, ?)",
                    (db.execute("SELECT last_insert_rowid()").fetchone()[0], source, chunk.content),
                )

    def _keyword_ranks(self, query: str) -> dict[int, int]:
        terms = " ".join(part for part in query.replace('"', ' ').split() if part)
        if not terms:
            return {}
        with self._connect() as db:
            rows = db.execute(
                "SELECT rowid FROM rag_search WHERE rag_search MATCH ? ORDER BY rank LIMIT 50",
                (terms,),
            ).fetchall()
        return {int(row["rowid"]): rank for rank, row in enumerate(rows, start=1)}

    def search(self, query: str, query_embedding: Sequence[float], limit: int = 5) -> str:
        """Return hybrid-ranked chunks with source and chunk citations."""
        limit = max(1, min(limit, 10))
        keyword_ranks = self._keyword_ranks(query)
        with self._connect() as db:
            rows = db.execute(
                "SELECT c.id, d.source, c.chunk_index, c.content, c.embedding "
                "FROM rag_chunks c JOIN rag_documents d ON d.id = c.document_id"
            ).fetchall()

        scored: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            vector = json.loads(row["embedding"])
            semantic = cosine_similarity(query_embedding, vector)
            keyword_rank = keyword_ranks.get(int(row["id"]))
            # Reciprocal rank fusion keeps keyword and semantic retrieval on comparable scales.
            score = 0.65 * semantic + (0.35 / (60 + keyword_rank) if keyword_rank else 0.0)
            scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored or scored[0][0] <= 0:
            return "No matching local knowledge was found."

        return "\n\n".join(
            f"[{row['source']}#chunk-{row['chunk_index']}]\n{row['content']}"
            for _, row in scored[:limit]
        )
