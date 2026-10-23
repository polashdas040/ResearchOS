from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.evidence.models import Claim, Evidence


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class ClaimVerificationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim: Claim
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    contradicting_evidence: list[Evidence] = Field(default_factory=list)
    cited_evidence_ids: list[UUID] = Field(default_factory=list)
    requires_experiment_provenance: bool = False
    experiment_provenance_id: UUID | None = None
    requires_statistical_verification: bool = False
    statistical_verification_complete: bool = False


class VerificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: UUID
    status: VerificationStatus
    valid_citation_ids: list[UUID] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class VerificationEngine:
    async def verify(self, request: ClaimVerificationRequest) -> VerificationResult:
        supporting_ids = {item.id for item in request.supporting_evidence}
        contradicting_ids = {item.id for item in request.contradicting_evidence}
        known_ids = supporting_ids | contradicting_ids
        valid_citations = [
            citation for citation in request.cited_evidence_ids if citation in known_ids
        ]
        issues: list[str] = []
        invalid_citations = set(request.cited_evidence_ids) - known_ids
        if invalid_citations:
            issues.append("Citation references evidence that is not available.")
        if supporting_ids and not valid_citations:
            issues.append("Supported claim requires at least one valid citation.")
        if request.requires_experiment_provenance and request.experiment_provenance_id is None:
            issues.append("Experiment provenance is required but unavailable.")
        if (
            request.requires_statistical_verification
            and not request.statistical_verification_complete
        ):
            issues.append("Statistical verification is required but incomplete.")

        if contradicting_ids:
            status = VerificationStatus.CONTRADICTED
        elif not supporting_ids:
            status = VerificationStatus.UNSUPPORTED
        elif issues:
            status = VerificationStatus.PARTIALLY_VERIFIED
        else:
            status = VerificationStatus.VERIFIED
        return VerificationResult(
            claim_id=request.claim.id,
            status=status,
            valid_citation_ids=valid_citations,
            issues=issues,
        )
