import pytest

from app.core.multiagent import MultiAgentRuntime, SpecialistAgent, VerifierAgent


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


def test_verifier_approves_non_empty_specialist_output() -> None:
    runtime = MultiAgentRuntime(
        {"coding": SpecialistAgent("coding", lambda context: "implemented")},
        verifier=VerifierAgent(),
    )

    context = runtime.run("Implement this function")

    assert context.artifacts["verification"] == "approved"
    assert context.events[-1] == "verifier:approved"


def test_verifier_rejects_empty_specialist_output() -> None:
    runtime = MultiAgentRuntime(
        {"coding": SpecialistAgent("coding", lambda context: "")},
        verifier=VerifierAgent(),
    )

    with pytest.raises(RuntimeError, match="Verifier rejected"):
        runtime.run("Implement this function")
