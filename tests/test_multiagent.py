import pytest

from app.core.multiagent import MultiAgentRuntime, SpecialistAgent


def test_supervisor_routes_knowledge_request() -> None:
    runtime = MultiAgentRuntime(
        {"knowledge": SpecialistAgent("knowledge", lambda context: "retrieved context")}
    )

    context = runtime.run("Answer according to my document")

    assert context.route == "knowledge"
    assert context.artifacts == {"knowledge": "retrieved context"}
    assert context.events == [
        "supervisor:routed:knowledge",
        "knowledge:completed",
    ]


def test_supervisor_routes_coding_request() -> None:
    runtime = MultiAgentRuntime(
        {"coding": SpecialistAgent("coding", lambda context: "implemented")}
    )

    context = runtime.run("Debug this function")

    assert context.route == "coding"
    assert context.artifacts["coding"] == "implemented"


def test_unknown_route_is_safe() -> None:
    context = MultiAgentRuntime({}).run("Tell me a joke")

    assert context.route == "general"
    assert context.artifacts == {}
    assert context.events[-1] == "runtime:no_specialist"


def test_empty_task_is_rejected() -> None:
    with pytest.raises(ValueError, match="Task must not be empty"):
        MultiAgentRuntime({}).run("   ")
