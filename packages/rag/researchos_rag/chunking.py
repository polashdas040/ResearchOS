from apps.api.app.domain.documents.models import ParsedDocument
from apps.api.app.domain.rag.models import ChunkType, SemanticChunk
from packages.documents.researchos_documents.schema import DocumentElement, DocumentElementType


class SemanticChunker:
    def chunk(self, document: ParsedDocument) -> list[SemanticChunk]:
        chunks: list[SemanticChunk] = []
        current_section: str | None = None
        for element in document.elements:
            if element.id is None:
                continue
            if element.element_type == DocumentElementType.HEADING:
                current_section = element.text or element.section
            section = element.section or current_section
            content = _chunk_content(element)
            if content is None:
                continue
            chunks.append(
                SemanticChunk(
                    organization_id=document.organization_id,
                    project_id=document.project_id,
                    document_id=document.id,
                    document_element_id=element.id,
                    chunk_type=_chunk_type(element.element_type),
                    page=element.page,
                    section=section,
                    content=content,
                    sequence_index=len(chunks),
                )
            )
        return chunks


def _chunk_content(element: DocumentElement) -> str | None:
    parts = [part for part in [element.caption, element.text] if part]
    if not parts:
        return None
    return "\n".join(parts)


def _chunk_type(element_type: DocumentElementType) -> ChunkType:
    match element_type:
        case DocumentElementType.HEADING:
            return ChunkType.SECTION
        case DocumentElementType.TABLE:
            return ChunkType.TABLE
        case DocumentElementType.FIGURE:
            return ChunkType.FIGURE
        case DocumentElementType.EQUATION:
            return ChunkType.EQUATION_CONTEXT
        case DocumentElementType.REFERENCE:
            return ChunkType.REFERENCE_CONTEXT
        case _:
            return ChunkType.PARAGRAPH
