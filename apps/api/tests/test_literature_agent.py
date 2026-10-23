from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from packages.agents.researchos_agents.literature import (
    LiteratureAgent,
    LiteratureSearchRequest,
    PaperRecord,
)


@dataclass
class FakeLiteratureProvider:
    records: list[PaperRecord]
    queries: list[str]

    async def search(self, query: str, limit: int) -> list[PaperRecord]:
        self.queries.append(query)
        return self.records[:limit]


@pytest.mark.asyncio
async def test_literature_agent_expands_goal_and_returns_structured_results() -> None:
    provider = FakeLiteratureProvider(
        records=[
            PaperRecord(
                paper_id="paper-1",
                title="Amyloid PET biomarkers in Alzheimer's disease",
                authors=["A. Researcher"],
                abstract="A study of amyloid biomarkers.",
                doi="10.1000/example.1",
                publication_year=2024,
                venue="Journal of Research",
                relevance_score=0.9,
            )
        ],
        queries=[],
    )
    agent = LiteratureAgent(provider)

    result = await agent.search(
        LiteratureSearchRequest(goal="amyloid PET biomarkers in Alzheimer's disease", limit=5)
    )

    assert len(result.queries) >= 2
    assert provider.queries == result.queries
    assert result.papers[0].paper_id == "paper-1"
    assert result.papers[0].reason


@pytest.mark.asyncio
async def test_literature_agent_filters_dates_and_deduplicates_doi_and_title() -> None:
    provider = FakeLiteratureProvider(
        records=[
            PaperRecord(
                paper_id="older",
                title="A Study of Retrieval",
                authors=[],
                publication_year=2018,
                relevance_score=0.99,
            ),
            PaperRecord(
                paper_id="doi-copy",
                title="Different title",
                authors=[],
                doi="10.1000/RETRIEVAL",
                publication_year=2022,
                relevance_score=0.7,
            ),
            PaperRecord(
                paper_id="title-copy",
                title=" A Study   of Retrieval ",
                authors=[],
                publication_year=2023,
                relevance_score=0.8,
            ),
        ],
        queries=[],
    )
    agent = LiteratureAgent(provider)

    result = await agent.search(
        LiteratureSearchRequest(goal="retrieval", limit=10, published_from=2020)
    )

    assert [paper.paper_id for paper in result.papers] == ["title-copy", "doi-copy"]


@pytest.mark.asyncio
async def test_literature_agent_applies_result_limit_after_deduplication() -> None:
    provider = FakeLiteratureProvider(
        records=[
            PaperRecord(
                paper_id=f"paper-{index}",
                title=f"Study {index}",
                authors=[],
                publication_year=2024,
                relevance_score=1.0 - index / 10,
            )
            for index in range(5)
        ],
        queries=[],
    )
    agent = LiteratureAgent(provider)

    result = await agent.search(LiteratureSearchRequest(goal="study", limit=2))

    assert len(result.papers) == 2
    assert [paper.paper_id for paper in result.papers] == ["paper-0", "paper-1"]


def test_literature_search_request_rejects_an_inverted_date_range() -> None:
    with pytest.raises(ValidationError, match="published_from"):
        LiteratureSearchRequest(goal="retrieval", published_from=2025, published_to=2024)
