import html
import re
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


class ScholarlySearchError(Exception):
    """Raised when a scholarly provider cannot return usable evidence."""


class ScholarlyReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    title: str
    citation: str
    evidence: str
    url: str | None = None
    pdf_url: str | None = None


class OpenAlexScholarlySearch:
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout_seconds = timeout_seconds

    async def search(self, query: str, limit: int = 5) -> list[ScholarlyReference]:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.get(
                    "https://api.openalex.org/works",
                    params={"search": query, "per-page": min(max(limit * 4, 10), 50)},
                    headers={"User-Agent": "ResearchOS/0.1 (scholarly-reference-search)"},
                )
                response.raise_for_status()
            except httpx.HTTPError:
                return await self._search_crossref(client, query, limit)

            results = response.json().get("results", [])
            references: list[ScholarlyReference] = []
            for work in results:
                reference = _parse_openalex_work(work, len(references) + 1)
                if reference is not None:
                    references.append(reference)
                if len(references) >= limit:
                    break
            return references or await self._search_crossref(client, query, limit)

    async def _search_crossref(
        self,
        client: httpx.AsyncClient,
        query: str,
        limit: int,
    ) -> list[ScholarlyReference]:
        try:
            response = await client.get(
                "https://api.crossref.org/works",
                params={
                    "query.bibliographic": query,
                    "rows": min(max(limit * 10, 20), 50),
                    "select": "DOI,title,author,published,container-title,abstract,URL",
                },
                headers={"User-Agent": "ResearchOS/0.1 (mailto:researchos@example.com)"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ScholarlySearchError("Scholarly search is temporarily unavailable") from exc
        references: list[ScholarlyReference] = []
        items = response.json().get("message", {}).get("items", [])
        for item in items:
            reference = _parse_crossref_work(item, len(references) + 1)
            if reference is not None:
                references.append(reference)
            if len(references) >= limit:
                break
        return references


def _parse_openalex_work(work: dict[str, Any], number: int) -> ScholarlyReference | None:
    title = _clean(str(work.get("display_name") or work.get("title") or ""))
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
    if not title or not abstract:
        return None
    authors = [
        _clean(str(authorship.get("author", {}).get("display_name") or ""))
        for authorship in work.get("authorships", [])
    ]
    authors = [author for author in authors if author]
    year = work.get("publication_year")
    source = _clean(
        str(((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "")
    )
    doi = str(work.get("doi") or "").removeprefix("https://doi.org/")
    source_id = str(work.get("id") or doi or title)
    primary_location = work.get("primary_location") or {}
    best_open_access = work.get("best_oa_location") or {}
    url = str(work.get("doi") or primary_location.get("landing_page_url") or "")
    pdf_url = str(best_open_access.get("pdf_url") or primary_location.get("pdf_url") or "")
    return ScholarlyReference(
        source_id=source_id,
        title=title,
        citation=_format_ieee_reference(number, authors, title, source, year, doi),
        evidence=abstract[:2400],
        url=url or None,
        pdf_url=pdf_url or None,
    )


def _parse_crossref_work(item: dict[str, Any], number: int) -> ScholarlyReference | None:
    titles = item.get("title") or []
    title = _clean(str(titles[0] if titles else ""))
    abstract = _strip_markup(str(item.get("abstract") or ""))
    if not title or not abstract:
        return None
    authors = [
        _clean(
            " ".join(
                str(value)
                for value in (author.get("given"), author.get("family"))
                if value
            )
        )
        for author in item.get("author", [])
    ]
    authors = [author for author in authors if author]
    date_parts = (item.get("published") or {}).get("date-parts") or []
    year = date_parts[0][0] if date_parts and date_parts[0] else None
    containers = item.get("container-title") or []
    source = _clean(str(containers[0] if containers else ""))
    doi = _clean(str(item.get("DOI") or ""))
    url = _clean(str(item.get("URL") or ""))
    return ScholarlyReference(
        source_id=f"doi:{doi}" if doi else url or title,
        title=title,
        citation=_format_ieee_reference(number, authors, title, source, year, doi),
        evidence=abstract[:2400],
        url=url or None,
        pdf_url=None,
    )


def _reconstruct_abstract(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        if not isinstance(positions, list):
            continue
        positioned.extend(
            (position, str(word)) for position in positions if isinstance(position, int)
        )
    return _clean(" ".join(word for _, word in sorted(positioned)))


def _format_ieee_reference(
    number: int,
    authors: list[str],
    title: str,
    source: str,
    year: Any,
    doi: str,
) -> str:
    author_text = _format_authors(authors)
    parts = [f"[{number}] {author_text}," if author_text else f"[{number}]", f'"{title},"']
    if source:
        parts.append(source + ",")
    if year:
        parts.append(str(year) + ",")
    if doi:
        parts.append(f"doi: {doi}")
    return " ".join(parts).rstrip(" ,") + "."


def _format_authors(authors: list[str]) -> str:
    formatted = [_format_author(author) for author in authors[:6]]
    if len(authors) > 6:
        return ", ".join(formatted) + ", et al."
    if len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", and " + formatted[-1]
    return formatted[0] if formatted else ""


def _format_author(author: str) -> str:
    parts = author.replace(",", " ").split()
    if len(parts) < 2:
        return author
    initials = " ".join(f"{part[0].upper()}." for part in parts[:-1] if part)
    return f"{initials} {parts[-1]}".strip()


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_markup(value: str) -> str:
    return _clean(html.unescape(re.sub(r"<[^>]+>", " ", value)))
