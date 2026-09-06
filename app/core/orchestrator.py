"""Central coordinator for JARVIS requests."""

from app.llm.provider import LLMProvider


SYSTEM_PROMPT = """You are JARVIS, a personal AI operating system.
Be concise, accurate, and practical. When you are unsure, say so.
For now, you only answer the user's request; tools and memory will be added later.
"""


class Orchestrator:
    """Route user input to the configured AI capability."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def respond(self, user_input: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}\nJARVIS:"
        return self._llm.generate(prompt)
