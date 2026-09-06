from app.core.orchestrator import Orchestrator


class FakeLLM:
    def __init__(self) -> None:
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "Hello from JARVIS."


def test_orchestrator_returns_llm_response() -> None:
    llm = FakeLLM()
    jarvis = Orchestrator(llm)

    result = jarvis.respond("Hello")

    assert result == "Hello from JARVIS."
    assert "User: Hello" in llm.last_prompt
