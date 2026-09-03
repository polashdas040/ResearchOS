from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.evidence.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    EvidenceGraphTraversal,
)
from apps.api.app.repositories.evidence import InMemoryEvidenceGraphRepository


@pytest.mark.asyncio
async def test_create_claim_and_attach_supporting_evidence() -> None:
    repository = InMemoryEvidenceGraphRepository()
    organization_id = uuid4()
    project_id = uuid4()
    claim = Claim(
        statement="ApoE4 is associated with hippocampal atrophy.",
        claim_type=ClaimType.ASSOCIATIVE,
        status=ClaimStatus.PROPOSED,
    )
    evidence = Evidence(
        project_id=project_id,
        source_type="document_chunk",
        source_id=str(uuid4()),
        page=7,
        section="Results",
        quote_span="ApoE4 carriers showed faster hippocampal atrophy.",
        extracted_statement="ApoE4 carriers showed faster hippocampal atrophy.",
        reliability_score=0.82,
    )

    stored_claim = await repository.create_claim(organization_id, project_id, claim)
    stored_evidence = await repository.create_evidence(organization_id, evidence)
    await repository.support_claim(organization_id, stored_claim.id, stored_evidence.id)

    loaded = await repository.get_claim(organization_id, stored_claim.id)

    assert loaded is not None
    assert loaded.supporting_evidence == [stored_evidence.id]
    assert loaded.contradicting_evidence == []


@pytest.mark.asyncio
async def test_contradictions_are_represented_separately_from_support() -> None:
    repository = InMemoryEvidenceGraphRepository()
    organization_id = uuid4()
    project_id = uuid4()
    claim = await repository.create_claim(
        organization_id,
        project_id,
        Claim(
            statement="ViT always outperforms CNN on medical imaging tasks.",
            claim_type=ClaimType.PREDICTIVE,
            status=ClaimStatus.PROPOSED,
        ),
    )
    evidence = await repository.create_evidence(
        organization_id,
        Evidence(
            project_id=project_id,
            source_type="paper",
            source_id="doi:10.123/example",
            page=None,
            section="Discussion",
            quote_span=None,
            extracted_statement="CNN outperformed ViT in small-data settings.",
            reliability_score=0.74,
        ),
    )

    await repository.contradict_claim(organization_id, claim.id, evidence.id)
    loaded = await repository.get_claim(organization_id, claim.id)

    assert loaded is not None
    assert loaded.supporting_evidence == []
    assert loaded.contradicting_evidence == [evidence.id]


@pytest.mark.asyncio
async def test_provenance_traversal_returns_claim_and_linked_evidence() -> None:
    repository = InMemoryEvidenceGraphRepository()
    organization_id = uuid4()
    project_id = uuid4()
    claim = await repository.create_claim(
        organization_id,
        project_id,
        Claim(
            statement="The dataset contains longitudinal visits.",
            claim_type=ClaimType.DESCRIPTIVE,
            status=ClaimStatus.VERIFIED,
        ),
    )
    support = await repository.create_evidence(
        organization_id,
        evidence_fixture(project_id, "Participants were assessed at baseline and 12 months."),
    )
    contradiction = await repository.create_evidence(
        organization_id,
        evidence_fixture(project_id, "Only baseline data were available."),
    )
    await repository.support_claim(organization_id, claim.id, support.id)
    await repository.contradict_claim(organization_id, claim.id, contradiction.id)

    traversal = await repository.traverse_claim_provenance(organization_id, claim.id)

    assert traversal == EvidenceGraphTraversal(
        claim=claim.model_copy(
            update={
                "supporting_evidence": [support.id],
                "contradicting_evidence": [contradiction.id],
            }
        ),
        supporting_evidence=[support],
        contradicting_evidence=[contradiction],
    )


@pytest.mark.asyncio
async def test_cross_tenant_claim_access_is_blocked() -> None:
    repository = InMemoryEvidenceGraphRepository()
    claim = await repository.create_claim(
        uuid4(),
        uuid4(),
        Claim(
            statement="Private tenant claim.",
            claim_type=ClaimType.DESCRIPTIVE,
            status=ClaimStatus.PROPOSED,
        ),
    )

    loaded = await repository.get_claim(uuid4(), claim.id)

    assert loaded is None


def evidence_fixture(project_id: UUID, statement: str) -> Evidence:
    return Evidence(
        project_id=project_id,
        source_type="document_chunk",
        source_id=str(uuid4()),
        page=1,
        section="Methods",
        quote_span=statement,
        extracted_statement=statement,
        reliability_score=0.8,
    )
