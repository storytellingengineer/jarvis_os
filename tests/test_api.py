from fastapi.testclient import TestClient

import app.api as api
from app.core.multiagent import MultiAgentRuntime, SpecialistAgent, VerifierAgent
from app.core.runtime import JarvisRuntime, RuntimeState


class FakeOrchestrator:
    def respond(self, message: str) -> str:
        return f"echo: {message}"

    def clear_history(self) -> None:
        return None


def make_test_service() -> api.JarvisService:
    orchestrator = FakeOrchestrator()
    agents = {
        name: SpecialistAgent(name, lambda context: orchestrator.respond(context.task))
        for name in ("knowledge", "coding", "research", "general")
    }
    lifecycle = JarvisRuntime(
        MultiAgentRuntime(agents, verifier=VerifierAgent()),
        session_id="api-test",
    )
    lifecycle.start()
    return api.JarvisService(
        orchestrator=orchestrator,
        memory=None,  # The API tests do not need a database.
        lifecycle=lifecycle,
    )


def test_health_endpoint() -> None:
    client = TestClient(api.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "jarvis-os",
        "version": "0.7.0",
    }


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(api.app)
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_runs_through_stateful_runtime(monkeypatch) -> None:
    service = make_test_service()
    monkeypatch.setattr(api, "runtime", service)

    client = TestClient(api.app)
    response = client.post("/chat", json={"message": "Hello JARVIS"})

    assert response.status_code == 200
    assert response.json() == {"response": "echo: Hello JARVIS"}
    assert service.lifecycle.session.turn_count == 1
    assert service.lifecycle.session.state is RuntimeState.READY
    assert "runtime:turn_completed" in service.lifecycle.session.events
    assert "verifier:approved" in service.lifecycle.session.events


def test_runtime_lifecycle_endpoints(monkeypatch) -> None:
    service = make_test_service()
    monkeypatch.setattr(api, "runtime", service)
    client = TestClient(api.app)

    status = client.get("/runtime")
    assert status.status_code == 200
    assert status.json()["state"] == "ready"
    assert status.json()["session_id"] == "api-test"

    slept = client.post("/runtime/sleep")
    assert slept.status_code == 200
    assert slept.json()["state"] == "sleeping"

    rejected = client.post("/chat", json={"message": "should not run"})
    assert rejected.status_code == 409

    awake = client.post("/runtime/wake")
    assert awake.status_code == 200
    assert awake.json()["state"] == "ready"

    stopped = client.post("/runtime/stop")
    assert stopped.status_code == 200
    assert stopped.json()["state"] == "stopped"

    restarted = client.post("/runtime/wake")
    assert restarted.status_code == 200
    assert restarted.json()["state"] == "ready"


def test_clear_memory_endpoint_uses_orchestrator(monkeypatch) -> None:
    service = make_test_service()
    monkeypatch.setattr(api, "runtime", service)

    response = TestClient(api.app).delete("/memory")

    assert response.status_code == 204
