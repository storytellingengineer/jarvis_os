from app.core.agent import AgentVerifier, AgentRuntime
from app.core.evaluation import AgentEvaluator, FailureClassifier, RecoveryPolicy
from app.core.policy import ToolExecutionPolicy


class FakeLLM:
    def generate(self, prompt: str) -> str:
        return "1. inspect the request\n2. execute the required tool\n3. verify the result"

    def generate_with_tools(self, prompt, tools, executor):
        return "Completed after executing the planned actions."


class EmptyThenGoodLLM(FakeLLM):
    def __init__(self):
        self.calls = 0

    def generate_with_tools(self, prompt, tools, executor):
        self.calls += 1
        return "" if self.calls == 1 else "Recovered successfully."


class EmptyLLM(FakeLLM):
    def generate_with_tools(self, prompt, tools, executor):
        return ""


def test_agent_runtime_tracks_plan_execute_verify() -> None:
    runtime = AgentRuntime(FakeLLM(), [], ToolExecutionPolicy())
    state = runtime.run("calculate something", "context", lambda name, args: None)
    assert state.status == "verified"
    assert state.steps == ["plan", "execute", "verify"]
    assert state.plan.startswith("1.")
    assert state.evaluation_score == 1.0


def test_verifier_rejects_empty_result() -> None:
    runtime = AgentRuntime(EmptyLLM(), [], ToolExecutionPolicy(), AgentVerifier())
    try:
        runtime.run("do something", "context", lambda name, args: None)
    except RuntimeError as exc:
        assert "empty result" in str(exc).lower()
    else:
        raise AssertionError("Expected verifier to reject an empty result")


def test_empty_result_is_recovered_once() -> None:
    llm = EmptyThenGoodLLM()
    runtime = AgentRuntime(
        llm,
        [],
        ToolExecutionPolicy(),
        recovery=RecoveryPolicy(max_retries=1),
    )
    state = runtime.run("do something", "context", lambda name, args: None)
    assert state.status == "verified"
    assert state.recovery_attempts == 1
    assert state.steps == ["plan", "execute", "recover", "execute", "verify"]
    assert llm.calls == 2


def test_recovery_policy_does_not_retry_policy_failures() -> None:
    decision = RecoveryPolicy(max_retries=3).decide("policy", 0)
    assert decision.action == "fail"


def test_evaluator_returns_deterministic_score() -> None:
    result = AgentEvaluator().evaluate("task", "plan", "answer")
    assert result.passed is True
    assert result.score == 1.0
    assert result.criteria == {
        "task_present": True,
        "plan_present": True,
        "result_present": True,
    }


def test_failure_classifier_categorizes_known_failures() -> None:
    classifier = FailureClassifier()
    assert classifier.classify(TimeoutError()) == "transient"
    assert classifier.classify(PermissionError("denied")) == "policy"
    assert classifier.classify(RuntimeError("Agent produced an empty result")) == "empty_result"
