"""Stateful runtime layer for long-lived JARVIS sessions.

This module keeps the existing planner/executor/verifier and multi-agent
primitives intact while adding the lifecycle concepts needed by a real
assistant: session state, wake/sleep gating, bounded turns, and safe
proactive hooks.

It intentionally contains no model/provider-specific code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from app.core.multiagent import MultiAgentRuntime


class RuntimeState(str, Enum):
    """Lifecycle state of a JARVIS runtime."""

    SLEEPING = "sleeping"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"


@dataclass
class SessionState:
    """Small, serializable state container for one long-lived session."""

    session_id: str
    state: RuntimeState = RuntimeState.SLEEPING
    turn_count: int = 0
    last_task: str = ""
    events: list[str] = field(default_factory=list)


class JarvisRuntime:
    """Coordinate session lifecycle around the existing agent runtime.

    The runtime deliberately does not own an LLM connection. This keeps voice,
    web, desktop, and future realtime providers replaceable.
    """

    def __init__(
        self,
        agent_runtime: MultiAgentRuntime,
        session_id: str = "default",
        proactive_hook: Callable[[SessionState], str | None] | None = None,
    ) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        self._agent_runtime = agent_runtime
        self._session = SessionState(session_id=session_id)
        self._proactive_hook = proactive_hook

    @property
    def session(self) -> SessionState:
        """Return the current session state."""
        return self._session

    def start(self) -> SessionState:
        """Move a stopped or sleeping runtime into a ready state."""
        if self._session.state is RuntimeState.STOPPED:
            self._session.events.append("runtime:restarted")
        self._session.state = RuntimeState.READY
        self._session.events.append("runtime:ready")
        return self._session

    def wake(self) -> SessionState:
        """Allow the runtime to accept work."""
        if self._session.state is RuntimeState.STOPPED:
            self.start()
        self._session.state = RuntimeState.READY
        self._session.events.append("runtime:wake")
        return self._session

    def sleep(self) -> SessionState:
        """Gate new work without destroying session state."""
        self._session.state = RuntimeState.SLEEPING
        self._session.events.append("runtime:sleep")
        return self._session

    def stop(self) -> SessionState:
        """Stop the runtime while preserving the session metadata."""
        self._session.state = RuntimeState.STOPPED
        self._session.events.append("runtime:stopped")
        return self._session

    def run(self, task: str) -> SessionState:
        """Run one task through the existing multi-agent runtime."""
        if not task.strip():
            raise ValueError("Task must not be empty")
        if self._session.state not in {RuntimeState.READY}:
            raise RuntimeError(f"Runtime is {self._session.state.value}")

        self._session.state = RuntimeState.RUNNING
        self._session.last_task = task
        self._session.turn_count += 1
        self._session.events.append("runtime:turn_started")

        try:
            context = self._agent_runtime.run(task)
            self._session.events.extend(context.events)
            self._session.events.append("runtime:turn_completed")
            return self._session
        except Exception as exc:
            self._session.events.append(
                f"runtime:turn_failed:{type(exc).__name__}"
            )
            raise
        finally:
            self._session.state = RuntimeState.READY

    def proactive_check(self) -> str | None:
        """Run an optional proactive hook without executing user work.

        A hook is intentionally explicit and injected by the host application.
        This prevents hidden background side effects from appearing in the
        core runtime.
        """
        if self._session.state is not RuntimeState.READY:
            return None
        if self._proactive_hook is None:
            return None
        result = self._proactive_hook(self._session)
        if result:
            self._session.events.append("runtime:proactive_signal")
        return result
