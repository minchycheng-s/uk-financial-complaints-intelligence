import pandas as pd

from customer_harm.reporting.tableau_pack import (
    build_presentation_tables, validate_pack, workbook_manifest,
)


def _product_rows() -> pd.DataFrame:
    rows = []
    bands = ["priority_review", "review", "monitor", "no_current_signal",
             "insufficient_data", "no_current_signal"]
    for index, band in enumerate(bands):
        rows.append({"firm_key": f"FRN:{index}", "reporting_period": "2025-H2",
            "period_end": "2025-12-31", "is_latest_reporting_period": True,
            "product_group": f"p{index}", "product_group_label": f"Product {index}",
            "display_order": index, "priority_band": band,
            "is_priority_review": band == "priority_review", "is_source_anomaly": index == 0,
            "methodology_id": "v2", "methodology_status": "candidate",
            "display_firm_name": f"Firm {index}", "resolved_frn": str(index),
            "source_reporting_period": "window", "warning_score": 8,
            "triggered_rule_count": 2, "persistent_rule_count": 0,
            "triggered_rule_ids": "A|B", "independent_signal_family_count": 2,
            "triggered_signal_families": "a|b",
            "review_disposition": "source_anomaly_requires_business_review" if index == 0 else None,
            "review_flags": "flag" if index == 0 else None, "review_comment": "reviewed",
            "source_check_status": "confirmed" if index == 0 else None,
            "source_check_resolution": "source anomaly" if index == 0 else None,
            "business_approval_status": "pending", "identity_match_status": "matched"})
    return pd.DataFrame(rows)


def test_presentation_tables_use_latest_period_and_priority_grain() -> None:
    product = _product_rows()
    tables = build_presentation_tables(product, pd.DataFrame())
    assert tables["executive_kpis"].iloc[0].latest_priority_observations == 1
    assert len(tables["priority_review_queue"]) == 1
    assert len(tables["executive_product_snapshot"]) == 6
    assert len(workbook_manifest()["dashboards"]) == 5


def test_pack_validation_reports_release_specific_count_mismatch() -> None:
    tables = build_presentation_tables(_product_rows(), pd.DataFrame())
    issues = validate_pack(tables)
    assert "priority_queue_has_135_rows" in {issue["rule"] for issue in issues}
    assert "period_trend_has_ten_periods" in {issue["rule"] for issue in issues}
