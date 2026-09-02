import re
from collections import Counter
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from apps.api.app.domain.rag.models import SemanticChunk
from packages.rag.researchos_rag.vector_store import (
    VectorSearchQuery,
    VectorSearchResult,
    VectorStore,
)


class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict[str, str | int]
    dense_score: float | None = None
    lexical_score: float | None = None


class DenseSearch(Protocol):
    async def search(
        self,
        organization_id: UUID,
        project_id: UUID,
        query_embedding: list[float],
        limit: int,
    ) -> list[RetrievalResult]: ...


class LexicalSearch(Protocol):
    async def search(
        self,
        organization_id: UUID,
        project_id: UUID,
        query: str,
        limit: int,
    ) -> list[RetrievalResult]: ...


class DenseRetriever:
    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store

    async def search(
        self,
        organization_id: UUID,
        project_id: UUID,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[RetrievalResult]:
        vector_results = await self._vector_store.search(
            VectorSearchQuery(
                organization_id=organization_id,
                project_id=project_id,
                embedding=query_embedding,
                limit=limit,
            )
        )
        return [_from_vector_result(result, dense_score=result.score) for result in vector_results]


class LexicalRetriever:
    def __init__(self, chunks: list[SemanticChunk]) -> None:
        self._chunks = chunks

    async def search(
        self,
        organization_id: UUID,
        project_id: UUID,
        query: str,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        query_terms = Counter(_tokenize(query))
        if not query_terms:
            return []

        results = [
            _chunk_result(
                chunk,
                score=_lexical_score(query_terms, Counter(_tokenize(chunk.content))),
            )
            for chunk in self._chunks
            if chunk.organization_id == organization_id and chunk.project_id == project_id
        ]
        ranked = sorted(
            [result for result in results if result.score > 0],
            key=lambda result: (-result.score, str(result.chunk_id)),
        )
        return ranked[:limit]


class HybridRetriever:
    def __init__(
        self,
        dense: DenseSearch,
        lexical: LexicalSearch,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k < 1:
            raise ValueError("rrf_k must be at least 1")
        self._dense = dense
        self._lexical = lexical
        self._rrf_k = int(rrf_k)

    async def search(
        self,
        organization_id: UUID,
        project_id: UUID,
        query: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[RetrievalResult]:
        dense_results = await self._dense.search(
            organization_id,
            project_id,
            query_embedding,
            limit,
        )
        lexical_results = await self._lexical.search(organization_id, project_id, query, limit)
        fused: dict[UUID, RetrievalResult] = {}
        scores: dict[UUID, float] = {}

        for results, channel in ((dense_results, "dense"), (lexical_results, "lexical")):
            for rank, result in enumerate(results, start=1):
                current = fused.get(result.chunk_id)
                if current is None:
                    current = result
                if channel == "dense":
                    current = current.model_copy(update={"dense_score": result.score})
                else:
                    current = current.model_copy(update={"lexical_score": result.score})
                fused[result.chunk_id] = current
                scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (
                    self._rrf_k + rank
                )

        ranked = sorted(
            fused.values(),
            key=lambda result: (
                -scores[result.chunk_id],
                -(result.lexical_score or 0.0),
                -(result.dense_score or 0.0),
                str(result.chunk_id),
            ),
        )
        return [
            result.model_copy(update={"score": scores[result.chunk_id]})
            for result in ranked[:limit]
        ]


def _from_vector_result(result: VectorSearchResult, dense_score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=result.chunk_id,
        document_id=result.document_id,
        content=result.content,
        score=result.score,
        metadata=result.metadata,
        dense_score=dense_score,
    )


def _chunk_result(chunk: SemanticChunk, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        content=chunk.content,
        score=score,
        metadata={
            "tenant_id": str(chunk.organization_id),
            "project_id": str(chunk.project_id),
            "document_id": str(chunk.document_id),
            "page": chunk.page,
            "section": chunk.section or "",
            "element_type": chunk.chunk_type.value,
        },
        lexical_score=score,
    )


def _lexical_score(query_terms: Counter[str], content_terms: Counter[str]) -> float:
    return float(sum(min(count, content_terms[term]) for term, count in query_terms.items()))


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())
