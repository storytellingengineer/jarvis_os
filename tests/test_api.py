from fastapi.testclient import TestClient

from app.api import APP_VERSION, app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "jarvis-os",
        "version": APP_VERSION,
    }


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(app)
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_endpoint_uses_runtime(monkeypatch) -> None:
    class FakeOrchestrator:
        def respond(self, message: str) -> str:
            return f"echo: {message}"

    monkeypatch.setattr(
        "app.api.runtime",
        type("Runtime", (), {"orchestrator": FakeOrchestrator()})(),
    )

    client = TestClient(app)
    response = client.post("/chat", json={"message": "Hello JARVIS"})

    assert response.status_code == 200
    assert response.json() == {"response": "echo: Hello JARVIS"}


def test_voice_chat_runs_transcription_agent_and_speech(monkeypatch) -> None:
    calls = []

    class FakeSpeech:
        def transcribe_audio(self, audio_bytes, filename, content_type):
            calls.append(("transcribe", audio_bytes, filename, content_type))
            return "What time is it?"

        def synthesize_speech(self, text):
            calls.append(("synthesize", text))
            return b"fake-mp3-audio"

    class FakeOrchestrator:
        def respond(self, message):
            calls.append(("respond", message))
            return "It is test time."

    fake_runtime = type(
        "Runtime",
        (),
        {"speech": FakeSpeech(), "orchestrator": FakeOrchestrator()},
    )()
    monkeypatch.setattr("app.api.runtime", fake_runtime)

    response = TestClient(app).post(
        "/voice/chat",
        files={"audio": ("sample.webm", b"fake-audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["x-jarvis-transcript"] == "What%20time%20is%20it%3F"
    assert response.headers["x-jarvis-response"] == "It%20is%20test%20time."
    assert response.content == b"fake-mp3-audio"
    assert [call[0] for call in calls] == ["transcribe", "respond", "synthesize"]


def test_voice_chat_rejects_non_audio_upload() -> None:
    response = TestClient(app).post(
        "/voice/chat",
        files={"audio": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 415


def test_voice_chat_rejects_empty_audio() -> None:
    response = TestClient(app).post(
        "/voice/chat",
        files={"audio": ("empty.webm", b"", "audio/webm")},
    )

    assert response.status_code == 400
