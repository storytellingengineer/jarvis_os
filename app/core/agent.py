"""Lightweight planner/executor/verifier runtime for JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


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
        state = TaskState(task=task)
        state.plan = self._plan(task)
        state.steps.append("plan")
        state.status = "executing"

        generate_with_tools = getattr(self._llm, "generate_with_tools", None)
        if generate_with_tools and len(self._tools):
            execution_prompt = (
                f"{context}\n\nAgent execution plan:\n{state.plan}\n\n"
                "Execute the plan using available tools when appropriate. "
                "You may perform multiple tool calls, but stay within the tool execution policy. "
                "Return the final answer only after completing the necessary actions."
            )
            state.result = generate_with_tools(
                execution_prompt,
                self._tools.schemas(),
                executor,
            )
        else:
            state.result = self._llm.generate(f"{context}\n\nPlan:\n{state.plan}")

        state.steps.append("execute")
        return self._verifier.verify(state)
