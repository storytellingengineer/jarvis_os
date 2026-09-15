"""LLM-facing hybrid RAG retrieval tool."""

from app.config import settings
from app.core.rag import EmbeddingProvider, RAGStore


def search_knowledge(query: str, limit: int = 5) -> str:
    """Search JARVIS's local personal knowledge with semantic + keyword retrieval."""
    embedder = EmbeddingProvider(settings.llm_api_key, settings.embedding_model)
    query_embedding = embedder.embed([query])[0]
    return RAGStore(settings.knowledge_path).search(query, query_embedding, limit)
