import pandas as pd

from customer_harm.analytics.tables import build_analysis_tables, firm_key, validate_analysis_tables


def _metric_rows() -> pd.DataFrame:
    common = {
        "reporting_period": "2025-H2", "source_reporting_period": "2025-07-01 to 2025-12-31",
        "firm_name": "Example Firm Ltd", "frn": "", "resolved_frn": "123456",
        "raw_firm_group": "Example Group", "joint_reporting_flag": "no",
        "canonical_sheet": "opened", "metric_name": "complaints_opened",
        "measurement_unit": "count", "measurement_basis": "", "value_status": "valid",
        "value_reason": "", "raw_header": "Home finance", "source_workbook": "source.xlsx",
        "source_sheet": "Opened", "match_status": "matched",
        "match_method": "exact_name_same_period", "match_confidence": "high",
    }
    return pd.DataFrame([
        {**common, "product_group": "home_finance", "metric_value": 10, "raw_value": "10",
         "source_row": 2, "source_column": 5},
        {**common, "product_group": "grand_total", "metric_value": 10, "raw_value": "10",
         "source_row": 2, "source_column": 6, "raw_header": "Grand Total"},
    ])


def test_resolved_and_unresolved_firm_keys_are_stable_and_distinct() -> None:
    assert firm_key("123456", "Any Name") == "FRN:123456"
    assert firm_key("", " Example  Firm ") == firm_key("", "example firm")
    assert firm_key("", "Example Firm") != firm_key("", "Other Firm")


def test_analysis_tables_preserve_rows_and_mark_grand_total() -> None:
    tables = build_analysis_tables(_metric_rows(), pd.DataFrame(columns=[
        "reporting_period", "source_workbook", "source_sheet", "source_row", "source_column",
        "quality_flag", "quality_review_status", "reviewer", "reviewed_at", "reviewer_comment"
    ]))
    fact = tables["fact_firm_complaints"]
    assert len(fact) == 2
    assert fact.fact_id.is_unique
    assert fact.loc[fact.product_group.eq("grand_total"), "is_product_level"].eq(False).all()
    assert validate_analysis_tables(tables, 2) == []


def test_confirmed_quality_decision_is_attached_by_source_cell() -> None:
    metrics = _metric_rows().iloc[[0]].copy()
    metrics.loc[:, "measurement_unit"] = "percentage"
    metrics.loc[:, "metric_value"] = 2.0
    quality = pd.DataFrame([{
        "reporting_period": "2025-H2", "source_workbook": "source.xlsx",
        "source_sheet": "Opened", "source_row": "2", "source_column": "5",
        "quality_flag": "percentage_above_expected_range",
        "quality_review_status": "source_value_confirmed", "reviewer": "Analyst",
        "reviewed_at": "2026-07-18", "reviewer_comment": "Confirmed in workbook",
    }])
    fact = build_analysis_tables(metrics, quality)["fact_firm_complaints"].iloc[0]
    assert fact.quality_review_status == "source_value_confirmed"
    assert bool(fact.is_analysis_ready_value)
