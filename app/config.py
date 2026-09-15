"""Application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Environment-backed settings for JARVIS OS."""

    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-5.6-luna")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    memory_path: str = os.getenv("JARVIS_MEMORY_PATH", "data/jarvis.db")
    knowledge_path: str = os.getenv("JARVIS_KNOWLEDGE_PATH", "data/knowledge.db")
    embedding_model: str = os.getenv("JARVIS_EMBEDDING_MODEL", "text-embedding-3-small")
    rag_chunk_size: int = int(os.getenv("JARVIS_RAG_CHUNK_SIZE", "500"))
    rag_chunk_overlap: int = int(os.getenv("JARVIS_RAG_CHUNK_OVERLAP", "75"))
    web_search_enabled: bool = os.getenv("JARVIS_WEB_SEARCH", "true").lower() in {"1", "true", "yes", "on"}


settings = Settings()
