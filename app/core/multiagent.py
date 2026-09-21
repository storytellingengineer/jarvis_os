"""Composable multi-agent orchestration primitives for JARVIS OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass
class AgentContext:
    """Shared, mutable context passed between agents in one run."""

    task: str
    route: str = "general"
    artifacts: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentResult:
    """A bounded result produced by one agent."""

    agent: str
    output: str
    next_agent: str | None = None


class Agent(Protocol):
    """Contract implemented by every JARVIS specialist agent."""

    name: str

    def run(self, context: AgentContext) -> AgentResult:
        ...


class SupervisorAgent:
    """Route requests to a specialist using transparent deterministic rules."""

    name = "supervisor"

    def run(self, context: AgentContext) -> AgentResult:
        task = context.task.lower()
        if any(term in task for term in ("document", "knowledge", "according to", "from my")):
            route = "knowledge"
        elif any(term in task for term in ("code", "debug", "implement", "function", "test")):
            route = "coding"
        elif any(term in task for term in ("research", "latest", "compare", "find")):
            route = "research"
        else:
            route = "general"
        context.route = route
        context.events.append(f"supervisor:routed:{route}")
        return AgentResult(self.name, f"Route selected: {route}", next_agent=route)


class SpecialistAgent:
    """Small adapter for registering a specialist before LLM-backed behavior exists."""

    def __init__(self, name: str, handler: Callable[[AgentContext], str]) -> None:
        if not name.strip():
            raise ValueError("Agent name must not be empty")
        self.name = name
        self._handler = handler

    def run(self, context: AgentContext) -> AgentResult:
        output = self._handler(context)
        context.artifacts[self.name] = output
        context.events.append(f"{self.name}:completed")
        return AgentResult(self.name, output)


class VerifierAgent:
    """Validate specialist output and record the verification decision."""

    name = "verifier"

    def __init__(self, validator: Callable[[AgentContext, AgentResult], bool] | None = None) -> None:
        self._validator = validator or (lambda context, result: bool(result.output.strip()))

    def run(self, context: AgentContext, result: AgentResult) -> AgentResult:
        if not self._validator(context, result):
            context.events.append("verifier:rejected")
            raise RuntimeError(f"Verifier rejected output from {result.agent}")
        context.events.append("verifier:approved")
        context.artifacts["verification"] = "approved"
        return AgentResult(self.name, "Output verified")


class MultiAgentRuntime:
    """Execute supervisor routing, a specialist, and an optional verifier."""

    def __init__(
        self,
        agents: dict[str, Agent],
        supervisor: Agent | None = None,
        verifier: VerifierAgent | None = None,
    ) -> None:
        self._agents = dict(agents)
        self._supervisor = supervisor or SupervisorAgent()
        self._verifier = verifier

    def run(self, task: str) -> AgentContext:
        if not task.strip():
            raise ValueError("Task must not be empty")
        context = AgentContext(task=task)
        decision = self._supervisor.run(context)
        specialist = self._agents.get(decision.next_agent or "")
        if specialist is None:
            context.events.append("runtime:no_specialist")
            return context
        result = specialist.run(context)
        if self._verifier is not None:
            self._verifier.run(context, result)
        return context
