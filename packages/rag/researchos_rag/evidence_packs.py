import re
from collections import Counter
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.rag.researchos_rag.retrieval import RetrievalResult


class EvidenceSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID
    page: int | None
    section: str | None
    element_type: str | None
    source_id: str | None = None


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    source: EvidenceSource
    content: str
    retrieval_score: float
    rerank_score: float


class EvidencePack(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    items: list[EvidenceItem] = Field(default_factory=list)


class Reranker(Protocol):
    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        limit: int,
    ) -> list[EvidenceItem]: ...


class KeywordReranker:
    async def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        limit: int = 15,
    ) -> list[EvidenceItem]:
        query_terms = Counter(_tokenize(query))
        scored = [
            (
                index,
                _to_evidence_item(
                    candidate,
                    rerank_score=_keyword_score(
                        query_terms,
                        Counter(_tokenize(candidate.content)),
                    ),
                ),
            )
            for index, candidate in enumerate(candidates)
        ]
        ranked = sorted(
            scored,
            key=lambda ranked_item: (
                -ranked_item[1].rerank_score,
                -ranked_item[1].retrieval_score,
                ranked_item[0],
                str(ranked_item[1].chunk_id),
            ),
        )
        return [item for _, item in ranked[:limit]]


class EvidencePackBuilder:
    def __init__(self, reranker: Reranker) -> None:
        self._reranker = reranker

    async def build(
        self,
        query: str,
        candidates: list[RetrievalResult],
        limit: int = 15,
    ) -> EvidencePack:
        items = await self._reranker.rerank(query=query, candidates=candidates, limit=limit)
        return EvidencePack(query=query, items=items)


def _to_evidence_item(candidate: RetrievalResult, rerank_score: float) -> EvidenceItem:
    return EvidenceItem(
        chunk_id=candidate.chunk_id,
        source=EvidenceSource(
            document_id=candidate.document_id,
            page=_optional_int(candidate.metadata.get("page")),
            section=_optional_str(candidate.metadata.get("section")),
            element_type=_optional_str(candidate.metadata.get("element_type")),
            source_id=_optional_str(candidate.metadata.get("source_id")),
        ),
        content=candidate.content,
        retrieval_score=candidate.score,
        rerank_score=rerank_score,
    )


def _keyword_score(query_terms: Counter[str], content_terms: Counter[str]) -> float:
    if not query_terms:
        return 0.0
    overlap = sum(min(count, content_terms[term]) for term, count in query_terms.items())
    return float(overlap) / float(sum(query_terms.values()))


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())


def _optional_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: str | int | None) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
