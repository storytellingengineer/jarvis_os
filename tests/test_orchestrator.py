from app.core.orchestrator import Orchestrator


class FakeLLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"response-{len(self.prompts)}"


def test_orchestrator_returns_llm_response() -> None:
    llm = FakeLLM()
    jarvis = Orchestrator(llm)

    result = jarvis.respond("Hello")

    assert result == "response-1"
    assert "User: Hello" in llm.prompts[0]


def test_orchestrator_preserves_conversation_context() -> None:
    llm = FakeLLM()
    jarvis = Orchestrator(llm)

    jarvis.respond("My project is called JARVIS OS.")
    jarvis.respond("What is my project called?")

    assert "User: My project is called JARVIS OS." in llm.prompts[1]
    assert "JARVIS: response-1" in llm.prompts[1]
    assert "User: What is my project called?" in llm.prompts[1]


def test_orchestrator_can_clear_history() -> None:
    llm = FakeLLM()
    jarvis = Orchestrator(llm)

    jarvis.respond("Remember this temporarily.")
    jarvis.clear_history()
    jarvis.respond("What do you remember?")

    assert "Remember this temporarily." not in llm.prompts[1]
