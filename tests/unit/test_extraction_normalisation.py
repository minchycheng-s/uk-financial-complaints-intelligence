from customer_harm.extraction.normalisation import (
    consumer_credit_measure,
    context_basis,
    normalise_metric_value,
    reviewed_metric_override,
)


def test_blank_text_is_missing_not_invalid() -> None:
    assert normalise_metric_value(" ") == (None, "missing", "blank_source_cell")


def test_excel_error_remains_distinct_from_zero() -> None:
    assert normalise_metric_value("#N/A") == (None, "invalid", "excel_error")


def test_context_basis_uses_explicit_qualifier() -> None:
    assert context_basis("Home finance (per 1,000 sales)", "context_intermediation") == "per_1000_sales"


def test_short_context_header_uses_reviewed_table_role() -> None:
    assert context_basis("Home finance", "context_provision") == "per_1000_accounts_or_policies_provided"


def test_consumer_credit_upheld_count_and_percentage_are_distinct() -> None:
    assert consumer_credit_measure("Complaints upheld by firm", "2022-H2") == (
        "complaints_upheld", "count"
    )
    assert consumer_credit_measure("Complaints upheld by firm", "2025-H2") == (
        "complaints_upheld", "percentage"
    )


def test_reviewed_na_total_is_not_calculable_not_zero() -> None:
    assert reviewed_metric_override(
        "#N/A", "2025-H2", "percentage_upheld", "grand_total"
    ) == ("not_calculable", "no_component_values")
    assert reviewed_metric_override(
        "#N/A", "2024-H2", "percentage_upheld", "grand_total"
    ) is None
