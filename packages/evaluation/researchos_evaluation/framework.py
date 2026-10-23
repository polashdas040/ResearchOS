from pydantic import BaseModel, ConfigDict, Field


class EvaluationCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str = Field(min_length=1)
    expected_ids: list[str]
    retrieved_ids: list[str]
    task_completed: bool
    citation_correct: bool
    cost: float = Field(ge=0.0)
    latency_ms: float = Field(ge=0.0)
    recovered: bool


class EvaluationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_ids: list[str]
    metrics: dict[str, float]


class EvaluationFramework:
    async def evaluate(self, cases: list[EvaluationCase]) -> EvaluationReport:
        if not cases:
            raise ValueError("evaluation requires at least one case")
        total = len(cases)
        recall_scores = [
            _recall(case.expected_ids, case.retrieved_ids)
            for case in cases
        ]
        reciprocal_ranks = [
            _reciprocal_rank(case.expected_ids, case.retrieved_ids)
            for case in cases
        ]
        return EvaluationReport(
            case_ids=[case.case_id for case in cases],
            metrics={
                "recall_at_k": round(sum(recall_scores) / total, 6),
                "mrr": round(sum(reciprocal_ranks) / total, 6),
                "task_completion": round(
                    sum(case.task_completed for case in cases) / total, 6
                ),
                "citation_correctness": round(
                    sum(case.citation_correct for case in cases) / total, 6
                ),
                "average_cost": round(sum(case.cost for case in cases) / total, 6),
                "average_latency_ms": round(
                    sum(case.latency_ms for case in cases) / total, 6
                ),
                "recovery_rate": round(sum(case.recovered for case in cases) / total, 6),
            },
        )


def _recall(expected_ids: list[str], retrieved_ids: list[str]) -> float:
    if not expected_ids:
        return 1.0
    return len(set(expected_ids) & set(retrieved_ids)) / len(set(expected_ids))


def _reciprocal_rank(expected_ids: list[str], retrieved_ids: list[str]) -> float:
    expected = set(expected_ids)
    if not expected:
        return 1.0
    for index, retrieved_id in enumerate(retrieved_ids, start=1):
        if retrieved_id in expected:
            return 1 / index
    return 0.0
