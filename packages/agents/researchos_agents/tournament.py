from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from packages.agents.researchos_agents.hypothesis import Hypothesis


class CriterionScores(BaseModel):
    model_config = ConfigDict(frozen=True)

    novelty: float = Field(ge=0.0, le=1.0)
    feasibility: float = Field(ge=0.0, le=1.0)
    evidence: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    testability: float = Field(ge=0.0, le=1.0)
    risk: float = Field(ge=0.0, le=1.0)


class CandidateEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    hypothesis: Hypothesis
    scores: CriterionScores
    evidence_ids: list[UUID | str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    major_uncertainties: list[str] = Field(default_factory=list)
    next_experiment: str = Field(min_length=1)


class TournamentRanking(BaseModel):
    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1)
    hypothesis_id: UUID
    score: float
    evaluation: CandidateEvaluation


class TournamentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    rankings: list[TournamentRanking] = Field(default_factory=list)


class TournamentRecordStore(Protocol):
    async def save(self, result: TournamentResult) -> TournamentResult: ...

    async def get(self, tournament_id: UUID) -> TournamentResult | None: ...


class InMemoryTournamentRecordStore:
    def __init__(self) -> None:
        self._results: dict[UUID, TournamentResult] = {}

    async def save(self, result: TournamentResult) -> TournamentResult:
        self._results[result.id] = result
        return result

    async def get(self, tournament_id: UUID) -> TournamentResult | None:
        return self._results.get(tournament_id)


class HypothesisTournament:
    def __init__(self, record_store: TournamentRecordStore | None = None) -> None:
        self._record_store = record_store or InMemoryTournamentRecordStore()

    async def rank(self, candidates: list[CandidateEvaluation]) -> TournamentResult:
        hypothesis_ids = [str(candidate.hypothesis.id) for candidate in candidates]
        if len(hypothesis_ids) != len(set(hypothesis_ids)):
            raise ValueError("duplicate hypothesis candidates")
        ordered = sorted(
            ((self._score(candidate), candidate) for candidate in candidates),
            key=lambda item: (-item[0], -item[1].scores.evidence, str(item[1].hypothesis.id)),
        )
        rankings = [
            TournamentRanking(
                rank=index,
                hypothesis_id=candidate.hypothesis.id,
                score=score,
                evaluation=candidate,
            )
            for index, (score, candidate) in enumerate(ordered, start=1)
        ]
        return await self._record_store.save(TournamentResult(rankings=rankings))

    @staticmethod
    def _score(candidate: CandidateEvaluation) -> float:
        scores = candidate.scores
        return round(
            0.20 * scores.novelty
            + 0.20 * scores.feasibility
            + 0.20 * scores.evidence
            + 0.15 * scores.importance
            + 0.15 * scores.testability
            - 0.10 * scores.risk,
            6,
        )
