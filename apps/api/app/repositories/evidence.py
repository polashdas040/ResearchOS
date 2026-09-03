from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.evidence import (
    ClaimEvidenceLinkRecord,
    ClaimRecord,
    EvidenceRecord,
)
from apps.api.app.domain.evidence.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    EvidenceGraphTraversal,
)

SUPPORTS = "SUPPORTS"
CONTRADICTS = "CONTRADICTS"


class EvidenceGraphRepository(Protocol):
    async def create_claim(
        self,
        organization_id: UUID,
        project_id: UUID,
        claim: Claim,
    ) -> Claim: ...

    async def create_evidence(self, organization_id: UUID, evidence: Evidence) -> Evidence: ...

    async def get_claim(self, organization_id: UUID, claim_id: UUID) -> Claim | None: ...

    async def support_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None: ...

    async def contradict_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None: ...

    async def traverse_claim_provenance(
        self,
        organization_id: UUID,
        claim_id: UUID,
    ) -> EvidenceGraphTraversal | None: ...


class SqlAlchemyEvidenceGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_claim(
        self,
        organization_id: UUID,
        project_id: UUID,
        claim: Claim,
    ) -> Claim:
        stored = claim.model_copy(update={"project_id": project_id})
        self._session.add(
            ClaimRecord(
                id=stored.id,
                organization_id=organization_id,
                project_id=project_id,
                statement=stored.statement,
                claim_type=stored.claim_type.value,
                confidence=stored.confidence,
                status=stored.status.value,
            )
        )
        await self._session.flush()
        return stored

    async def create_evidence(self, organization_id: UUID, evidence: Evidence) -> Evidence:
        self._session.add(
            EvidenceRecord(
                id=evidence.id,
                organization_id=organization_id,
                project_id=evidence.project_id,
                source_type=evidence.source_type,
                source_id=evidence.source_id,
                page=evidence.page,
                section=evidence.section,
                quote_span=evidence.quote_span,
                extracted_statement=evidence.extracted_statement,
                reliability_score=evidence.reliability_score,
            )
        )
        await self._session.flush()
        return evidence

    async def get_claim(self, organization_id: UUID, claim_id: UUID) -> Claim | None:
        claim = await self._claim_record(organization_id, claim_id)
        if claim is None:
            return None
        links = await self._links_for_claim(organization_id, claim_id)
        return _claim_from_record(claim, links)

    async def support_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None:
        await self._link_claim(organization_id, claim_id, evidence_id, SUPPORTS)

    async def contradict_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None:
        await self._link_claim(organization_id, claim_id, evidence_id, CONTRADICTS)

    async def traverse_claim_provenance(
        self,
        organization_id: UUID,
        claim_id: UUID,
    ) -> EvidenceGraphTraversal | None:
        claim = await self.get_claim(organization_id, claim_id)
        if claim is None:
            return None
        evidence = await self._evidence_for_ids(
            organization_id,
            claim.supporting_evidence + claim.contradicting_evidence,
        )
        by_id = {item.id: item for item in evidence}
        return EvidenceGraphTraversal(
            claim=claim,
            supporting_evidence=[by_id[item_id] for item_id in claim.supporting_evidence],
            contradicting_evidence=[by_id[item_id] for item_id in claim.contradicting_evidence],
        )

    async def _link_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
        relationship: str,
    ) -> None:
        claim = await self._claim_record(organization_id, claim_id)
        evidence = await self._evidence_record(organization_id, evidence_id)
        if claim is None or evidence is None:
            return
        self._session.add(
            ClaimEvidenceLinkRecord(
                organization_id=organization_id,
                claim_id=claim_id,
                evidence_id=evidence_id,
                relationship=relationship,
            )
        )
        await self._session.flush()

    async def _claim_record(self, organization_id: UUID, claim_id: UUID) -> ClaimRecord | None:
        result = await self._session.execute(
            select(ClaimRecord).where(
                ClaimRecord.id == claim_id,
                ClaimRecord.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def _evidence_record(
        self,
        organization_id: UUID,
        evidence_id: UUID,
    ) -> EvidenceRecord | None:
        result = await self._session.execute(
            select(EvidenceRecord).where(
                EvidenceRecord.id == evidence_id,
                EvidenceRecord.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def _links_for_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
    ) -> list[ClaimEvidenceLinkRecord]:
        result = await self._session.execute(
            select(ClaimEvidenceLinkRecord).where(
                ClaimEvidenceLinkRecord.claim_id == claim_id,
                ClaimEvidenceLinkRecord.organization_id == organization_id,
            )
        )
        return list(result.scalars())

    async def _evidence_for_ids(
        self,
        organization_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[Evidence]:
        if not evidence_ids:
            return []
        result = await self._session.execute(
            select(EvidenceRecord).where(
                EvidenceRecord.id.in_(evidence_ids),
                EvidenceRecord.organization_id == organization_id,
            )
        )
        return [_evidence_from_record(record) for record in result.scalars()]


class InMemoryEvidenceGraphRepository:
    def __init__(self) -> None:
        self._claims: dict[UUID, tuple[UUID, Claim]] = {}
        self._evidence: dict[UUID, tuple[UUID, Evidence]] = {}
        self._links: list[tuple[UUID, UUID, UUID, str]] = []

    async def create_claim(
        self,
        organization_id: UUID,
        project_id: UUID,
        claim: Claim,
    ) -> Claim:
        stored = claim.model_copy(update={"project_id": project_id})
        self._claims[stored.id] = (organization_id, stored)
        return stored

    async def create_evidence(self, organization_id: UUID, evidence: Evidence) -> Evidence:
        self._evidence[evidence.id] = (organization_id, evidence)
        return evidence

    async def get_claim(self, organization_id: UUID, claim_id: UUID) -> Claim | None:
        stored = self._claims.get(claim_id)
        if stored is None or stored[0] != organization_id:
            return None
        return self._claim_with_links(organization_id, stored[1])

    async def support_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None:
        self._add_link(organization_id, claim_id, evidence_id, SUPPORTS)

    async def contradict_claim(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
    ) -> None:
        self._add_link(organization_id, claim_id, evidence_id, CONTRADICTS)

    async def traverse_claim_provenance(
        self,
        organization_id: UUID,
        claim_id: UUID,
    ) -> EvidenceGraphTraversal | None:
        claim = await self.get_claim(organization_id, claim_id)
        if claim is None:
            return None
        evidence_by_id = {
            evidence.id: evidence
            for stored_organization_id, evidence in self._evidence.values()
            if stored_organization_id == organization_id
        }
        return EvidenceGraphTraversal(
            claim=claim,
            supporting_evidence=[
                evidence_by_id[evidence_id] for evidence_id in claim.supporting_evidence
            ],
            contradicting_evidence=[
                evidence_by_id[evidence_id] for evidence_id in claim.contradicting_evidence
            ],
        )

    def _add_link(
        self,
        organization_id: UUID,
        claim_id: UUID,
        evidence_id: UUID,
        relationship: str,
    ) -> None:
        claim = self._claims.get(claim_id)
        evidence = self._evidence.get(evidence_id)
        if claim is None or evidence is None:
            return
        if claim[0] != organization_id or evidence[0] != organization_id:
            return
        link = (organization_id, claim_id, evidence_id, relationship)
        if link not in self._links:
            self._links.append(link)

    def _claim_with_links(self, organization_id: UUID, claim: Claim) -> Claim:
        supporting = [
            evidence_id
            for stored_organization_id, claim_id, evidence_id, relationship in self._links
            if stored_organization_id == organization_id
            and claim_id == claim.id
            and relationship == SUPPORTS
        ]
        contradicting = [
            evidence_id
            for stored_organization_id, claim_id, evidence_id, relationship in self._links
            if stored_organization_id == organization_id
            and claim_id == claim.id
            and relationship == CONTRADICTS
        ]
        return claim.model_copy(
            update={
                "supporting_evidence": supporting,
                "contradicting_evidence": contradicting,
            }
        )


def _claim_from_record(
    record: ClaimRecord,
    links: list[ClaimEvidenceLinkRecord],
) -> Claim:
    return Claim(
        id=record.id,
        project_id=record.project_id,
        statement=record.statement,
        claim_type=ClaimType(record.claim_type),
        supporting_evidence=[
            link.evidence_id for link in links if link.relationship == SUPPORTS
        ],
        contradicting_evidence=[
            link.evidence_id for link in links if link.relationship == CONTRADICTS
        ],
        confidence=record.confidence,
        status=ClaimStatus(record.status),
    )


def _evidence_from_record(record: EvidenceRecord) -> Evidence:
    return Evidence(
        id=record.id,
        project_id=record.project_id,
        source_type=record.source_type,
        source_id=record.source_id,
        page=record.page,
        section=record.section,
        quote_span=record.quote_span,
        extracted_statement=record.extracted_statement,
        reliability_score=record.reliability_score,
    )
