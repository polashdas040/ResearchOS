from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.figures import FigureRecord
from apps.api.app.domain.figures.models import FigureDescription, ScientificFigure


class FigureRepository(Protocol):
    async def create_figure(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        figure: ScientificFigure,
        description: FigureDescription,
    ) -> ScientificFigure: ...

    async def get_figure(
        self,
        figure_id: UUID,
        organization_id: UUID,
    ) -> ScientificFigure | None: ...


class SqlAlchemyFigureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_figure(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        figure: ScientificFigure,
        description: FigureDescription,
    ) -> ScientificFigure:
        stored = figure.model_copy(
            update={
                "organization_id": organization_id,
                "project_id": project_id,
                "document_id": document_id,
                "description": description,
            }
        )
        self._session.add(_record_from_figure(stored))
        await self._session.flush()
        return stored

    async def get_figure(self, figure_id: UUID, organization_id: UUID) -> ScientificFigure | None:
        result = await self._session.execute(
            select(FigureRecord).where(
                FigureRecord.id == figure_id,
                FigureRecord.organization_id == organization_id,
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _figure_from_record(record)


class InMemoryFigureRepository:
    def __init__(self) -> None:
        self._figures: dict[UUID, ScientificFigure] = {}

    async def create_figure(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        figure: ScientificFigure,
        description: FigureDescription,
    ) -> ScientificFigure:
        stored = figure.model_copy(
            update={
                "organization_id": organization_id,
                "project_id": project_id,
                "document_id": document_id,
                "description": description,
            }
        )
        self._figures[stored.id] = stored
        return stored

    async def get_figure(self, figure_id: UUID, organization_id: UUID) -> ScientificFigure | None:
        figure = self._figures.get(figure_id)
        if figure is None or figure.organization_id != organization_id:
            return None
        return figure


def _record_from_figure(figure: ScientificFigure) -> FigureRecord:
    description = figure.description
    return FigureRecord(
        id=figure.id,
        organization_id=figure.organization_id,
        project_id=figure.project_id,
        document_id=figure.document_id,
        document_element_id=figure.document_element_id,
        page=figure.page,
        section=figure.section,
        caption=figure.caption,
        image_sha256=figure.image_sha256,
        image_content_type=figure.image_content_type,
        figure_type=None if description is None else description.figure_type,
        labels=None if description is None else description.labels,
        components=None if description is None else description.components,
        relationships=None if description is None else description.relationships,
        axes=None if description is None else description.axes,
        trends=None if description is None else description.trends,
        architecture_nodes=None if description is None else description.architecture_nodes,
        medical_anatomy=None if description is None else description.medical_anatomy,
        confidence=None if description is None else description.confidence,
    )


def _figure_from_record(record: FigureRecord) -> ScientificFigure:
    description = None
    if record.figure_type is not None:
        description = FigureDescription(
            figure_type=record.figure_type,
            labels=record.labels or [],
            components=record.components or [],
            relationships=record.relationships or [],
            axes=record.axes or [],
            trends=record.trends or [],
            architecture_nodes=record.architecture_nodes or [],
            medical_anatomy=record.medical_anatomy or [],
            confidence=record.confidence or 0,
            source_page=record.page,
        )
    return ScientificFigure(
        id=record.id,
        organization_id=record.organization_id,
        project_id=record.project_id,
        document_id=record.document_id,
        document_element_id=record.document_element_id,
        page=record.page,
        section=record.section,
        caption=record.caption,
        image_sha256=record.image_sha256,
        image_content_type=record.image_content_type,
        description=description,
    )
