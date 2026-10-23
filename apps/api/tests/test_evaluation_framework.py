import pytest

from packages.evaluation.researchos_evaluation.framework import (
    EvaluationCase,
    EvaluationFramework,
)


@pytest.mark.asyncio
async def test_evaluation_framework_computes_retrieval_and_task_metrics() -> None:
    report = await EvaluationFramework().evaluate(
        [
            EvaluationCase(
                case_id="retrieval-1",
                expected_ids=["a", "b"],
                retrieved_ids=["b", "a", "c"],
                task_completed=True,
                citation_correct=True,
                cost=2.0,
                latency_ms=100,
                recovered=False,
            ),
            EvaluationCase(
                case_id="retrieval-2",
                expected_ids=["d"],
                retrieved_ids=["x"],
                task_completed=False,
                citation_correct=False,
                cost=4.0,
                latency_ms=300,
                recovered=True,
            ),
        ]
    )

    assert report.metrics["recall_at_k"] == 0.5
    assert report.metrics["mrr"] == 0.5
    assert report.metrics["task_completion"] == 0.5
    assert report.metrics["citation_correctness"] == 0.5
    assert report.metrics["average_cost"] == 3.0
    assert report.metrics["average_latency_ms"] == 200.0
    assert report.metrics["recovery_rate"] == 0.5


@pytest.mark.asyncio
async def test_evaluation_framework_rejects_empty_cases_and_preserves_case_ids() -> None:
    with pytest.raises(ValueError, match="at least one"):
        await EvaluationFramework().evaluate([])

    report = await EvaluationFramework().evaluate(
        [
            EvaluationCase(
                case_id="case-1",
                expected_ids=[],
                retrieved_ids=[],
                task_completed=True,
                citation_correct=True,
                cost=1.0,
                latency_ms=10,
                recovered=True,
            )
        ]
    )
    assert report.case_ids == ["case-1"]
