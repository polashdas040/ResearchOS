import hashlib
import re
from uuid import UUID

from apps.api.app.domain.files.models import ProjectFile
from apps.api.app.domain.users.models import User
from apps.api.app.repositories.files import FileRepository
from apps.api.app.services.projects import ProjectService, ResourceNotFoundError
from apps.api.app.services.storage import ObjectStorage

ALLOWED_CONTENT_TYPES = {
    "application/json": ".json",
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "text/csv": ".csv",
    "text/plain": ".txt",
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


class InvalidFileError(Exception):
    """Raised when an uploaded file fails validation."""


class FileService:
    def __init__(
        self,
        project_service: ProjectService,
        file_repository: FileRepository,
        object_storage: ObjectStorage,
    ) -> None:
        self._project_service = project_service
        self._file_repository = file_repository
        self._object_storage = object_storage

    async def upload_file(
        self,
        user: User,
        project_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> ProjectFile:
        project = await self._project_service.get_project(user, project_id)
        safe_filename = _safe_filename(filename)
        _validate_file(safe_filename, content_type, content)
        sha256 = hashlib.sha256(content).hexdigest()
        duplicate = await self._file_repository.find_duplicate(
            project.id,
            project.organization_id,
            sha256,
        )
        storage_key = f"{project.organization_id}/{project.id}/{sha256}/{safe_filename}"
        await self._object_storage.put_object(storage_key, content, content_type)
        return await self._file_repository.create_file(
            project_id=project.id,
            organization_id=project.organization_id,
            uploaded_by_user_id=user.id,
            filename=safe_filename,
            content_type=content_type,
            size_bytes=len(content),
            sha256=sha256,
            storage_key=storage_key,
            duplicate_of_file_id=None if duplicate is None else duplicate.id,
        )

    async def list_files(
        self,
        user: User,
        project_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[ProjectFile], int]:
        project = await self._project_service.get_project(user, project_id)
        return await self._file_repository.list_files(
            project.id,
            project.organization_id,
            limit,
            offset,
        )

    async def get_download(self, user: User, file_id: UUID) -> tuple[ProjectFile, bytes]:
        file = await self._file_repository.get_file(file_id, user.primary_organization_id)
        if file is None:
            raise ResourceNotFoundError("File not found")
        content = await self._object_storage.get_object(file.storage_key)
        if content is None:
            raise ResourceNotFoundError("File content not found")
        return file, content

    async def delete_file(self, user: User, file_id: UUID) -> None:
        file = await self._file_repository.mark_deleted(file_id, user.primary_organization_id)
        if file is None:
            raise ResourceNotFoundError("File not found")
        await self._object_storage.delete_object(file.storage_key)


def _safe_filename(filename: str) -> str:
    name = filename.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1].strip()
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name or name in {".", ".."}:
        raise InvalidFileError("Invalid filename")
    return name[:255]


def _validate_file(filename: str, content_type: str, content: bytes) -> None:
    expected_extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if expected_extension is None:
        raise InvalidFileError("Unsupported file type")
    if not filename.lower().endswith(expected_extension):
        raise InvalidFileError("File extension does not match content type")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise InvalidFileError("File is too large")
