import asyncio
from typing import Annotated, Literal
from urllib.parse import urlparse

import httpx
from fastapi import Depends
from pydantic import BaseModel

from apps.api.app.config import Settings, get_settings

DependencyState = Literal["ok", "error"]
ReadinessState = Literal["ok", "error"]


class DependencyStatus(BaseModel):
    status: DependencyState
    detail: str | None = None


class ReadinessReport(BaseModel):
    status: ReadinessState
    dependencies: dict[str, DependencyStatus]


class ReadinessChecker:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check(self) -> ReadinessReport:
        dependencies = {
            "postgres": await self._check_tcp_url(str(self._settings.database_url)),
            "redis": await self._check_tcp_url(self._settings.redis_url),
            "chroma": await self._check_http(str(self._settings.chroma_url)),
            "object_storage": await self._check_http(str(self._settings.object_storage_endpoint)),
        }
        status: ReadinessState = (
            "ok" if all(item.status == "ok" for item in dependencies.values()) else "error"
        )
        return ReadinessReport(status=status, dependencies=dependencies)

    async def _check_tcp_url(self, url: str) -> DependencyStatus:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        if host is None or port is None:
            return DependencyStatus(status="error", detail="missing host or port")

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port),
                timeout=2.0,
            )
            writer.close()
            await writer.wait_closed()
            reader.feed_eof()
            return DependencyStatus(status="ok")
        except OSError as exc:
            return DependencyStatus(status="error", detail=str(exc))
        except TimeoutError:
            return DependencyStatus(status="error", detail="connection timed out")

    async def _check_http(self, url: str) -> DependencyStatus:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
            if response.status_code < 500:
                return DependencyStatus(status="ok")
            return DependencyStatus(status="error", detail=f"http {response.status_code}")
        except httpx.HTTPError as exc:
            return DependencyStatus(status="error", detail=str(exc))


def get_readiness_checker(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessChecker:
    return ReadinessChecker(settings=settings)
