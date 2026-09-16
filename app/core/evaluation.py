"""Deterministic agent evaluation and bounded failure classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    """Small, inspectable quality signal for one agent execution."""

    passed: bool
    score: float
    criteria: dict[str, bool]
    reason: str | None = None


class AgentEvaluator:
    """Evaluate operational properties without judging model chain-of-thought."""

    def evaluate(self, task: str, plan: str, result: str) -> EvaluationResult:
        criteria = {
            "task_present": bool(task.strip()),
            "plan_present": bool(plan.strip()),
            "result_present": bool(result.strip()),
        }
        passed = all(criteria.values())
        score = sum(criteria.values()) / len(criteria)
        reason = None if passed else "; ".join(
            name for name, ok in criteria.items() if not ok
        )
        return EvaluationResult(
            passed=passed,
            score=round(score, 3),
            criteria=criteria,
            reason=reason,
        )


class FailureClassifier:
    """Classify failures into safe retry, terminal, or unknown categories."""

    RETRYABLE = (TimeoutError, ConnectionError)

    def classify(self, error: BaseException) -> str:
        if isinstance(error, self.RETRYABLE):
            return "transient"
        if isinstance(error, PermissionError):
            return "policy"
        if isinstance(error, RuntimeError) and "empty result" in str(error).lower():
            return "empty_result"
        if isinstance(error, RuntimeError) and "maximum tool calls" in str(error).lower():
            return "budget_exhausted"
        return "terminal"


@dataclass(frozen=True)
class RecoveryDecision:
    """Decision made from a failure classification."""

    action: str
    reason: str


class RecoveryPolicy:
    """Allow only bounded retries for failures that are plausibly recoverable."""

    def __init__(self, max_retries: int = 1) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.max_retries = max_retries

    def decide(self, category: str, retries_used: int) -> RecoveryDecision:
        if category in {"transient", "empty_result"} and retries_used < self.max_retries:
            return RecoveryDecision("retry", f"recoverable:{category}")
        return RecoveryDecision("fail", f"terminal:{category}")
