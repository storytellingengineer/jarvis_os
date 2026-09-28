"""Tests for orchestration quality signals."""

from app.core.evaluation import AgentEvaluator


def test_agent_evaluator_passes_complete_execution():
    result = AgentEvaluator().evaluate(
        "summarize the project",
        "Use the project context and produce a concise summary.",
        "The project is a local-first multi-agent runtime.",
    )
    assert result.passed is True
    assert result.score == 1.0
    assert all(result.criteria.values())


def test_agent_evaluator_flags_empty_result_without_model_judgement():
    result = AgentEvaluator().evaluate(
        "summarize the project",
        "Use the project context.",
        "",
    )
    assert result.passed is False
    assert result.score == 2 / 3
    assert result.criteria["result_present"] is False
    assert result.reason == "result_present"
