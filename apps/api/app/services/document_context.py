import csv
import json
import re
from io import BytesIO, StringIO
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel

from apps.api.app.domain.users.models import User
from apps.api.app.services.files import FileService
from apps.api.app.services.projects import ResourceNotFoundError
from packages.documents.researchos_documents.parser import (
    MalformedDocumentError,
    ScientificPdfParser,
)


class DocumentContextService:
    def __init__(self, file_service: FileService) -> None:
        self._file_service = file_service
        self._parser = ScientificPdfParser()

    async def build_context(
        self,
        user: User,
        file_ids: list[UUID],
        query: str = "",
    ) -> str:
        excerpts: list[str] = []
        references: list[str] = []
        for file_id in file_ids:
            try:
                file, content = await self._file_service.get_download(user, file_id)
            except ResourceNotFoundError:
                continue
            number = len(references) + 1
            references.append(
                _build_ieee_reference(number, file.filename, file.content_type, content)
            )
            pages = _extract_pages(file.filename, file.content_type, content)
            selected_pages = _select_relevant_pages(pages, query)
            if selected_pages:
                excerpts.extend(
                    f"[{number}, p. {page}] Source file: {file.filename}\n{text}"
                    for page, text in selected_pages
                )
            else:
                excerpts.append(
                    f"[{number}] Source file: {file.filename}. No extractable text was found."
                )
        if not references:
            return ""
        return (
            "IEEE REFERENCE CATALOG (use these exact numbers; do not invent sources):\n"
            + "\n".join(references)
            + "\n\nRELEVANT SOURCE EXCERPTS:\n"
            + "\n\n".join(excerpts)
        )

    async def build_reference_catalog(
        self,
        user: User,
        file_ids: list[UUID],
    ) -> list["DocumentReference"]:
        references: list[DocumentReference] = []
        for file_id in file_ids:
            try:
                file, content = await self._file_service.get_download(user, file_id)
            except ResourceNotFoundError:
                continue
            number = len(references) + 1
            references.append(
                DocumentReference(
                    number=number,
                    file_id=file.id,
                    filename=file.filename,
                    citation=_build_ieee_reference(
                        number,
                        file.filename,
                        file.content_type,
                        content,
                    ),
                )
            )
        return references


class DocumentReference(BaseModel):
    number: int
    file_id: UUID
    filename: str
    citation: str


def _extract_pages(filename: str, content_type: str, content: bytes) -> list[tuple[int, str]]:
    if content_type == "text/plain":
        text = _clean_text(content.decode("utf-8", errors="ignore"))
        return _chunk_text(text)
    if content_type == "text/csv":
        return _extract_csv_sections(content)
    if content_type == "application/json":
        return _extract_json_sections(content)
    if content_type != "application/pdf":
        return []
    try:
        parsed = ScientificPdfParser().parse(content, filename, content_type)
        pages: dict[int, list[str]] = {}
        for element in parsed.elements:
            values = [value for value in (element.text, element.caption) if value]
            if values:
                pages.setdefault(element.page, []).extend(values)
        return [
            (page, cleaned)
            for page, values in sorted(pages.items())
            if (cleaned := _clean_text(" ".join(values)))
        ]
    except MalformedDocumentError:
        return _extract_pdf_pages_with_pypdf(content)


def _extract_pdf_pages_with_pypdf(content: bytes) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return [
            (page_number, text)
            for page_number, page in enumerate(reader.pages, start=1)
            if (text := _clean_text(page.extract_text() or ""))
        ]
    except Exception:
        return []


def _extract_csv_sections(content: bytes, rows_per_section: int = 40) -> list[tuple[int, str]]:
    try:
        rows = list(csv.reader(StringIO(content.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error):
        return []
    if not rows:
        return []
    header, data_rows = rows[0], rows[1:]
    batches = [
        data_rows[index:index + rows_per_section]
        for index in range(0, len(data_rows), rows_per_section)
    ]
    if not batches:
        batches = [[]]
    sections: list[tuple[int, str]] = []
    for number, batch in enumerate(batches, start=1):
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(batch)
        if text := output.getvalue().strip():
            sections.append((number, text))
    return sections


def _extract_json_sections(content: bytes) -> list[tuple[int, str]]:
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    return _chunk_text(serialized)


def _chunk_text(text: str, chunk_size: int = 6000) -> list[tuple[int, str]]:
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    remaining = cleaned
    while remaining:
        if len(remaining) <= chunk_size:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = remaining.rfind(" ", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = chunk_size
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return [(number, chunk) for number, chunk in enumerate(chunks, start=1) if chunk]


def _build_ieee_reference(
    number: int,
    filename: str,
    content_type: str,
    content: bytes,
) -> str:
    if content_type == "text/plain":
        embedded_citation = _extract_embedded_citation(content)
        if embedded_citation:
            return _renumber_reference(embedded_citation, number)

    title = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
    author = ""
    year = "n.d."
    doi = ""
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            metadata = reader.metadata
            if metadata:
                title = str(metadata.title or title).strip()
                author = str(metadata.author or "").strip()
                creation_date = metadata.creation_date
                if creation_date is not None:
                    year = str(creation_date.year)
            first_page = reader.pages[0].extract_text() if reader.pages else ""
            doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", first_page or "", re.I)
            if doi_match:
                doi = doi_match.group(0).rstrip(".,;)")
            if year == "n.d.":
                year_match = re.search(r"\b(?:19|20)\d{2}\b", first_page or "")
                if year_match:
                    year = year_match.group(0)
        except Exception:
            pass
    author_prefix = f"{author}, " if author else ""
    suffix = f", doi: {doi}" if doi else ""
    reference = f'[{number}] {author_prefix}"{title}," unpublished manuscript, {year}{suffix}'
    return reference if reference.endswith(".") else f"{reference}."


def _extract_embedded_citation(content: bytes) -> str:
    """Read citations stored by the scholarly-literature import endpoint.

    The unlabelled second non-empty line supports summaries created before the
    explicit ``Citation:`` marker was introduced.
    """
    lines = [line.strip() for line in content.decode("utf-8-sig", errors="ignore").splitlines()]
    for line in lines:
        if line.lower().startswith("citation:"):
            return line.partition(":")[2].strip()

    non_empty = [line for line in lines if line]
    if len(non_empty) >= 3 and non_empty[2].lower() == "summary":
        candidate = non_empty[1]
        if candidate.startswith("[") or '"' in candidate or "doi:" in candidate.lower():
            return candidate
    return ""


def _renumber_reference(citation: str, number: int) -> str:
    normalized = re.sub(r"^\[\d+\]\s*", "", citation.strip())
    return f"[{number}] {normalized}"


def _select_relevant_pages(
    pages: list[tuple[int, str]],
    query: str,
    limit: int = 6,
    excerpt_size: int = 1800,
) -> list[tuple[int, str]]:
    if not pages:
        return []
    terms = {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", query.lower())
        if term not in _STOP_WORDS
    }
    ranked = sorted(
        pages,
        key=lambda item: (
            -sum(item[1].lower().count(term) for term in terms),
            item[0],
        ),
    )
    return [(page, text[:excerpt_size]) for page, text in ranked[:limit]]


def _clean_text(text: str) -> str:
    return " ".join(text.split())


_STOP_WORDS = {
    "about",
    "after",
    "before",
    "context",
    "document",
    "existing",
    "include",
    "paper",
    "section",
    "source",
    "their",
    "this",
    "uploaded",
    "with",
    "write",
}
