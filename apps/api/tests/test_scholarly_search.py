from apps.api.app.services.scholarly_search import (
    _format_ieee_reference,
    _parse_crossref_work,
    _parse_openalex_work,
    _reconstruct_abstract,
)


def test_reconstructs_openalex_abstract_in_word_order() -> None:
    abstract = _reconstruct_abstract({"retrieval": [0], "improves": [2], "grounding": [1]})

    assert abstract == "retrieval grounding improves"


def test_parses_openalex_work_into_evidence_and_ieee_reference() -> None:
    reference = _parse_openalex_work(
        {
            "id": "https://openalex.org/W1",
            "display_name": "Retrieval-Augmented Generation",
            "publication_year": 2024,
            "doi": "https://doi.org/10.1000/rag.1",
            "abstract_inverted_index": {
                "Retrieval": [0],
                "grounds": [1],
                "generation": [2],
            },
            "authorships": [
                {"author": {"display_name": "Jane Q. Researcher"}},
                {"author": {"display_name": "Alan Turing"}},
            ],
            "primary_location": {
                "source": {"display_name": "Journal of Research"},
                "landing_page_url": "https://example.test/paper",
            },
            "best_oa_location": {
                "pdf_url": "https://example.test/paper.pdf",
            },
        },
        1,
    )

    assert reference is not None
    assert reference.evidence == "Retrieval grounds generation"
    assert reference.pdf_url == "https://example.test/paper.pdf"
    assert reference.citation == (
        '[1] J. Q. Researcher, and A. Turing, "Retrieval-Augmented Generation," '
        "Journal of Research, 2024, doi: 10.1000/rag.1."
    )


def test_ieee_reference_uses_numbered_format_without_doi() -> None:
    citation = _format_ieee_reference(
        3,
        ["Ada Lovelace"],
        "Analytical Engines",
        "Computing Letters",
        2025,
        "",
    )

    assert citation == '[3] A. Lovelace, "Analytical Engines," Computing Letters, 2025.'


def test_parses_crossref_abstract_and_metadata() -> None:
    reference = _parse_crossref_work(
        {
            "DOI": "10.1000/example",
            "title": ["Grounded Generation"],
            "author": [{"given": "Jane", "family": "Researcher"}],
            "published": {"date-parts": [[2025, 1, 1]]},
            "container-title": ["AI Journal"],
            "abstract": "<jats:p>Retrieved evidence improves factual grounding.</jats:p>",
            "URL": "https://doi.org/10.1000/example",
        },
        1,
    )

    assert reference is not None
    assert reference.evidence == "Retrieved evidence improves factual grounding."
    assert reference.citation == (
        '[1] J. Researcher, "Grounded Generation," AI Journal, 2025, '
        "doi: 10.1000/example."
    )
