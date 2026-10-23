import re
from typing import Annotated
from urllib.parse import urlparse
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.app.api.dependencies import get_current_user
from apps.api.app.api.routers.files import get_file_service
from apps.api.app.api.routers.projects import get_project_service
from apps.api.app.domain.users.models import User
from apps.api.app.schemas.files import FileResponse
from apps.api.app.schemas.literature import (
    LiteratureImportRequest,
    LiteratureReferenceListResponse,
    LiteratureReferenceResponse,
)
from apps.api.app.services.files import MAX_FILE_SIZE_BYTES, FileService, InvalidFileError
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError
from apps.api.app.services.scholarly_search import OpenAlexScholarlySearch, ScholarlySearchError

router = APIRouter(tags=["literature"])


def get_scholarly_search() -> OpenAlexScholarlySearch:
    return OpenAlexScholarlySearch()


@router.get(
    "/projects/{project_id}/literature-references",
    response_model=LiteratureReferenceListResponse,
)
async def search_literature_references(
    project_id: UUID,
    query: Annotated[str, Query(min_length=3, max_length=1000)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    search: Annotated[OpenAlexScholarlySearch, Depends(get_scholarly_search)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> LiteratureReferenceListResponse:
    try:
        await project_service.get_project(current_user, project_id)
        references = await search.search(query, limit)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
    except ScholarlySearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return LiteratureReferenceListResponse(
        items=[
            LiteratureReferenceResponse(number=index, **reference.model_dump())
            for index, reference in enumerate(references, start=1)
        ]
    )


@router.post(
    "/projects/{project_id}/literature-references/import",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_literature_reference(
    project_id: UUID,
    request: LiteratureImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
) -> FileResponse:
    filename = _summary_filename(request.title)
    content_type = "text/plain"
    content = _summary_content(request).encode("utf-8")
    if request.pdf_url and _safe_public_pdf_url(request.pdf_url):
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(request.pdf_url)
                response.raise_for_status()
            if (
                response.content.startswith(b"%PDF")
                and len(response.content) <= MAX_FILE_SIZE_BYTES
            ):
                filename = _pdf_filename(request.title)
                content_type = "application/pdf"
                content = response.content
        except httpx.HTTPError:
            pass
    try:
        uploaded = await service.upload_file(
            current_user,
            project_id,
            filename,
            content_type,
            content,
        )
    except InvalidFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
    return FileResponse.model_validate(uploaded, from_attributes=True)


def _safe_public_pdf_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and bool(host) and host not in {"localhost", "127.0.0.1", "::1"}


def _safe_stem(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", title).strip("_")[:180] or "paper"


def _pdf_filename(title: str) -> str:
    return f"{_safe_stem(title)}.pdf"


def _summary_filename(title: str) -> str:
    return f"{_safe_stem(title)}_summary.txt"


def _summary_content(request: LiteratureImportRequest) -> str:
    lines = [request.title, "", f"Citation: {request.citation}", "", "Summary", request.evidence]
    if request.url:
        lines.extend(["", f"Source: {request.url}"])
    return "\n".join(lines)
