from uuid import UUID, uuid4

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base


class FigureRecord(Base):
    __tablename__ = "figures"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )
    document_element_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_elements.id"),
        nullable=False,
        unique=True,
    )
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    image_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    figure_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    components: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    relationships: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    axes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    trends: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    architecture_nodes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    medical_anatomy: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
