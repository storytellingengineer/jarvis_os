"""Deterministic evaluation helpers for local RAG retrieval outputs."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re


_CITATION_PATTERN = re.compile(r"\[([^\]#]+)#chunk-(\d+)\]")


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_sources: frozenset[str]


@dataclass(frozen=True)
class RetrievalScore:
    hit: bool
    reciprocal_rank: float
    retrieved_sources: tuple[str, ...]


def extract_sources(result: str) -> tuple[str, ...]:
    """Extract unique source names from citation headers in ranked order."""
    seen: set[str] = set()
    sources: list[str] = []
    for source, _ in _CITATION_PATTERN.findall(result):
        if source not in seen:
            seen.add(source)
            sources.append(source)
    return tuple(sources)


def score_retrieval(case: RetrievalCase, result: str) -> RetrievalScore:
    """Score a ranked retrieval response using hit rate and reciprocal rank."""
    sources = extract_sources(result)
    expected = set(case.expected_sources)
    rank = next(
        (index for index, source in enumerate(sources, start=1) if source in expected),
        None,
    )
    return RetrievalScore(
        hit=rank is not None,
        reciprocal_rank=1.0 / rank if rank is not None else 0.0,
        retrieved_sources=sources,
    )


def aggregate_scores(scores: Iterable[RetrievalScore]) -> dict[str, float]:
    """Return deterministic aggregate hit-rate and MRR metrics."""
    values = list(scores)
    if not values:
        return {"hit_rate": 0.0, "mrr": 0.0}
    return {
        "hit_rate": sum(score.hit for score in values) / len(values),
        "mrr": sum(score.reciprocal_rank for score in values) / len(values),
    }


def evaluate_cases(
    cases: Iterable[RetrievalCase],
    retrieve: Callable[[str], str],
) -> dict[str, float]:
    """Run a retrieval callable against cases and return aggregate metrics."""
    scores = [score_retrieval(case, retrieve(case.query)) for case in cases]
    return aggregate_scores(scores)
