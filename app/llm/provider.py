"""Provider-independent interface for language models."""

from typing import Protocol


class LLMProvider(Protocol):
    """Minimal interface the orchestrator needs from an LLM."""

    def generate(self, prompt: str) -> str:
        """Generate a response for a user prompt."""
        ...
