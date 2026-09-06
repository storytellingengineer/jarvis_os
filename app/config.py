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


settings = Settings()
