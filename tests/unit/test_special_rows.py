from customer_harm.profiling.pipeline import _potential_special_rows


def test_reference_firm_names_are_not_notes_or_totals() -> None:
    matrix = [
        ["Firm Name", "FRN", "Other Trading Names"],
        ["Source Insurance Limited", 300222, "Source Finance"],
        ["Total Financial Solutions Ltd", 123456, "Example"],
    ]

    totals, notes = _potential_special_rows(matrix, 1, "trading_names")

    assert totals == []
    assert notes == []


def test_metric_total_requires_exact_first_cell_label() -> None:
    matrix = [
        ["Firm Name", "Reporting period", "Grand Total"],
        ["Bank A", "2025-H1", 10],
        ["Grand Total", None, 10],
    ]

    totals, _ = _potential_special_rows(matrix, 1, "opened")

    assert totals == [3]
