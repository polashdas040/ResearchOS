import pytest

from packages.documents.researchos_documents.parser import (
    MalformedDocumentError,
    ScientificPdfParser,
)
from packages.documents.researchos_documents.schema import DocumentElementType


def test_scientific_pdf_parser_preserves_structured_elements_and_page_metadata() -> None:
    parser = ScientificPdfParser()
    content = b"""%PDF-1.4
PAGE 1
TITLE: Attention Models in Longitudinal MRI
ABSTRACT: We evaluate transformer encoders for disease progression.
HEADING: Methods
PARAGRAPH: We trained models on baseline and follow-up scans.
TABLE: Model | Accuracy | AUC
TABLE: CNN | 88.1 | 0.91
TABLE: ViT | 91.5 | 0.94
FIGURE: Figure 2. Transformer encoder architecture.
PAGE 2
HEADING: References
REFERENCE: Doe J. Longitudinal MRI. 2025.
%%EOF
"""

    document = parser.parse(content, filename="paper.pdf", content_type="application/pdf")

    assert document.title == "Attention Models in Longitudinal MRI"
    assert document.page_count == 2
    assert [element.element_type for element in document.elements] == [
        DocumentElementType.TITLE,
        DocumentElementType.ABSTRACT,
        DocumentElementType.HEADING,
        DocumentElementType.PARAGRAPH,
        DocumentElementType.TABLE,
        DocumentElementType.FIGURE,
        DocumentElementType.HEADING,
        DocumentElementType.REFERENCE,
    ]
    table = document.elements[4]
    assert table.page == 1
    assert table.section == "Methods"
    assert table.text == "Model | Accuracy | AUC\nCNN | 88.1 | 0.91\nViT | 91.5 | 0.94"
    figure = document.elements[5]
    assert figure.page == 1
    assert figure.caption == "Figure 2. Transformer encoder architecture."
    reference = document.elements[-1]
    assert reference.page == 2
    assert reference.section == "References"


def test_scientific_pdf_parser_fails_safely_for_malformed_pdf() -> None:
    parser = ScientificPdfParser()

    with pytest.raises(MalformedDocumentError):
        parser.parse(b"not a pdf", filename="broken.pdf", content_type="application/pdf")
