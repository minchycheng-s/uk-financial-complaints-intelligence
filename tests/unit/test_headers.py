from customer_harm.profiling.headers import (
    FIRM_TABLE_TERMS,
    PRODUCT_REFERENCE_TERMS,
    classify_header_confidence,
    detect_header,
    score_header_candidates,
)


def test_detect_header_uses_structure_and_keywords() -> None:
    matrix = [
        ["FCA complaints publication", None, None],
        [None, None, None],
        ["Firm name", "Reporting period", "Banking and credit cards"],
        ["Example Bank", "2025-H1", 25],
    ]
    index, candidates = detect_header(matrix, expected_terms=FIRM_TABLE_TERMS)
    assert index == 2
    assert candidates[0]["row_number"] == 3
    assert candidates[0]["keyword_matches"] >= 2


def test_candidates_exclude_empty_rows_and_are_ranked() -> None:
    candidates = score_header_candidates(
        [[None], ["Title"], ["Firm name", "Reporting period"]],
        expected_terms=FIRM_TABLE_TERMS,
    )
    assert [candidate["row_number"] for candidate in candidates] == [3, 2]


def test_notes_use_product_reference_header_terms() -> None:
    matrix = [
        [None, None],
        ["Notes on data tables", None],
        ["The figures in this table are reported by firms.", None],
        [None, None],
        ["Product groups reported since 2016", None],
        ["Product group", "Product/service name"],
        ["Banking and credit cards", "Credit cards"],
        [None, "Current accounts"],
    ]

    index, candidates = detect_header(matrix, expected_terms=PRODUCT_REFERENCE_TERMS)

    assert index == 5
    assert candidates[0]["keyword_matches"] == 2


def test_tied_header_candidates_require_manual_review() -> None:
    confidence = classify_header_confidence([
        {"score": 14.5, "keyword_matches": 3},
        {"score": 14.5, "keyword_matches": 3},
    ])

    assert confidence["header_confidence"] == "low"
    assert confidence["score_margin"] == 0.0
    assert confidence["requires_manual_review"] is True
