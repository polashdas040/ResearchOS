from pydantic import BaseModel


class LiteratureReferenceResponse(BaseModel):
    number: int
    source_id: str
    title: str
    citation: str
    evidence: str
    url: str | None = None
    pdf_url: str | None = None


class LiteratureImportRequest(BaseModel):
    title: str
    citation: str
    evidence: str
    url: str | None = None
    pdf_url: str | None = None


class LiteratureReferenceListResponse(BaseModel):
    items: list[LiteratureReferenceResponse]
