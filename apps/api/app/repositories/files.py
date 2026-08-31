from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.files import FileRecord
from apps.api.app.domain.files.models import FileStatus, ProjectFile


class FileRepository(Protocol):
    async def create_file(
        self,
        project_id: UUID,
        organization_id: UUID,
        uploaded_by_user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        sha256: str,
        storage_key: str,
        duplicate_of_file_id: UUID | None,
    ) -> ProjectFile: ...

    async def list_files(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[ProjectFile], int]: ...

    async def get_file(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None: ...

    async def find_duplicate(
        self,
        project_id: UUID,
        organization_id: UUID,
        sha256: str,
    ) -> ProjectFile | None: ...

    async def mark_deleted(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None: ...


def _file_from_record(record: FileRecord) -> ProjectFile:
    return ProjectFile(
        id=record.id,
        project_id=record.project_id,
        organization_id=record.organization_id,
        uploaded_by_user_id=record.uploaded_by_user_id,
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        sha256=record.sha256,
        storage_key=record.storage_key,
        status=FileStatus(record.status),
        duplicate_of_file_id=record.duplicate_of_file_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


class SqlAlchemyFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_file(
        self,
        project_id: UUID,
        organization_id: UUID,
        uploaded_by_user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        sha256: str,
        storage_key: str,
        duplicate_of_file_id: UUID | None,
    ) -> ProjectFile:
        now = datetime.now(UTC)
        record = FileRecord(
            id=uuid4(),
            project_id=project_id,
            organization_id=organization_id,
            uploaded_by_user_id=uploaded_by_user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256,
            storage_key=storage_key,
            status=FileStatus.READY.value,
            duplicate_of_file_id=duplicate_of_file_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        await self._session.flush()
        return _file_from_record(record)

    async def list_files(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[ProjectFile], int]:
        criteria = (
            FileRecord.project_id == project_id,
            FileRecord.organization_id == organization_id,
            FileRecord.status != FileStatus.DELETED.value,
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(FileRecord).where(*criteria)
        )
        result = await self._session.execute(
            select(FileRecord)
            .where(*criteria)
            .order_by(FileRecord.created_at, FileRecord.id)
            .limit(limit)
            .offset(offset)
        )
        files = [_file_from_record(record) for record in result.scalars()]
        return files, int(total_result.scalar_one())

    async def get_file(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None:
        result = await self._session.execute(
            select(FileRecord).where(
                FileRecord.id == file_id,
                FileRecord.organization_id == organization_id,
                FileRecord.status != FileStatus.DELETED.value,
            )
        )
        record = result.scalar_one_or_none()
        return None if record is None else _file_from_record(record)

    async def find_duplicate(
        self,
        project_id: UUID,
        organization_id: UUID,
        sha256: str,
    ) -> ProjectFile | None:
        result = await self._session.execute(
            select(FileRecord)
            .where(
                FileRecord.project_id == project_id,
                FileRecord.organization_id == organization_id,
                FileRecord.sha256 == sha256,
                FileRecord.status != FileStatus.DELETED.value,
            )
            .order_by(FileRecord.created_at, FileRecord.id)
            .limit(1)
        )
        record = result.scalar_one_or_none()
        return None if record is None else _file_from_record(record)

    async def mark_deleted(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None:
        result = await self._session.execute(
            select(FileRecord).where(
                FileRecord.id == file_id,
                FileRecord.organization_id == organization_id,
                FileRecord.status != FileStatus.DELETED.value,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        record.status = FileStatus.DELETED.value
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return _file_from_record(record)


class InMemoryFileRepository:
    def __init__(self) -> None:
        self._files: dict[UUID, ProjectFile] = {}

    async def create_file(
        self,
        project_id: UUID,
        organization_id: UUID,
        uploaded_by_user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        sha256: str,
        storage_key: str,
        duplicate_of_file_id: UUID | None,
    ) -> ProjectFile:
        now = datetime.now(UTC)
        file = ProjectFile(
            id=uuid4(),
            project_id=project_id,
            organization_id=organization_id,
            uploaded_by_user_id=uploaded_by_user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256,
            storage_key=storage_key,
            status=FileStatus.READY,
            duplicate_of_file_id=duplicate_of_file_id,
            created_at=now,
            updated_at=now,
        )
        self._files[file.id] = file
        return file

    async def list_files(
        self,
        project_id: UUID,
        organization_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[ProjectFile], int]:
        files = [
            file
            for file in self._files.values()
            if file.project_id == project_id
            and file.organization_id == organization_id
            and file.status != FileStatus.DELETED
        ]
        files.sort(key=lambda file: file.created_at)
        return files[offset : offset + limit], len(files)

    async def get_file(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None:
        file = self._files.get(file_id)
        if (
            file is None
            or file.organization_id != organization_id
            or file.status == FileStatus.DELETED
        ):
            return None
        return file

    async def find_duplicate(
        self,
        project_id: UUID,
        organization_id: UUID,
        sha256: str,
    ) -> ProjectFile | None:
        files, _ = await self.list_files(project_id, organization_id, limit=10_000, offset=0)
        for file in files:
            if file.sha256 == sha256:
                return file
        return None

    async def mark_deleted(self, file_id: UUID, organization_id: UUID) -> ProjectFile | None:
        file = await self.get_file(file_id, organization_id)
        if file is None:
            return None
        deleted = file.model_copy(
            update={"status": FileStatus.DELETED, "updated_at": datetime.now(UTC)}
        )
        self._files[file_id] = deleted
        return deleted
