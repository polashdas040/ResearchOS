import re

from apps.api.app.domain.tables.models import (
    ScientificTable,
    TableAnswer,
    TableCell,
    TableCellKind,
    TableColumn,
    TableRow,
)
from packages.documents.researchos_documents.schema import DocumentElement, DocumentElementType


class TableExtractionError(Exception):
    """Raised when a document table element cannot be structured."""


class ScientificTableExtractor:
    def extract(self, element: DocumentElement) -> ScientificTable:
        if element.element_type != DocumentElementType.TABLE or element.id is None:
            raise TableExtractionError("Table extraction requires a persisted table element")
        lines = [line.strip() for line in (element.text or "").splitlines() if line.strip()]
        if len(lines) < 2:
            raise TableExtractionError("Table requires headers and at least one data row")
        headers = [_normalize_header(value) for value in _split_row(lines[0])]
        columns = [TableColumn(index=index, name=name) for index, name in enumerate(headers)]
        rows = [
            _row_from_values(index, _split_row(line), len(columns))
            for index, line in enumerate(lines[1:])
        ]
        column_names = ", ".join(column.name for column in columns)
        prefix = f"{element.caption} " if element.caption else ""
        return ScientificTable(
            document_element_id=element.id,
            page=element.page,
            section=element.section,
            caption=element.caption,
            columns=columns,
            rows=rows,
            semantic_summary=f"{prefix}Columns: {column_names}.",
        )


class TableQuestionAnswerer:
    def answer(self, table: ScientificTable, question: str) -> TableAnswer:
        normalized_question = question.lower()
        requested_column = _requested_numeric_column(table, normalized_question)
        if requested_column is None or "highest" not in normalized_question:
            return TableAnswer(
                answer="No structured table answer is available for that question.",
                source_table_id=table.id,
                source_cell_ids=[],
            )
        numeric_rows = [
            row
            for row in table.rows
            if row.cells[requested_column.index].numeric_value is not None
        ]
        if not numeric_rows:
            return TableAnswer(
                answer=f"No numeric values are available for {requested_column.name}.",
                source_table_id=table.id,
                source_cell_ids=[],
            )
        best_row = max(
            numeric_rows,
            key=lambda row: row.cells[requested_column.index].numeric_value or float("-inf"),
        )
        label_cell = best_row.cells[0]
        value_cell = best_row.cells[requested_column.index]
        return TableAnswer(
            answer=f"{label_cell.raw_value} has the highest {requested_column.name}: "
            f"{value_cell.raw_value}.",
            source_table_id=table.id,
            source_cell_ids=[label_cell.id, value_cell.id],
        )


def _split_row(line: str) -> list[str]:
    return [value.strip() for value in line.split("|")]


def _requested_numeric_column(
    table: ScientificTable,
    normalized_question: str,
) -> TableColumn | None:
    matching_columns = [
        column for column in table.columns if column.name.lower() in normalized_question
    ]
    return next(
        (
            column
            for column in matching_columns
            if any(row.cells[column.index].numeric_value is not None for row in table.rows)
        ),
        matching_columns[0] if matching_columns else None,
    )


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _row_from_values(index: int, values: list[str], column_count: int) -> TableRow:
    padded = values[:column_count] + [""] * max(0, column_count - len(values))
    return TableRow(
        index=index,
        cells=[
            TableCell(
                row_index=index,
                column_index=column_index,
                raw_value=value,
                normalized_value=None if value == "" else value,
                numeric_value=_numeric_value(value),
                kind=_cell_kind(value),
            )
            for column_index, value in enumerate(padded)
        ],
    )


def _cell_kind(value: str) -> TableCellKind:
    if value == "":
        return TableCellKind.MISSING
    if _numeric_value(value) is not None:
        return TableCellKind.NUMBER
    return TableCellKind.TEXT


def _numeric_value(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None
