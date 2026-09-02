import math
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.domain.rag.models import SemanticChunk


class VectorDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    organization_id: UUID
    project_id: UUID
    document_id: UUID
    content: str
    embedding: list[float]
    metadata: dict[str, str | int]

    @classmethod
    def from_chunk(cls, chunk: SemanticChunk, embedding: list[float]) -> "VectorDocument":
        return cls(
            chunk_id=chunk.id,
            organization_id=chunk.organization_id,
            project_id=chunk.project_id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=embedding,
            metadata={
                "tenant_id": str(chunk.organization_id),
                "project_id": str(chunk.project_id),
                "document_id": str(chunk.document_id),
                "page": chunk.page,
                "section": chunk.section or "",
                "element_type": chunk.chunk_type.value,
            },
        )


class VectorSearchQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    project_id: UUID
    embedding: list[float]
    limit: int = Field(ge=1, le=100)


class VectorSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict[str, str | int]


class VectorStore(Protocol):
    async def upsert(self, documents: list[VectorDocument]) -> None: ...

    async def search(self, query: VectorSearchQuery) -> list[VectorSearchResult]: ...

    async def delete_document(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
    ) -> None: ...


class ChromaVectorStore:
    def __init__(self) -> None:
        self._documents: dict[UUID, VectorDocument] = {}

    async def upsert(self, documents: list[VectorDocument]) -> None:
        for document in documents:
            self._documents[document.chunk_id] = document

    async def search(self, query: VectorSearchQuery) -> list[VectorSearchResult]:
        scoped = [
            document
            for document in self._documents.values()
            if document.organization_id == query.organization_id
            and document.project_id == query.project_id
        ]
        ranked = sorted(
            scoped,
            key=lambda document: _cosine_similarity(query.embedding, document.embedding),
            reverse=True,
        )
        return [
            VectorSearchResult(
                chunk_id=document.chunk_id,
                document_id=document.document_id,
                content=document.content,
                score=_cosine_similarity(query.embedding, document.embedding),
                metadata=document.metadata,
            )
            for document in ranked[: query.limit]
        ]

    async def delete_document(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
    ) -> None:
        matching_ids = [
            chunk_id
            for chunk_id, document in self._documents.items()
            if document.organization_id == organization_id
            and document.project_id == project_id
            and document.document_id == document_id
        ]
        for chunk_id in matching_ids:
            del self._documents[chunk_id]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
