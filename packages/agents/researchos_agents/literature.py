from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LiteratureSearchRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal: str = Field(min_length=1, max_length=10_000)
    limit: int = Field(default=20, ge=1, le=100)
    published_from: int | None = Field(default=None, ge=1800, le=2100)
    published_to: int | None = Field(default=None, ge=1800, le=2100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "LiteratureSearchRequest":
        if (
            self.published_from is not None
            and self.published_to is not None
            and self.published_from > self.published_to
        ):
            raise ValueError("published_from cannot be later than published_to")
        return self


class PaperRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    paper_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    doi: str | None = None
    publication_year: int | None = Field(default=None, ge=1800, le=2100)
    venue: str | None = None
    url: str | None = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="", min_length=0)


class LiteratureSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    queries: list[str]
    papers: list[PaperRecord]


class LiteratureProvider(Protocol):
    async def search(self, query: str, limit: int) -> list[PaperRecord]: ...


class LiteratureAgent:
    def __init__(self, provider: LiteratureProvider) -> None:
        self._provider = provider

    async def search(self, request: LiteratureSearchRequest) -> LiteratureSearchResult:
        queries = _expand_queries(request.goal)
        candidates: list[PaperRecord] = []
        provider_limit = max(request.limit, 20)
        for query in queries:
            records = await self._provider.search(query, provider_limit)
            candidates.extend(
                record.model_copy(update={"reason": f"Matched literature search query: {query}"})
                for record in records
            )

        filtered = [
            paper
            for paper in candidates
            if _within_years(paper, request.published_from, request.published_to)
        ]
        deduplicated = _deduplicate(filtered)
        ranked = sorted(
            deduplicated,
            key=lambda paper: (
                -paper.relevance_score,
                -(paper.publication_year or 0),
                paper.paper_id,
            ),
        )
        return LiteratureSearchResult(queries=queries, papers=ranked[: request.limit])


def _expand_queries(goal: str) -> list[str]:
    normalized = " ".join(goal.split())
    candidates = [
        normalized,
        f"{normalized} systematic review",
        f"{normalized} recent findings",
    ]
    return list(dict.fromkeys(candidates))


def _within_years(
    paper: PaperRecord,
    published_from: int | None,
    published_to: int | None,
) -> bool:
    if paper.publication_year is None:
        return published_from is None and published_to is None
    if published_from is not None and paper.publication_year < published_from:
        return False
    if published_to is not None and paper.publication_year > published_to:
        return False
    return True


def _deduplicate(papers: list[PaperRecord]) -> list[PaperRecord]:
    unique: dict[str, PaperRecord] = {}
    for paper in papers:
        key = _paper_key(paper)
        current = unique.get(key)
        if current is None or _paper_sort_key(paper) < _paper_sort_key(current):
            unique[key] = paper
    return list(unique.values())


def _paper_key(paper: PaperRecord) -> str:
    if paper.doi:
        return f"doi:{paper.doi.strip().lower()}"
    normalized_title = " ".join(paper.title.split()).casefold()
    return f"title:{normalized_title}"


def _paper_sort_key(paper: PaperRecord) -> tuple[float, int, str]:
    return (-paper.relevance_score, -(paper.publication_year or 0), paper.paper_id)
