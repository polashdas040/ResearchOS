from dataclasses import dataclass
from uuid import uuid4

import pytest

from apps.api.app.domain.evidence.models import Claim, ClaimStatus, ClaimType
from packages.agents.researchos_agents.gap_analysis import ResearchGap
from packages.agents.researchos_agents.hypothesis import (
    HypothesisGenerationError,
    HypothesisGenerationRequest,
    HypothesisGenerator,
    HypothesisProposal,
)


@dataclass
class FakeHypothesisReasoner:
    proposals: list[HypothesisProposal]
    received_request: HypothesisGenerationRequest | None = None

    async def propose(self, request: HypothesisGenerationRequest) -> list[HypothesisProposal]:
        self.received_request = request
        return self.proposals


@pytest.mark.asyncio
async def test_generator_returns_structured_diverse_hypotheses() -> None:
    claim_id = uuid4()
    gap_id = uuid4()
    reasoner = FakeHypothesisReasoner(
        proposals=[
            HypothesisProposal(
                statement="Longer follow-up improves prediction of cognitive decline.",
                rationale="The evidence is limited by short follow-up windows.",
                mechanism="Additional visits capture delayed effects.",
                required_data=["longitudinal outcomes"],
                supporting_claim_ids=[claim_id],
                supporting_gap_ids=[gap_id],
                falsification_test="Compare the model with and without 24-month follow-up.",
                generation_strategy="temporal_extension",
            ),
            HypothesisProposal(
                statement="A calibrated multimodal model improves prediction of cognitive decline.",
                rationale="Combining modalities may address missing signal.",
                mechanism=None,
                required_data=["imaging", "clinical covariates"],
                supporting_claim_ids=[claim_id],
                supporting_gap_ids=[gap_id],
                falsification_test=(
                    "Test whether multimodal inputs outperform the clinical baseline."
                ),
                generation_strategy="multimodal_combination",
            ),
        ]
    )
    agent = HypothesisGenerator(reasoner)

    result = await agent.generate(
        HypothesisGenerationRequest(
            claims=[
                Claim(
                    id=claim_id,
                    statement="Existing studies have limited follow-up.",
                    claim_type=ClaimType.METHODOLOGICAL,
                    status=ClaimStatus.PROPOSED,
                )
            ],
            gaps=[
                ResearchGap(
                    id=gap_id,
                    description="Long-term follow-up is under-studied.",
                    supporting_claim_ids=[claim_id],
                    confidence=0.8,
                    opportunity="Study longer follow-up.",
                )
            ],
            dataset_profile={"modalities": ["imaging", "clinical"]},
        )
    )

    assert len(result.hypotheses) == 2
    assert result.hypotheses[0].falsification_test
    assert {item.generation_strategy for item in result.hypotheses} == {
        "temporal_extension",
        "multimodal_combination",
    }
    assert reasoner.received_request is not None
    assert reasoner.received_request.dataset_profile["modalities"] == ["imaging", "clinical"]


@pytest.mark.asyncio
async def test_generator_rejects_unknown_evidence_references() -> None:
    reasoner = FakeHypothesisReasoner(
        proposals=[
            HypothesisProposal(
                statement="A new method will solve the problem.",
                rationale="A proposal without valid provenance.",
                required_data=["benchmark"],
                supporting_claim_ids=[uuid4()],
                falsification_test="The method fails to beat the baseline.",
                generation_strategy="baseline_change",
            )
        ]
    )
    agent = HypothesisGenerator(reasoner)

    with pytest.raises(HypothesisGenerationError, match="unknown claim"):
        await agent.generate(HypothesisGenerationRequest())


@pytest.mark.asyncio
async def test_generator_rejects_duplicate_evidence_references() -> None:
    claim_id = uuid4()
    reasoner = FakeHypothesisReasoner(
        proposals=[
            HypothesisProposal(
                statement="A longer follow-up period improves prediction.",
                rationale="The available evidence has short follow-up windows.",
                required_data=["longitudinal outcomes"],
                supporting_claim_ids=[claim_id, claim_id],
                falsification_test="Compare short and long follow-up models.",
                generation_strategy="temporal_extension",
            )
        ]
    )
    claim = Claim(
        id=claim_id,
        statement="Current follow-up periods are short.",
        claim_type=ClaimType.METHODOLOGICAL,
        status=ClaimStatus.PROPOSED,
    )

    with pytest.raises(HypothesisGenerationError, match="duplicate"):
        await HypothesisGenerator(reasoner).generate(HypothesisGenerationRequest(claims=[claim]))


def test_hypothesis_requires_falsification_test() -> None:
    with pytest.raises(ValueError):
        HypothesisProposal(
            statement="A testable proposal.",
            rationale="Because evidence suggests a gap.",
            required_data=[],
            falsification_test="",
            generation_strategy="mechanistic",
        )
