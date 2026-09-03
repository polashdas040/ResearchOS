from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ClaimType(StrEnum):
    DESCRIPTIVE = "DESCRIPTIVE"
    ASSOCIATIVE = "ASSOCIATIVE"
    PREDICTIVE = "PREDICTIVE"
    CAUSAL = "CAUSAL"
    MECHANISTIC = "MECHANISTIC"
    METHODOLOGICAL = "METHODOLOGICAL"


class ClaimStatus(StrEnum):
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    source_type: str
    source_id: str
    page: int | None = None
    section: str | None = None
    quote_span: str | None = None
    extracted_statement: str
    reliability_score: float | None = Field(default=None, ge=0.0, le=1.0)


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    statement: str
    claim_type: ClaimType
    supporting_evidence: list[UUID] = Field(default_factory=list)
    contradicting_evidence: list[UUID] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: ClaimStatus


class EvidenceGraphTraversal(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim: Claim
    supporting_evidence: list[Evidence]
    contradicting_evidence: list[Evidence]
