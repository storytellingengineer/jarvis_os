from pathlib import Path

from app.core.knowledge import KnowledgeStore


def test_knowledge_store_add_and_search(tmp_path: Path) -> None:
    store = KnowledgeStore(tmp_path / "knowledge.db")
    store.add_document("notes.md", "JARVIS should prioritize evaluation and observability.")
    result = store.search("evaluation observability")
    assert "notes.md" in result
    assert "observability" in result
