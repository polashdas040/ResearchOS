from uuid import uuid4

import pytest

from packages.agents.researchos_agents.hypothesis import Hypothesis
from packages.agents.researchos_agents.tournament import (
    CandidateEvaluation,
    CriterionScores,
    HypothesisTournament,
    InMemoryTournamentRecordStore,
)


def hypothesis(statement: str) -> Hypothesis:
    return Hypothesis(
        statement=statement,
        rationale="A grounded rationale.",
        required_data=["outcome"],
        falsification_test="The candidate fails to beat the baseline.",
        generation_strategy="strategy",
    )


@pytest.mark.asyncio
async def test_tournament_ranks_candidates_deterministically_and_preserves_judge_evidence() -> None:
    first = hypothesis("Candidate one")
    second = hypothesis("Candidate two")
    evidence_id = uuid4()
    result = await HypothesisTournament().rank(
        [
            CandidateEvaluation(
                hypothesis=second,
                scores=CriterionScores(
                    novelty=0.7,
                    feasibility=0.8,
                    evidence=0.9,
                    importance=0.7,
                    testability=0.8,
                    risk=0.1,
                ),
                evidence_ids=[],
                rationale="Strong evidence and feasibility.",
                major_uncertainties=["Small external validation set."],
                next_experiment="Run external validation.",
            ),
            CandidateEvaluation(
                hypothesis=first,
                scores=CriterionScores(
                    novelty=0.9,
                    feasibility=0.4,
                    evidence=0.5,
                    importance=0.9,
                    testability=0.5,
                    risk=0.4,
                ),
                evidence_ids=[evidence_id],
                rationale="Novel but less feasible.",
                major_uncertainties=[],
                next_experiment="Collect more labels.",
            ),
        ]
    )

    assert result.rankings[0].hypothesis_id == second.id
    assert result.rankings[0].rank == 1
    assert result.rankings[1].evaluation.evidence_ids == [evidence_id]
    assert result.rankings[0].evaluation.next_experiment == "Run external validation."
    assert result.rankings[0].score != result.rankings[1].score


@pytest.mark.asyncio
async def test_tournament_rejects_duplicate_candidates() -> None:
    candidate = CandidateEvaluation(
        hypothesis=hypothesis("Duplicate"),
        scores=CriterionScores(
            novelty=0.5, feasibility=0.5, evidence=0.5, importance=0.5, testability=0.5, risk=0.5
        ),
        evidence_ids=[],
        rationale="Recorded judgment.",
        major_uncertainties=[],
        next_experiment="Repeat evaluation.",
    )

    with pytest.raises(ValueError, match="duplicate"):
        await HypothesisTournament().rank([candidate, candidate])


@pytest.mark.asyncio
async def test_tournament_persists_a_reproducible_ranking_record() -> None:
    store = InMemoryTournamentRecordStore()
    candidate = CandidateEvaluation(
        hypothesis=hypothesis("Recorded candidate"),
        scores=CriterionScores(
            novelty=0.8,
            feasibility=0.8,
            evidence=0.8,
            importance=0.8,
            testability=0.8,
            risk=0.1,
        ),
        evidence_ids=[uuid4()],
        rationale="All ranking criteria are recorded.",
        major_uncertainties=["Replication is still needed."],
        next_experiment="Run a preregistered replication.",
    )

    result = await HypothesisTournament(store).rank([candidate])
    stored = await store.get(result.id)

    assert stored == result
    assert stored is not None
    assert stored.rankings[0].evaluation.evidence_ids == candidate.evidence_ids
