import pandas as pd

from customer_harm.analytics.priority_review import build_priority_reviews


def test_priority_review_flags_source_checks_and_boundary_cases() -> None:
    keys = {"firm_key": "FRN:1", "reporting_period": "2025-H2",
            "source_reporting_period": "window", "product_group": "investments"}
    summary = pd.DataFrame([{**keys, "priority_band": "priority_review",
        "display_firm_name": "Example", "warning_score": 8, "triggered_rule_count": 2}])
    indicators = pd.DataFrame([
        {**keys, "triggered": True, "score_family": "context_rate", "rule_id": "A",
         "persistent_trigger": False},
        {**keys, "triggered": True, "score_family": "timeliness", "rule_id": "B",
         "persistent_trigger": False},
    ])
    features = pd.DataFrame([{**keys, "complaints_opened_count": 25,
        "complaints_closed_count": 20, "complaints_upheld_pct": .5,
        "closed_within_8_weeks_pct": .8, "context_provision_rate": 2,
        "context_intermediation_rate": None, "identity_match_status": "matched"}])
    previous = pd.DataFrame(columns=list(keys) + ["review_outcome", "review_comment"])
    result = build_priority_reviews(summary, indicators, features, previous, "Analyst", "2026-01-01")
    assert result.iloc[0].review_disposition == "source_check_required_before_reliance"
    assert "low_closed_denominator" in result.iloc[0].review_flags
    assert result.iloc[0].business_approval_status == "pending_business_review"
