from __future__ import annotations

import pandas as pd

from customer_harm.extraction.validation import build_total_reconciliation


def _metrics(total: float, components: list[tuple[str, float, str]]) -> pd.DataFrame:
    rows = []
    for product, value, status in components + [("grand_total", total, "valid")]:
        rows.append({"reporting_period": "2025-H2", "firm_name": "Example Firm",
                     "canonical_sheet": "opened", "metric_name": "complaints_opened",
                     "source_workbook": "source.xlsx", "source_sheet": "Opened", "source_row": 2,
                     "measurement_unit": "count", "product_group": product,
                     "metric_value": value, "value_status": status})
    return pd.DataFrame(rows)


def test_count_total_matches_sum_of_components() -> None:
    result = build_total_reconciliation(_metrics(12, [
        ("home_finance", 5, "valid"), ("investments", 7, "valid")
    ]))
    assert result.iloc[0].reconciliation_status == "matched"
    assert result.iloc[0].difference == 0


def test_count_total_mismatch_is_visible() -> None:
    result = build_total_reconciliation(_metrics(13, [
        ("home_finance", 5, "valid"), ("investments", 7, "valid")
    ]))
    assert result.iloc[0].reconciliation_status == "mismatch"
    assert result.iloc[0].difference == 1


def test_missing_component_prevents_false_reconciliation() -> None:
    result = build_total_reconciliation(_metrics(5, [
        ("home_finance", 5, "valid"), ("investments", None, "missing")
    ]))
    assert result.iloc[0].reconciliation_status == "not_comparable"
    assert result.iloc[0].reconciliation_reason == "one_or_more_components_missing"
