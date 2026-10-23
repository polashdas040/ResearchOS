from apps.api.app.services.document_context import (
    _build_ieee_reference,
    _select_relevant_pages,
)


def test_select_relevant_pages_prioritizes_query_matches_and_keeps_page_labels() -> None:
    pages = [
        (1, "Background and motivation for the study."),
        (2, "The method uses a convolutional baseline."),
        (3, "Results show the transformer reached AUC 0.94 on the held-out cohort."),
    ]

    selected = _select_relevant_pages(pages, "Write the Results section about transformer AUC")

    assert selected[0] == (
        3,
        "Results show the transformer reached AUC 0.94 on the held-out cohort.",
    )


def test_select_relevant_pages_limits_excerpt_size() -> None:
    selected = _select_relevant_pages([(7, "result " * 500)], "result", excerpt_size=100)

    assert selected[0][0] == 7
    assert len(selected[0][1]) == 100


def test_ieee_reference_has_clear_fallback_when_pdf_metadata_is_missing() -> None:
    reference = _build_ieee_reference(
        2,
        "AI_Agent_Review_2023.pdf",
        "application/pdf",
        b"not-a-real-pdf",
    )

    assert reference == '[2] "AI Agent Review 2023," unpublished manuscript, n.d.'
