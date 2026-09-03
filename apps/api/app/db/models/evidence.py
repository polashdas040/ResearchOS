from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(500), nullable=False)
    page: Mapped[int | None] = mapped_column(nullable=True)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quote_span: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_statement: Mapped[str] = mapped_column(Text, nullable=False)
    reliability_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class ClaimRecord(Base):
    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class ClaimEvidenceLinkRecord(Base):
    __tablename__ = "claim_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "claim_id",
            "evidence_id",
            "relationship",
            name="uq_claim_evidence_relationship",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claims.id"), nullable=False, index=True)
    evidence_id: Mapped[UUID] = mapped_column(ForeignKey("evidence.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    relationship: Mapped[str] = mapped_column(String(32), nullable=False)
