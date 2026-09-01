from uuid import uuid4

import pytest

from apps.api.app.domain.documents.models import (
    DocumentElement,
    DocumentElementType,
    StructuredDocument,
)
from apps.api.app.repositories.documents import InMemoryDocumentRepository


@pytest.mark.asyncio
async def test_document_repository_persists_elements_with_project_scope() -> None:
    repository = InMemoryDocumentRepository()
    organization_id = uuid4()
    other_organization_id = uuid4()
    project_id = uuid4()
    file_id = uuid4()

    stored = await repository.create_document(
        organization_id=organization_id,
        project_id=project_id,
        file_id=file_id,
        parsed=StructuredDocument(
            title="Structured MRI Paper",
            page_count=1,
            elements=[
                DocumentElement(
                    element_type=DocumentElementType.TITLE,
                    page=1,
                    text="Structured MRI Paper",
                ),
                DocumentElement(
                    element_type=DocumentElementType.FIGURE,
                    page=1,
                    section="Methods",
                    caption="Figure 1. Pipeline overview.",
                ),
            ],
        ),
    )

    loaded = await repository.get_document(stored.id, organization_id)
    blocked = await repository.get_document(stored.id, other_organization_id)

    assert loaded is not None
    assert loaded.title == "Structured MRI Paper"
    assert loaded.elements[1].element_type == DocumentElementType.FIGURE
    assert loaded.elements[1].caption == "Figure 1. Pipeline overview."
    assert blocked is None
