from uuid import uuid4

import pytest

from apps.api.app.domain.tables.models import TableCellKind
from apps.api.app.repositories.tables import InMemoryTableRepository
from packages.documents.researchos_documents.schema import (
    DocumentElement,
    DocumentElementType,
)
from packages.documents.researchos_documents.tables import (
    ScientificTableExtractor,
    TableQuestionAnswerer,
)


def test_table_extractor_preserves_headers_rows_numeric_values_and_caption_linkage() -> None:
    element_id = uuid4()
    extractor = ScientificTableExtractor()
    element = DocumentElement(
        id=element_id,
        element_type=DocumentElementType.TABLE,
        page=3,
        section="Results",
        text=(
            "Model | Accuracy | AUC\n"
            "CNN | 88.1 | 0.91\n"
            "ViT | 91.5 | 0.94\n"
            "MissingNet |  | 0.72"
        ),
        caption="Table 1. Classification performance.",
    )

    table = extractor.extract(element)

    assert table.document_element_id == element_id
    assert table.page == 3
    assert table.section == "Results"
    assert table.caption == "Table 1. Classification performance."
    assert [column.name for column in table.columns] == ["Model", "Accuracy", "AUC"]
    assert table.rows[1].cells[2].numeric_value == 0.94
    assert table.rows[2].cells[1].kind == TableCellKind.MISSING
    assert table.semantic_summary == (
        "Table 1. Classification performance. Columns: Model, Accuracy, AUC."
    )


def test_table_question_answerer_uses_structure_for_highest_numeric_column() -> None:
    table = ScientificTableExtractor().extract(
        DocumentElement(
            id=uuid4(),
            element_type=DocumentElementType.TABLE,
            page=4,
            section="Results",
            text="Model | Accuracy | AUC\nCNN | 88.1 | 0.91\nViT | 91.5 | 0.94",
        )
    )

    answer = TableQuestionAnswerer().answer(table, "Which model has highest AUC?")

    assert answer.answer == "ViT has the highest AUC: 0.94."
    assert answer.source_table_id == table.id
    assert answer.source_cell_ids == [table.rows[1].cells[0].id, table.rows[1].cells[2].id]


@pytest.mark.asyncio
async def test_table_repository_persists_tables_with_cells_and_tenant_scope() -> None:
    repository = InMemoryTableRepository()
    organization_id = uuid4()
    blocked_organization_id = uuid4()
    project_id = uuid4()
    document_id = uuid4()
    table = ScientificTableExtractor().extract(
        DocumentElement(
            id=uuid4(),
            element_type=DocumentElementType.TABLE,
            page=2,
            section="Results",
            text="Model | AUC\nCNN | 0.91\nViT | 0.94",
        )
    )

    stored = await repository.create_table(
        organization_id=organization_id,
        project_id=project_id,
        document_id=document_id,
        table=table,
    )
    loaded = await repository.get_table(stored.id, organization_id)
    blocked = await repository.get_table(stored.id, blocked_organization_id)

    assert loaded is not None
    assert loaded.columns[1].name == "AUC"
    assert loaded.rows[1].cells[1].numeric_value == 0.94
    assert blocked is None
