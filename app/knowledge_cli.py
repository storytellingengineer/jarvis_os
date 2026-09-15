"""Import text or Markdown files into JARVIS's local RAG index."""

import argparse
from pathlib import Path

from app.config import settings
from app.core.rag import Chunk, EmbeddingProvider, RAGStore, chunk_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a document into JARVIS local RAG.")
    parser.add_argument("path", help="Path to a UTF-8 text or Markdown file")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_file():
        parser.error(f"File not found: {path}")

    content = path.read_text(encoding="utf-8").strip()
    pieces = chunk_text(content, settings.rag_chunk_size, settings.rag_chunk_overlap)
    if not pieces:
        parser.error(f"File is empty: {path}")

    chunks = [Chunk(str(path), index, text) for index, text in enumerate(pieces)]
    embedder = EmbeddingProvider(settings.llm_api_key, settings.embedding_model)
    embeddings = embedder.embed([chunk.content for chunk in chunks])
    RAGStore(settings.knowledge_path).replace_document(str(path), chunks, embeddings)
    print(f"Imported: {path} ({len(chunks)} chunks)")


if __name__ == "__main__":
    main()
