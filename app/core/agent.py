"""Lightweight planner/executor/verifier runtime for JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.core.observability import observability


@dataclass
class TaskState:
    """State carried across one agent task."""

    task: str
    plan: str = ""
    result: str = ""
    status: str = "planned"
    steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class AgentVerifier:
    """Apply cheap, deterministic checks before returning an agent result."""

    def verify(self, state: TaskState) -> TaskState:
        if not state.result.strip():
            state.status = "failed"
            state.errors.append("Agent produced an empty result")
            raise RuntimeError("Agent produced an empty result")
        state.status = "verified"
        state.steps.append("verify")
        return state


class AgentRuntime:
    """Run a request through planning, guarded execution, and verification."""

    def __init__(
        self,
        llm: Any,
        tools: Any,
        policy: Any,
        verifier: AgentVerifier | None = None,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._policy = policy
        self._verifier = verifier or AgentVerifier()

    def _plan(self, task: str) -> str:
        prompt = (
            "You are the planning stage of JARVIS. Create a short execution plan for the user request. "
            "List only the actions needed, including tools that may be useful. Do not answer the request.\n\n"
            f"User request:\n{task}"
        )
        return self._llm.generate(prompt).strip()

    def run(
        self,
        task: str,
        context: str,
        executor: Callable[[str, dict[str, Any]], Any],
    ) -> TaskState:
        """Execute one bounded agent task and emit operational trace events."""
        trace = observability.start(
            "agent.run",
            input_length=len(task),
            tool_count=len(self._tools),
        )
        state = TaskState(task=task)
        self._policy.reset()

        try:
            trace.event("planning_started")
            state.plan = self._plan(task)
            state.steps.append("plan")
            trace.event("planning_finished", plan_length=len(state.plan))
            state.status = "executing"

            generate_with_tools = getattr(self._llm, "generate_with_tools", None)
            if generate_with_tools and len(self._tools):
                execution_prompt = (
                    f"{context}\n\nAgent execution plan:\n{state.plan}\n\n"
                    "Execute the plan using available tools when appropriate. "
                    "You may perform multiple tool calls, but stay within the tool execution policy. "
                    "Return the final answer only after completing the necessary actions."
                )
                trace.event("execution_started", mode="tools")
                state.result = generate_with_tools(
                    execution_prompt,
                    self._tools.schemas(),
                    executor,
                )
            else:
                trace.event("execution_started", mode="text")
                state.result = self._llm.generate(f"{context}\n\nPlan:\n{state.plan}")

            state.steps.append("execute")
            trace.event("execution_finished", tool_calls=self._policy.calls_used)
            trace.event("verification_started")
            state = self._verifier.verify(state)
            trace.event("verification_finished", status=state.status)
            trace.finish("completed")
            return state
        except Exception as exc:
            state.status = "failed"
            if not state.errors or state.errors[-1] != str(exc):
                state.errors.append(str(exc))
            trace.finish("failed", type(exc).__name__)
            raise
