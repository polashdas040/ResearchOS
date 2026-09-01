from uuid import UUID, uuid4

import pytest

from apps.api.app.domain.documents.models import DocumentElementType
from apps.api.app.repositories.documents import InMemoryDocumentRepository
from apps.api.app.repositories.files import InMemoryFileRepository
from apps.api.app.services.storage import InMemoryObjectStorage
from apps.worker.app.documents import DocumentParseJobHandler


@pytest.mark.asyncio
async def test_document_parse_job_reads_file_and_persists_structured_document() -> None:
    organization_id = uuid4()
    project_id = uuid4()
    user_id = uuid4()
    file_repository = InMemoryFileRepository()
    document_repository = InMemoryDocumentRepository()
    object_storage = InMemoryObjectStorage()
    storage_key = f"{organization_id}/{project_id}/paper.pdf"
    await object_storage.put_object(
        storage_key,
        b"""%PDF-1.4
PAGE 1
TITLE: Scientific Figure Paper
ABSTRACT: We analyze a biomedical workflow.
FIGURE: Figure 1. Workflow diagram.
%%EOF
""",
        "application/pdf",
    )
    file = await file_repository.create_file(
        project_id=project_id,
        organization_id=organization_id,
        uploaded_by_user_id=user_id,
        filename="paper.pdf",
        content_type="application/pdf",
        size_bytes=128,
        sha256="a" * 64,
        storage_key=storage_key,
        duplicate_of_file_id=None,
    )
    handler = DocumentParseJobHandler(file_repository, document_repository, object_storage)

    result = await handler(
        {
            "organization_id": str(organization_id),
            "file_id": str(file.id),
        }
    )

    document_id = result["document_id"]
    assert isinstance(document_id, str)
    stored = await document_repository.get_document(uuid_from_string(document_id), organization_id)
    assert stored is not None
    assert stored.file_id == file.id
    assert stored.elements[-1].element_type == DocumentElementType.FIGURE


def uuid_from_string(value: object) -> UUID:
    return UUID(str(value))
