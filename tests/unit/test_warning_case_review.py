import pandas as pd
import pytest

from customer_harm.analytics.case_review import merge_case_reviews


def _sample() -> pd.DataFrame:
    return pd.DataFrame([{"firm_key": "FRN:1", "reporting_period": "2025-H2",
        "source_reporting_period": "2025-07-01 to 2025-12-31", "product_group": "home_finance",
        "priority_band": "review", "review_status": "pending_case_review", "reviewer": "",
        "reviewed_at": "", "review_comment": ""}])


def test_complete_valid_decision_is_merged() -> None:
    decision = pd.DataFrame([{"firm_key": "FRN:1", "reporting_period": "2025-H2",
        "source_reporting_period": "2025-07-01 to 2025-12-31", "product_group": "home_finance",
        "review_outcome": "useful_monitoring_case", "reviewer": "Analyst",
        "reviewed_at": "2026-07-20", "review_comment": "Reviewed"}])
    result = merge_case_reviews(_sample(), decision)
    assert result.iloc[0].review_outcome == "useful_monitoring_case"
    assert result.iloc[0].reviewer == "Analyst"


def test_incomplete_decision_coverage_is_rejected() -> None:
    decisions = pd.DataFrame(columns=["firm_key", "reporting_period", "source_reporting_period",
        "product_group", "review_outcome", "reviewer", "reviewed_at", "review_comment"])
    with pytest.raises(ValueError, match="cover the sampled case keys exactly"):
        merge_case_reviews(_sample(), decisions)
