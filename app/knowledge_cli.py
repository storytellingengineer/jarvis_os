"""Import supported documents into JARVIS's local RAG index."""

import argparse
from pathlib import Path

from app.config import settings
from app.core.knowledge import KnowledgeStore, extract_file
from app.core.rag import Chunk, EmbeddingProvider, RAGStore, chunk_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a supported document into JARVIS local RAG."
    )
    parser.add_argument("path", help="Path to a UTF-8 text, Markdown, PDF, or DOCX file")
    args = parser.parse_args()
    path = Path(args.path)

    try:
        content, file_type, size_bytes = extract_file(path)
        pieces = chunk_text(
            content.strip(), settings.rag_chunk_size, settings.rag_chunk_overlap
        )
        if not pieces:
            parser.error(f"File contains no extractable text: {path}")

        chunks = [Chunk(str(path), index, text) for index, text in enumerate(pieces)]
        embedder = EmbeddingProvider(settings.llm_api_key, settings.embedding_model)
        embeddings = embedder.embed([chunk.content for chunk in chunks])

        # Extraction and embedding happen before either persistent store is mutated.
        RAGStore(settings.knowledge_path).replace_document(str(path), chunks, embeddings)
        metadata = KnowledgeStore(settings.knowledge_path).add_document(
            str(path), content, file_type=file_type, size_bytes=size_bytes
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    print(
        f"Imported: {path} ({len(chunks)} chunks, "
        f"document_id={metadata.document_id[:12]}...)"
    )


if __name__ == "__main__":
    main()
