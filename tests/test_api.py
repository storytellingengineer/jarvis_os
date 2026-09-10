from fastapi.testclient import TestClient

from app.api import app, runtime


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "jarvis-os"}


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(app)
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_endpoint_uses_runtime(monkeypatch) -> None:
    class FakeOrchestrator:
        def respond(self, message: str) -> str:
            return f"echo: {message}"

    monkeypatch.setattr("app.api.runtime", type("Runtime", (), {"orchestrator": FakeOrchestrator()})())

    client = TestClient(app)
    response = client.post("/chat", json={"message": "Hello JARVIS"})

    assert response.status_code == 200
    assert response.json() == {"response": "echo: Hello JARVIS"}
