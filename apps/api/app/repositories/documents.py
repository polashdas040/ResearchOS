from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.documents import DocumentElementRecord, DocumentRecord
from apps.api.app.domain.documents.models import ParsedDocument, StructuredDocument
from packages.documents.researchos_documents.schema import (
    BoundingBox,
    DocumentElement,
    DocumentElementType,
)


class DocumentRepository(Protocol):
    async def create_document(
        self,
        organization_id: UUID,
        project_id: UUID,
        file_id: UUID,
        parsed: StructuredDocument,
    ) -> ParsedDocument: ...

    async def get_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> ParsedDocument | None: ...


class SqlAlchemyDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_document(
        self,
        organization_id: UUID,
        project_id: UUID,
        file_id: UUID,
        parsed: StructuredDocument,
    ) -> ParsedDocument:
        now = datetime.now(UTC)
        document_id = uuid4()
        document = DocumentRecord(
            id=document_id,
            organization_id=organization_id,
            project_id=project_id,
            file_id=file_id,
            title=parsed.title,
            page_count=parsed.page_count,
            created_at=now,
            updated_at=now,
        )
        self._session.add(document)
        element_records = [
            _element_record(document_id, organization_id, project_id, element, index)
            for index, element in enumerate(parsed.elements)
        ]
        self._session.add_all(element_records)
        await self._session.flush()
        return _parsed_document(document, element_records)

    async def get_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> ParsedDocument | None:
        document_result = await self._session.execute(
            select(DocumentRecord).where(
                DocumentRecord.id == document_id,
                DocumentRecord.organization_id == organization_id,
            )
        )
        document = document_result.scalar_one_or_none()
        if document is None:
            return None
        element_result = await self._session.execute(
            select(DocumentElementRecord)
            .where(
                DocumentElementRecord.document_id == document_id,
                DocumentElementRecord.organization_id == organization_id,
            )
            .order_by(DocumentElementRecord.sequence_index)
        )
        return _parsed_document(document, list(element_result.scalars()))


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self._documents: dict[UUID, ParsedDocument] = {}

    async def create_document(
        self,
        organization_id: UUID,
        project_id: UUID,
        file_id: UUID,
        parsed: StructuredDocument,
    ) -> ParsedDocument:
        now = datetime.now(UTC)
        document = ParsedDocument(
            id=uuid4(),
            organization_id=organization_id,
            project_id=project_id,
            file_id=file_id,
            title=parsed.title,
            page_count=parsed.page_count,
            elements=[
                element.model_copy(update={"id": element.id or uuid4()})
                for element in parsed.elements
            ],
            created_at=now,
            updated_at=now,
        )
        self._documents[document.id] = document
        return document

    async def get_document(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> ParsedDocument | None:
        document = self._documents.get(document_id)
        if document is None or document.organization_id != organization_id:
            return None
        return document


def _element_record(
    document_id: UUID,
    organization_id: UUID,
    project_id: UUID,
    element: DocumentElement,
    index: int,
) -> DocumentElementRecord:
    bbox = element.bbox
    return DocumentElementRecord(
        id=element.id or uuid4(),
        document_id=document_id,
        organization_id=organization_id,
        project_id=project_id,
        element_type=element.element_type.value,
        page=element.page,
        section=element.section,
        bbox_x0=None if bbox is None else bbox.x0,
        bbox_y0=None if bbox is None else bbox.y0,
        bbox_x1=None if bbox is None else bbox.x1,
        bbox_y1=None if bbox is None else bbox.y1,
        text=element.text,
        caption=element.caption,
        parent_id=element.parent_id,
        sequence_index=index,
    )


def _parsed_document(
    document: DocumentRecord,
    elements: list[DocumentElementRecord],
) -> ParsedDocument:
    return ParsedDocument(
        id=document.id,
        organization_id=document.organization_id,
        project_id=document.project_id,
        file_id=document.file_id,
        title=document.title,
        page_count=document.page_count,
        elements=[_element_from_record(element) for element in elements],
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _element_from_record(record: DocumentElementRecord) -> DocumentElement:
    bbox = (
        None
        if record.bbox_x0 is None
        else BoundingBox(
            x0=record.bbox_x0,
            y0=record.bbox_y0 or 0,
            x1=record.bbox_x1 or 0,
            y1=record.bbox_y1 or 0,
        )
    )
    return DocumentElement(
        id=record.id,
        element_type=DocumentElementType(record.element_type),
        page=record.page,
        section=record.section,
        bbox=bbox,
        text=record.text,
        caption=record.caption,
        parent_id=record.parent_id,
    )
