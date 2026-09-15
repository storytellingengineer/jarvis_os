from pathlib import Path

from app.core.rag import Chunk, RAGStore, chunk_text, cosine_similarity


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("one two three four five six", chunk_size=4, overlap=1)
    assert chunks == ["one two three four", "four five six"]


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_rag_store_returns_cited_chunks(tmp_path: Path) -> None:
    store = RAGStore(tmp_path / "knowledge.db")
    chunks = [
        Chunk("project.md", 0, "JARVIS evaluation uses retrieval groundedness metrics."),
        Chunk("project.md", 1, "Agent workflows will add planner and verifier stages."),
    ]
    store.replace_document("project.md", chunks, [[1.0, 0.0], [0.0, 1.0]])

    result = store.search("retrieval evaluation", [1.0, 0.0], limit=1)
    assert "[project.md#chunk-0]" in result
    assert "retrieval groundedness" in result
