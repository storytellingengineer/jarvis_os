from app.core.retrieval_eval import (
    RetrievalCase,
    aggregate_scores,
    evaluate_cases,
    extract_sources,
    score_retrieval,
)


def test_extract_sources_preserves_ranked_unique_sources() -> None:
    result = (
        "[guide.md#chunk-2]\ntext\n\n"
        "[guide.md#chunk-4]\ntext\n\n"
        "[faq.md#chunk-1]\ntext"
    )
    assert extract_sources(result) == ("guide.md", "faq.md")


def test_score_retrieval_returns_reciprocal_rank() -> None:
    case = RetrievalCase("reset password", frozenset({"faq.md"}))
    result = "[guide.md#chunk-0]\ntext\n\n[faq.md#chunk-1]\ntext"

    score = score_retrieval(case, result)

    assert score.hit is True
    assert score.reciprocal_rank == 0.5
    assert score.retrieved_sources == ("guide.md", "faq.md")


def test_aggregate_scores_returns_hit_rate_and_mrr() -> None:
    scores = [
        score_retrieval(
            RetrievalCase("one", frozenset({"one.md"})),
            "[one.md#chunk-0]\ntext",
        ),
        score_retrieval(
            RetrievalCase("two", frozenset({"two.md"})),
            "No matching local knowledge was found.",
        ),
    ]

    assert aggregate_scores(scores) == {"hit_rate": 0.5, "mrr": 0.5}


def test_evaluate_cases_runs_retriever_and_aggregates_scores() -> None:
    cases = [
        RetrievalCase("reset password", frozenset({"faq.md"})),
        RetrievalCase("install app", frozenset({"guide.md"})),
    ]
    responses = {
        "reset password": "[faq.md#chunk-0]\ntext",
        "install app": "[other.md#chunk-0]\ntext\n\n[guide.md#chunk-1]\ntext",
    }

    assert evaluate_cases(cases, responses.__getitem__) == {
        "hit_rate": 1.0,
        "mrr": 0.75,
    }
