import asyncio
import time
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class LiteratureQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str = Field(min_length=1)
    text: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class NormalizedPaper(BaseModel):
    model_config = ConfigDict(frozen=True)

    external_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str | None = None
    doi: str | None = None
    source: str = Field(min_length=1)


class ProviderResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    papers: list[NormalizedPaper] = Field(default_factory=list)
    next_cursor: str | None = None
    transient_error: bool = False


class LiteratureTransport(Protocol):
    async def search(self, query: LiteratureQuery) -> ProviderResponse: ...


class ExternalLiteratureClient:
    def __init__(
        self,
        transport: LiteratureTransport,
        cache_ttl_seconds: float = 300.0,
        max_retries: int = 2,
        min_interval_seconds: float = 0.0,
    ) -> None:
        if cache_ttl_seconds < 0 or max_retries < 0 or min_interval_seconds < 0:
            raise ValueError("integration limits cannot be negative")
        self._transport = transport
        self._cache_ttl_seconds = cache_ttl_seconds
        self._max_retries = max_retries
        self._min_interval_seconds = min_interval_seconds
        self._cache: dict[str, tuple[float, ProviderResponse]] = {}
        self._last_request_at = 0.0
        self._lock = asyncio.Lock()

    async def search(self, query: LiteratureQuery) -> ProviderResponse:
        key = query.model_dump_json()
        cached = self._cache.get(key)
        now = time.monotonic()
        if cached is not None and now - cached[0] <= self._cache_ttl_seconds:
            return cached[1]
        async with self._lock:
            cached = self._cache.get(key)
            now = time.monotonic()
            if cached is not None and now - cached[0] <= self._cache_ttl_seconds:
                return cached[1]
            delay = self._min_interval_seconds - (now - self._last_request_at)
            if delay > 0:
                await asyncio.sleep(delay)
            for attempt in range(self._max_retries + 1):
                response = await self._transport.search(query)
                self._last_request_at = time.monotonic()
                if not response.transient_error or attempt == self._max_retries:
                    if response.transient_error:
                        raise RuntimeError("external literature provider failed after retries")
                    self._cache[key] = (time.monotonic(), response)
                    return response
            raise RuntimeError("external literature provider failed")


class IntegrationRegistry:
    def __init__(self) -> None:
        self._literature_clients: dict[str, ExternalLiteratureClient] = {}

    def register(self, provider: str, client: ExternalLiteratureClient) -> None:
        normalized_provider = provider.strip().lower()
        if not normalized_provider:
            raise ValueError("provider name cannot be empty")
        self._literature_clients[normalized_provider] = client

    async def search(self, query: LiteratureQuery) -> ProviderResponse:
        provider = query.provider.strip().lower()
        client = self._literature_clients.get(provider)
        if client is None:
            raise ValueError(f"unsupported literature provider: {query.provider}")
        normalized_query = query.model_copy(update={"provider": provider})
        return await client.search(normalized_query)
