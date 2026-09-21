from pathlib import Path
import sqlite3

import pytest

from app.core.knowledge import KnowledgeStore


def test_knowledge_store_add_and_search(tmp_path: Path) -> None:
    store = KnowledgeStore(tmp_path / "knowledge.db")
    store.add_document("notes.md", "JARVIS should prioritize evaluation and observability.")
    result = store.search("evaluation observability")
    assert any(row["source"] == "notes.md" for row in result)
    assert any("observability" in row["content"] for row in result)


def test_ingest_text_file_persists_stable_metadata(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("Evaluation must be deterministic.", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "knowledge.db")

    metadata = store.ingest_file(source, source="notes.txt")
    persisted = store.get_metadata("notes.txt")

    assert metadata.document_id == store.stable_document_id("Evaluation must be deterministic.")
    assert persisted == metadata
    assert persisted.file_type == ".txt"


def test_ingest_rejects_unsupported_files(tmp_path: Path) -> None:
    source = tmp_path / "notes.csv"
    source.write_text("a,b", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "knowledge.db")

    with pytest.raises(ValueError, match="Unsupported knowledge file type"):
        store.ingest_file(source)


def test_existing_database_is_migrated(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as db:
        db.execute(
            "CREATE TABLE documents ("
            "id INTEGER PRIMARY KEY, "
            "source TEXT NOT NULL UNIQUE, "
            "content TEXT NOT NULL"
            ")"
        )
        db.execute(
            "CREATE VIRTUAL TABLE document_search USING fts5(source, content)"
        )

    store = KnowledgeStore(db_path)
    metadata = store.add_document("legacy.txt", "Legacy knowledge remains available.")
    persisted = store.get_metadata("legacy.txt")

    assert persisted == metadata
    assert persisted.file_type == "text"
