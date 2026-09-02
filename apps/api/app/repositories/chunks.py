from typing import Protocol
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.chunks import SemanticChunkRecord
from apps.api.app.domain.rag.models import ChunkType, SemanticChunk


class ChunkRepository(Protocol):
    async def replace_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
        chunks: list[SemanticChunk],
    ) -> list[SemanticChunk]: ...

    async def list_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> list[SemanticChunk]: ...


class SqlAlchemyChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
        chunks: list[SemanticChunk],
    ) -> list[SemanticChunk]:
        await self._session.execute(
            delete(SemanticChunkRecord).where(
                SemanticChunkRecord.document_id == document_id,
                SemanticChunkRecord.organization_id == organization_id,
            )
        )
        self._session.add_all(_record_from_chunk(chunk) for chunk in chunks)
        await self._session.flush()
        return chunks

    async def list_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> list[SemanticChunk]:
        result = await self._session.execute(
            select(SemanticChunkRecord)
            .where(
                SemanticChunkRecord.document_id == document_id,
                SemanticChunkRecord.organization_id == organization_id,
            )
            .order_by(SemanticChunkRecord.sequence_index)
        )
        return [_chunk_from_record(record) for record in result.scalars()]


class InMemoryChunkRepository:
    def __init__(self) -> None:
        self._chunks: dict[tuple[UUID, UUID], list[SemanticChunk]] = {}

    async def replace_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
        chunks: list[SemanticChunk],
    ) -> list[SemanticChunk]:
        self._chunks[(document_id, organization_id)] = chunks
        return chunks

    async def list_document_chunks(
        self,
        document_id: UUID,
        organization_id: UUID,
    ) -> list[SemanticChunk]:
        return self._chunks.get((document_id, organization_id), [])


def _record_from_chunk(chunk: SemanticChunk) -> SemanticChunkRecord:
    return SemanticChunkRecord(
        id=chunk.id,
        organization_id=chunk.organization_id,
        project_id=chunk.project_id,
        document_id=chunk.document_id,
        document_element_id=chunk.document_element_id,
        chunk_type=chunk.chunk_type.value,
        page=chunk.page,
        section=chunk.section,
        content=chunk.content,
        sequence_index=chunk.sequence_index,
    )


def _chunk_from_record(record: SemanticChunkRecord) -> SemanticChunk:
    return SemanticChunk(
        id=record.id,
        organization_id=record.organization_id,
        project_id=record.project_id,
        document_id=record.document_id,
        document_element_id=record.document_element_id,
        chunk_type=ChunkType(record.chunk_type),
        page=record.page,
        section=record.section,
        content=record.content,
        sequence_index=record.sequence_index,
    )
