"""Execution guardrails for JARVIS agent tool calls."""

from dataclasses import dataclass, field
from typing import Any

from app.core.tools import ToolRegistry


@dataclass
class ToolExecutionPolicy:
    """Restrict which tools an agent may execute and bound tool-call loops."""

    allowed_tools: set[str] | None = None
    max_tool_calls: int = 5
    _calls: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_tool_calls < 1:
            raise ValueError("max_tool_calls must be at least 1")

    def reset(self) -> None:
        """Reset the tool-call budget for a new user request."""
        self._calls = 0

    def execute(
        self,
        registry: ToolRegistry,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Validate and execute one tool call."""
        if self.allowed_tools is not None and name not in self.allowed_tools:
            raise PermissionError(f"Tool is not allowed: {name}")
        if self._calls >= self.max_tool_calls:
            raise RuntimeError("Maximum tool calls exceeded for this request")

        self._calls += 1
        return registry.execute(name, arguments)

    @property
    def calls_used(self) -> int:
        return self._calls
