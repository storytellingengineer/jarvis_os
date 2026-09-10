"""Conversation history with optional persistent storage."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    """A single conversation message."""

    role: str
    content: str


class MessageStore(Protocol):
    """Storage interface used by conversation history."""

    def save(self, message: Message) -> None:
        ...

    def load_recent(self, limit: int) -> list[Message]:
        ...

    def clear(self) -> None:
        ...


class ConversationHistory:
    """Store recent messages and optionally persist them."""

    def __init__(self, max_messages: int = 20, store: MessageStore | None = None) -> None:
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2")
        self._max_messages = max_messages
        self._store = store
        self._messages: list[Message] = (
            store.load_recent(max_messages) if store else []
        )

    def add(self, role: str, content: str) -> None:
        """Append a message, persist it when configured, and trim local context."""
        message = Message(role=role, content=content)
        self._messages.append(message)
        self._messages = self._messages[-self._max_messages :]
        if self._store:
            self._store.save(message)

    def as_prompt(self) -> str:
        """Render history as a compact transcript for the LLM."""
        return "\n".join(
            f"{message.role}: {message.content}" for message in self._messages
        )

    def clear(self) -> None:
        """Clear both the active context and persistent history."""
        self._messages.clear()
        if self._store:
            self._store.clear()

    def __len__(self) -> int:
        return len(self._messages)
