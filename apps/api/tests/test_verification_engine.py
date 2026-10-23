from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.evidence.models import Claim, ClaimStatus, ClaimType, Evidence
from packages.verification.researchos_verification.engine import (
    ClaimVerificationRequest,
    VerificationEngine,
    VerificationStatus,
)


def claim() -> Claim:
    return Claim(
        id=uuid4(),
        statement="The intervention improves outcomes.",
        claim_type=ClaimType.PREDICTIVE,
        status=ClaimStatus.PROPOSED,
    )


def evidence(project_id: UUID) -> Evidence:
    return Evidence(
        project_id=project_id,
        source_type="paper",
        source_id="paper-1",
        extracted_statement="The intervention improved outcomes.",
    )


@pytest.mark.asyncio
async def test_verification_accepts_supported_cited_claim_with_provenance() -> None:
    current_claim = claim()
    source = evidence(uuid4())
    result = await VerificationEngine().verify(
        ClaimVerificationRequest(
            claim=current_claim,
            supporting_evidence=[source],
            cited_evidence_ids=[source.id],
        )
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.valid_citation_ids == [source.id]
    assert result.issues == []


@pytest.mark.asyncio
async def test_verification_surfaces_unsupported_and_contradicted_claims() -> None:
    current_claim = claim()
    source = evidence(uuid4())
    unsupported = await VerificationEngine().verify(
        ClaimVerificationRequest(claim=current_claim)
    )
    contradicted = await VerificationEngine().verify(
        ClaimVerificationRequest(
            claim=current_claim,
            supporting_evidence=[source],
            contradicting_evidence=[source],
        )
    )

    assert unsupported.status == VerificationStatus.UNSUPPORTED
    assert contradicted.status == VerificationStatus.CONTRADICTED


@pytest.mark.asyncio
async def test_verification_rejects_invalid_citations_and_missing_experiment_provenance() -> None:
    current_claim = claim()
    source = evidence(uuid4())
    result = await VerificationEngine().verify(
        ClaimVerificationRequest(
            claim=current_claim,
            supporting_evidence=[source],
            cited_evidence_ids=[uuid4()],
            requires_experiment_provenance=True,
        )
    )

    assert result.status == VerificationStatus.PARTIALLY_VERIFIED
    assert any("citation" in issue.lower() for issue in result.issues)
    assert any("provenance" in issue.lower() for issue in result.issues)


@pytest.mark.asyncio
async def test_verification_marks_supported_claim_without_citation_partial() -> None:
    current_claim = claim()
    source = evidence(uuid4())

    result = await VerificationEngine().verify(
        ClaimVerificationRequest(
            claim=current_claim,
            supporting_evidence=[source],
            cited_evidence_ids=[],
        )
    )

    assert result.status == VerificationStatus.PARTIALLY_VERIFIED
    assert any("citation" in issue.lower() for issue in result.issues)
