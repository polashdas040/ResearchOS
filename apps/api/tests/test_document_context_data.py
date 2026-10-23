from apps.api.app.services.document_context import _extract_pages, _select_relevant_pages


def test_csv_extraction_preserves_header_and_retrieves_relevant_rows() -> None:
    rows = ["subject,modality,score"]
    rows.extend(f"S-{index:03d},MRI,{index / 100:.2f}" for index in range(45))
    rows.append("S-999,PET,0.97")

    sections = _extract_pages("subjects.csv", "text/csv", "\n".join(rows).encode())
    selected = _select_relevant_pages(sections, "PET subject S-999", limit=1)

    assert len(sections) == 2
    assert selected[0][0] == 2
    assert selected[0][1].startswith("subject,modality,score")
    assert "S-999,PET,0.97" in selected[0][1]


def test_json_extraction_returns_searchable_structured_content() -> None:
    content = b'{"study": "ADNI", "metrics": {"auc": 0.94}, "model": "ViT"}'

    sections = _extract_pages("results.json", "application/json", content)
    selected = _select_relevant_pages(sections, "ADNI AUC ViT", limit=1)

    assert len(sections) == 1
    assert '"study": "ADNI"' in selected[0][1]
    assert '"auc": 0.94' in selected[0][1]
