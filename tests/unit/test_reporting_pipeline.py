import pandas as pd

from customer_harm.reporting.pipeline import (
    OBSERVATION_KEYS, build_firm_period_dashboard, data_dictionary, validate_reporting,
)


def test_firm_period_dashboard_preaggregates_product_bands_safely() -> None:
    rows = []
    for product, band, score in [("banking", "priority_review", 9),
                                 ("insurance", "monitor", 2)]:
        rows.append({"firm_key": "FRN:1", "reporting_period": "2025-H2",
            "display_firm_name": "Example", "resolved_frn": "1", "year": 2025,
            "half": 2, "period_start": "2025-07-01", "period_end": "2025-12-31",
            "product_group": product, "product_group_label": product.title(),
            "has_current_signal": True, "warning_score": score,
            "triggered_rule_count": 2, "persistent_rule_count": 1,
            "is_source_anomaly": False, "is_latest_reporting_period": True,
            "priority_band": band, "is_priority_review": band == "priority_review"})
    result = build_firm_period_dashboard(pd.DataFrame(rows))
    assert len(result) == 1
    assert result.iloc[0].priority_review_product_count == 1
    assert result.iloc[0].monitor_product_count == 1
    assert result.iloc[0].maximum_warning_score == 9


def test_reporting_validation_requires_complete_priority_reviews() -> None:
    keys = dict(zip(OBSERVATION_KEYS, ["FRN:1", "2025-H2", "window", "banking"]))
    product = pd.DataFrame([{**keys, "is_priority_review": True,
        "review_disposition": None, "is_source_anomaly": True,
        "methodology_id": "fca_complaint_early_warning_v2_candidate"}])
    rule = pd.DataFrame([{**keys, "rule_id": "R1"}])
    tables = {"dashboard_firm_product_period": product,
              "dashboard_warning_rule_detail": rule,
              "dashboard_firm_period": pd.DataFrame([{"firm_key": "FRN:1",
                                                       "reporting_period": "2025-H2"}])}
    issues = validate_reporting(tables, feature_rows=1, rule_count=1)
    assert "all_priority_cases_reviewed" in {issue["rule"] for issue in issues}
    assert len(data_dictionary()) == 5
