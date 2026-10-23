import mimetypes
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import get_current_user, get_db_session
from apps.api.app.api.routers.projects import get_project_service
from apps.api.app.config import get_settings
from apps.api.app.domain.files.models import ProjectFile
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.files import FileRepository, SqlAlchemyFileRepository
from apps.api.app.schemas.files import (
    FileListResponse,
    FileReferenceListResponse,
    FileReferenceResponse,
    FileResponse,
)
from apps.api.app.services.document_context import DocumentContextService
from apps.api.app.services.files import FileService, InvalidFileError
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError
from apps.api.app.services.storage import MinioObjectStorage, ObjectStorage

router = APIRouter(tags=["files"])

def get_file_repository(
    session: Annotated[AsyncSession, Depends(get_db_session, scope="function")],
) -> FileRepository:
    return SqlAlchemyFileRepository(session)


@lru_cache
def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    return MinioObjectStorage(
        endpoint=str(settings.object_storage_endpoint),
        bucket=settings.object_storage_bucket,
        access_key=settings.object_storage_access_key,
        secret_key=settings.object_storage_secret_key,
    )


def get_file_service(
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    object_storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> FileService:
    return FileService(project_service, file_repository, object_storage)


@router.post(
    "/projects/{project_id}/files",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_file(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
    file: Annotated[UploadFile, File()],
) -> FileResponse:
    try:
        content = await file.read()
        uploaded = await service.upload_file(
            user=current_user,
            project_id=project_id,
            filename=file.filename or "",
            content_type=(
                file.content_type
                or mimetypes.guess_type(file.filename or "")[0]
                or ""
            ),
            content=content,
        )
    except InvalidFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
    return _file_response(uploaded)


@router.get("/projects/{project_id}/files", response_model=FileListResponse)
async def list_project_files(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FileListResponse:
    try:
        files, total = await service.list_files(current_user, project_id, limit, offset)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
    return FileListResponse(
        items=[_file_response(file) for file in files],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/projects/{project_id}/file-references",
    response_model=FileReferenceListResponse,
)
async def list_project_file_references(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
) -> FileReferenceListResponse:
    try:
        files, _ = await service.list_files(current_user, project_id, 100, 0)
        references = await DocumentContextService(service).build_reference_catalog(
            current_user,
            [file.id for file in files if file.status.value == "READY"],
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from exc
    return FileReferenceListResponse(
        items=[FileReferenceResponse(**reference.model_dump()) for reference in references]
    )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
) -> FastAPIResponse:
    try:
        file, content = await service.get_download(current_user, file_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc
    return FastAPIResponse(
        content=content,
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[FileService, Depends(get_file_service)],
) -> Response:
    try:
        await service.delete_file(current_user, file_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _file_response(file: ProjectFile) -> FileResponse:
    return FileResponse(
        id=file.id,
        project_id=file.project_id,
        organization_id=file.organization_id,
        uploaded_by_user_id=file.uploaded_by_user_id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=file.size_bytes,
        sha256=file.sha256,
        status=file.status,
        duplicate_of_file_id=file.duplicate_of_file_id,
        created_at=file.created_at,
        updated_at=file.updated_at,
    )
