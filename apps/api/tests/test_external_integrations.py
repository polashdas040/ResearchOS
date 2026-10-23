from dataclasses import dataclass

import pytest

from packages.tools.researchos_tools.integrations import (
    ExternalLiteratureClient,
    IntegrationRegistry,
    LiteratureQuery,
    NormalizedPaper,
    ProviderResponse,
)


@dataclass
class FakeTransport:
    responses: list[ProviderResponse]
    queries: list[LiteratureQuery]

    async def search(self, query: LiteratureQuery) -> ProviderResponse:
        self.queries.append(query)
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_external_literature_adapter_normalizes_and_caches_results() -> None:
    transport = FakeTransport(
        responses=[
            ProviderResponse(
                papers=[
                    NormalizedPaper(
                        external_id="doi:10.1000/example",
                        title="A Study",
                        authors=["Researcher"],
                        year=2024,
                        source="openalex",
                    )
                ],
                next_cursor="cursor-1",
            )
        ],
        queries=[],
    )
    client = ExternalLiteratureClient(transport, cache_ttl_seconds=60)
    query = LiteratureQuery(provider="openalex", text="amyloid PET", limit=10)

    first = await client.search(query)
    second = await client.search(query)

    assert first == second
    assert len(transport.queries) == 1
    assert first.papers[0].external_id == "doi:10.1000/example"
    assert first.next_cursor == "cursor-1"


@pytest.mark.asyncio
async def test_external_literature_adapter_retries_transient_provider_failure() -> None:
    transport = FakeTransport(
        responses=[
            ProviderResponse(papers=[], transient_error=True),
            ProviderResponse(
                papers=[
                    NormalizedPaper(
                        external_id="paper-1",
                        title="Recovered",
                        authors=[],
                        source="pubmed",
                    )
                ]
            ),
        ],
        queries=[],
    )
    client = ExternalLiteratureClient(transport, max_retries=1)

    result = await client.search(LiteratureQuery(provider="pubmed", text="MRI"))

    assert result.papers[0].title == "Recovered"
    assert len(transport.queries) == 2


@pytest.mark.asyncio
async def test_integration_registry_rejects_unregistered_provider() -> None:
    transport = FakeTransport(responses=[], queries=[])
    registry = IntegrationRegistry()
    registry.register("openalex", ExternalLiteratureClient(transport))

    with pytest.raises(ValueError, match="unsupported literature provider"):
        await registry.search(LiteratureQuery(provider="pubmed", text="amyloid PET"))
