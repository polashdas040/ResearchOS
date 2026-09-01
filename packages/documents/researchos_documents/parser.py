from packages.documents.researchos_documents.schema import (
    DocumentElement,
    DocumentElementType,
    StructuredDocument,
)


class MalformedDocumentError(Exception):
    """Raised when a scientific document cannot be parsed safely."""


class ScientificPdfParser:
    def parse(self, content: bytes, filename: str, content_type: str) -> StructuredDocument:
        if content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
            raise MalformedDocumentError("Only PDF documents are supported")
        if not content.startswith(b"%PDF"):
            raise MalformedDocumentError("Malformed PDF document")

        text = content.decode("utf-8", errors="ignore")
        elements: list[DocumentElement] = []
        current_page = 1
        max_page = 1
        current_section: str | None = None
        pending_table: list[str] = []

        def flush_table() -> None:
            if pending_table:
                elements.append(
                    DocumentElement(
                        element_type=DocumentElementType.TABLE,
                        page=current_page,
                        section=current_section,
                        text="\n".join(pending_table),
                    )
                )
                pending_table.clear()

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("PAGE "):
                flush_table()
                current_page = _parse_page(line)
                max_page = max(max_page, current_page)
                continue
            element_type, value = _parse_tagged_line(line)
            if element_type is None:
                continue
            if element_type != DocumentElementType.TABLE:
                flush_table()
            if element_type == DocumentElementType.HEADING:
                current_section = value
            if element_type == DocumentElementType.TABLE:
                pending_table.append(value)
                continue
            elements.append(
                DocumentElement(
                    element_type=element_type,
                    page=current_page,
                    section=current_section if element_type != DocumentElementType.TITLE else None,
                    text=None if element_type == DocumentElementType.FIGURE else value,
                    caption=value if element_type == DocumentElementType.FIGURE else None,
                )
            )
        flush_table()
        if not elements:
            raise MalformedDocumentError("No structured document content found")
        title = next(
            (
                element.text
                for element in elements
                if element.element_type == DocumentElementType.TITLE
            ),
            None,
        )
        return StructuredDocument(title=title, page_count=max_page, elements=elements)


def _parse_page(line: str) -> int:
    try:
        page = int(line.removeprefix("PAGE ").strip())
    except ValueError as exc:
        raise MalformedDocumentError("Invalid page marker") from exc
    if page < 1:
        raise MalformedDocumentError("Invalid page marker")
    return page


def _parse_tagged_line(line: str) -> tuple[DocumentElementType | None, str]:
    for element_type in DocumentElementType:
        prefix = f"{element_type.value}:"
        if line.startswith(prefix):
            return element_type, line.removeprefix(prefix).strip()
    return None, ""
