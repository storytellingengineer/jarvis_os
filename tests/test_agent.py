from app.core.agent import AgentVerifier, AgentRuntime


class FakeLLM:
    def generate(self, prompt: str) -> str:
        return "1. inspect the request\n2. execute the required tool\n3. verify the result"

    def generate_with_tools(self, prompt, tools, executor):
        return "Completed after executing the planned actions."


class EmptyLLM(FakeLLM):
    def generate_with_tools(self, prompt, tools, executor):
        return ""


def test_agent_runtime_tracks_plan_execute_verify() -> None:
    runtime = AgentRuntime(FakeLLM(), [], object())
    state = runtime.run("calculate something", "context", lambda name, args: None)
    assert state.status == "verified"
    assert state.steps == ["plan", "execute", "verify"]
    assert state.plan.startswith("1.")


def test_verifier_rejects_empty_result() -> None:
    runtime = AgentRuntime(EmptyLLM(), [], object(), AgentVerifier())
    try:
        runtime.run("do something", "context", lambda name, args: None)
    except RuntimeError as exc:
        assert "empty result" in str(exc)
    else:
        raise AssertionError("Expected verifier to reject an empty result")
