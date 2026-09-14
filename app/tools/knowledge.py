"""LLM-facing local knowledge retrieval tool."""

from app.config import settings
from app.core.knowledge import KnowledgeStore


def search_knowledge(query: str, limit: int = 5) -> str:
    """Search JARVIS's local personal knowledge base."""
    store = KnowledgeStore(settings.knowledge_path)
    return store.search(query, limit)
