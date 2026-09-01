from uuid import UUID

from apps.api.app.repositories.documents import DocumentRepository
from apps.api.app.repositories.files import FileRepository
from apps.api.app.services.storage import ObjectStorage
from packages.documents.researchos_documents.parser import ScientificPdfParser


class DocumentParseJobHandler:
    def __init__(
        self,
        file_repository: FileRepository,
        document_repository: DocumentRepository,
        object_storage: ObjectStorage,
    ) -> None:
        self._file_repository = file_repository
        self._document_repository = document_repository
        self._object_storage = object_storage
        self._parser = ScientificPdfParser()

    async def __call__(self, payload: dict[str, object]) -> dict[str, object]:
        organization_id = UUID(str(payload["organization_id"]))
        file_id = UUID(str(payload["file_id"]))
        file = await self._file_repository.get_file(file_id, organization_id)
        if file is None:
            raise ValueError("File not found")
        content = await self._object_storage.get_object(file.storage_key)
        if content is None:
            raise ValueError("File content not found")
        parsed = self._parser.parse(content, file.filename, file.content_type)
        document = await self._document_repository.create_document(
            organization_id=file.organization_id,
            project_id=file.project_id,
            file_id=file.id,
            parsed=parsed,
        )
        return {
            "document_id": str(document.id),
            "page_count": document.page_count,
            "element_count": len(document.elements),
        }
