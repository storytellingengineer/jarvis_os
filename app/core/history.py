"""In-memory conversation history for a single JARVIS session."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    """A single conversation message."""

    role: str
    content: str


class ConversationHistory:
    """Store recent conversation turns without persistence."""

    def __init__(self, max_messages: int = 20) -> None:
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2")
        self._max_messages = max_messages
        self._messages: list[Message] = []

    def add(self, role: str, content: str) -> None:
        """Append a message and keep only the most recent messages."""
        self._messages.append(Message(role=role, content=content))
        self._messages = self._messages[-self._max_messages :]

    def as_prompt(self) -> str:
        """Render history as a compact transcript for the LLM."""
        return "\n".join(
            f"{message.role}: {message.content}" for message in self._messages
        )

    def clear(self) -> None:
        """Remove all messages from the current session."""
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
