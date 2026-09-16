"""Central coordinator for JARVIS requests."""

from __future__ import annotations

import time

from app.core.history import ConversationHistory
from app.core.observability import observability
from app.core.policy import ToolExecutionPolicy
from app.core.tools import ToolRegistry
from app.llm.provider import LLMProvider


SYSTEM_PROMPT = """You are JARVIS, a personal AI operating system.
Be concise, accurate, and practical. When you are unsure, say so.
Use the conversation history to maintain context and answer follow-up questions naturally.
Use available tools when they are appropriate instead of doing tool work manually.
For current, recent, or time-sensitive information, use web search when available.
Never claim that a tool was executed unless the tool result was actually returned.
"""


class Orchestrator:
    """Route user input to the configured AI capability."""

    def __init__(
        self,
        llm: LLMProvider,
        history: ConversationHistory | None = None,
        tools: ToolRegistry | None = None,
        policy: ToolExecutionPolicy | None = None,
    ) -> None:
        self._llm = llm
        self._history = history or ConversationHistory()
        self._tools = tools or ToolRegistry()
        self._policy = policy or ToolExecutionPolicy()

    def respond(self, user_input: str) -> str:
        """Generate a response using conversation context and guarded tools."""
        trace = observability.start(
            "orchestrator.respond",
            model=getattr(self._llm, "_model", "unknown"),
            input_length=len(user_input),
            tool_count=len(self._tools),
        )
        started = time.time()
        self._policy.reset()
        self._history.add("User", user_input)
        trace.event("history_updated", role="user")
        prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{self._history.as_prompt()}\nJARVIS:"

        def execute_tool(name: str, arguments: dict) -> object:
            tool_started = time.time()
            trace.event("tool_started", tool=name)
            try:
                result = self._policy.execute(self._tools, name, arguments)
            except Exception as exc:
                trace.event(
                    "tool_failed",
                    tool=name,
                    duration_ms=round((time.time() - tool_started) * 1000, 2),
                    error=type(exc).__name__,
                )
                raise
            trace.event(
                "tool_finished",
                tool=name,
                duration_ms=round((time.time() - tool_started) * 1000, 2),
            )
            return result

        try:
            generate_with_tools = getattr(self._llm, "generate_with_tools", None)
            if generate_with_tools and len(self._tools):
                trace.event("generation_started", mode="tools")
                response = generate_with_tools(
                    prompt,
                    self._tools.schemas(),
                    execute_tool,
                )
            else:
                trace.event("generation_started", mode="text")
                response = self._llm.generate(prompt)

            self._history.add("JARVIS", response)
            trace.event(
                "response_ready",
                output_length=len(response),
                tool_calls=self._policy.calls_used,
            )
            trace.finish("completed")
            return response
        except Exception as exc:
            trace.finish("failed", type(exc).__name__)
            raise
        finally:
            trace.event(
                "request_metrics",
                duration_ms=round((time.time() - started) * 1000, 2),
                tool_calls=self._policy.calls_used,
            )

    def clear_history(self) -> None:
        """Clear the current session's conversation history."""
        self._history.clear()
