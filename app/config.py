"""Application configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Environment-backed settings for JARVIS OS."""

    llm_provider: str = os.getenv("LLM_PROVIDER", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")


settings = Settings()
