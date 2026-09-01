from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models.tables import (
    TableCellRecord,
    TableColumnRecord,
    TableRecord,
    TableRowRecord,
)
from apps.api.app.domain.tables.models import (
    ScientificTable,
    TableCell,
    TableCellKind,
    TableColumn,
    TableRow,
)


class TableRepository(Protocol):
    async def create_table(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        table: ScientificTable,
    ) -> ScientificTable: ...

    async def get_table(self, table_id: UUID, organization_id: UUID) -> ScientificTable | None: ...


class SqlAlchemyTableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_table(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        table: ScientificTable,
    ) -> ScientificTable:
        stored = table.model_copy(
            update={
                "organization_id": organization_id,
                "project_id": project_id,
                "document_id": document_id,
            }
        )
        self._session.add(
            TableRecord(
                id=stored.id,
                organization_id=organization_id,
                project_id=project_id,
                document_id=document_id,
                document_element_id=stored.document_element_id,
                page=stored.page,
                section=stored.section,
                caption=stored.caption,
                semantic_summary=stored.semantic_summary,
            )
        )
        self._session.add_all(_records_for_table(stored))
        await self._session.flush()
        return stored

    async def get_table(self, table_id: UUID, organization_id: UUID) -> ScientificTable | None:
        table_result = await self._session.execute(
            select(TableRecord).where(
                TableRecord.id == table_id,
                TableRecord.organization_id == organization_id,
            )
        )
        table = table_result.scalar_one_or_none()
        if table is None:
            return None
        column_result = await self._session.execute(
            select(TableColumnRecord)
            .where(TableColumnRecord.table_id == table_id)
            .order_by(TableColumnRecord.index)
        )
        row_result = await self._session.execute(
            select(TableRowRecord)
            .where(TableRowRecord.table_id == table_id)
            .order_by(TableRowRecord.index)
        )
        cell_result = await self._session.execute(
            select(TableCellRecord)
            .where(TableCellRecord.table_id == table_id)
            .order_by(TableCellRecord.row_index, TableCellRecord.column_index)
        )
        return _table_from_records(
            table,
            list(column_result.scalars()),
            list(row_result.scalars()),
            list(cell_result.scalars()),
        )


class InMemoryTableRepository:
    def __init__(self) -> None:
        self._tables: dict[UUID, ScientificTable] = {}

    async def create_table(
        self,
        organization_id: UUID,
        project_id: UUID,
        document_id: UUID,
        table: ScientificTable,
    ) -> ScientificTable:
        stored = table.model_copy(
            update={
                "organization_id": organization_id,
                "project_id": project_id,
                "document_id": document_id,
            }
        )
        self._tables[stored.id] = stored
        return stored

    async def get_table(self, table_id: UUID, organization_id: UUID) -> ScientificTable | None:
        table = self._tables.get(table_id)
        if table is None or table.organization_id != organization_id:
            return None
        return table


def _records_for_table(table: ScientificTable) -> list[object]:
    records: list[object] = [
        TableColumnRecord(
            id=column.id,
            table_id=table.id,
            index=column.index,
            name=column.name,
        )
        for column in table.columns
    ]
    for row in table.rows:
        records.append(TableRowRecord(id=row.id, table_id=table.id, index=row.index))
        records.extend(
            TableCellRecord(
                id=cell.id,
                table_id=table.id,
                row_id=row.id,
                row_index=cell.row_index,
                column_index=cell.column_index,
                raw_value=cell.raw_value,
                normalized_value=cell.normalized_value,
                numeric_value=cell.numeric_value,
                kind=cell.kind.value,
            )
            for cell in row.cells
        )
    return records


def _table_from_records(
    table: TableRecord,
    columns: list[TableColumnRecord],
    rows: list[TableRowRecord],
    cells: list[TableCellRecord],
) -> ScientificTable:
    cells_by_row = {
        row.id: [_cell_from_record(cell) for cell in cells if cell.row_id == row.id]
        for row in rows
    }
    return ScientificTable(
        id=table.id,
        organization_id=table.organization_id,
        project_id=table.project_id,
        document_id=table.document_id,
        document_element_id=table.document_element_id,
        page=table.page,
        section=table.section,
        caption=table.caption,
        semantic_summary=table.semantic_summary,
        columns=[
            TableColumn(id=column.id, index=column.index, name=column.name)
            for column in columns
        ],
        rows=[
            TableRow(id=row.id, index=row.index, cells=cells_by_row[row.id])
            for row in rows
        ],
    )


def _cell_from_record(record: TableCellRecord) -> TableCell:
    return TableCell(
        id=record.id,
        row_index=record.row_index,
        column_index=record.column_index,
        raw_value=record.raw_value,
        normalized_value=record.normalized_value,
        numeric_value=record.numeric_value,
        kind=TableCellKind(record.kind),
    )
