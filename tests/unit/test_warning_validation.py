import copy

import pandas as pd

from customer_harm.analytics.validation import build_scenarios, select_review_sample


def _methodology() -> dict:
    return {
        "methodology_id": "test", "methodology_status": "analytical_prototype",
        "minimum_peer_size": 20, "minimum_eligible_rules_for_classification": 3,
        "maximum_persistence_bonus": 2,
        "priority_bands": [
            {"minimum_score": 6, "label": "priority_review"},
            {"minimum_score": 3, "label": "review"},
            {"minimum_score": 1, "label": "monitor"},
            {"minimum_score": 0, "label": "no_current_signal"},
        ],
        "rules": [{"rule_id": "UPHELD_PEER_HIGH", "label": "High upheld",
                   "category": "outcome", "points": 3,
                   "peer_count_feature": "complaints_upheld_pct_peer_count",
                   "conditions": [{"feature": "complaints_upheld_pct_peer_percentile",
                                   "operator": ">=", "threshold": 0.9}]},
                  {"rule_id": "UPHELD_DETERIORATION", "label": "Upheld change",
                   "category": "change", "points": 2,
                   "peer_count_feature": "complaints_upheld_pct_peer_count",
                   "conditions": [{"feature": "change_complaints_upheld_pct",
                                   "operator": ">=", "threshold": 0.05}]}],
    }


def test_scenarios_are_one_at_a_time_and_do_not_mutate_baseline() -> None:
    baseline = _methodology()
    original = copy.deepcopy(baseline)
    scenarios = build_scenarios(baseline)
    assert len(scenarios) == 15
    assert scenarios[0][0] == "baseline"
    assert baseline == original
    peer_95 = next(method for scenario, _, method in scenarios if scenario == "peer_high_95")
    threshold = peer_95["rules"][0]["conditions"][0]["threshold"]
    assert threshold == 0.95


def test_review_sample_covers_each_band_and_stays_pending() -> None:
    bands = ["priority_review", "review", "monitor", "no_current_signal", "insufficient_data"]
    summary_rows, feature_rows, indicator_rows = [], [], []
    for index, band in enumerate(bands):
        common = {"firm_key": f"FRN:{index}", "reporting_period": "2025-H2",
                  "source_reporting_period": "2025-07-01 to 2025-12-31",
                  "product_group": "home_finance"}
        summary_rows.append({**common, "display_firm_name": f"Firm {index}", "resolved_frn": str(index),
                             "observation_start": "2025-07-01", "observation_end": "2025-12-31",
                             "eligible_rule_count": 4 if band != "insufficient_data" else 1,
                             "triggered_rule_count": 1 if band in {"priority_review", "review", "monitor"} else 0,
                             "persistent_rule_count": 0, "base_warning_score": index,
                             "persistence_bonus": 0, "warning_score": 10 - index,
                             "coverage_status": "broad", "priority_band": band,
                             "triggered_rule_ids": "RULE"})
        feature_rows.append({**common, "complaints_opened_count": 10,
            "complaints_upheld_pct": 0.2, "closed_within_8_weeks_pct": 0.9,
            "context_provision_rate": 2.0, "context_intermediation_rate": None,
            "pct_change_complaints_opened_count": 0.1, "change_complaints_upheld_pct": 0.01,
            "pct_change_context_provision_rate": 0.1,
            "pct_change_context_intermediation_rate": None})
        indicator_rows.append({**common, "rule_id": "RULE", "triggered": band == "priority_review"})
    sample, drilldown = select_review_sample(pd.DataFrame(summary_rows),
                                             pd.DataFrame(indicator_rows),
                                             pd.DataFrame(feature_rows), per_band=1)
    assert set(sample.priority_band) == set(bands)
    assert sample.review_status.eq("pending_case_review").all()
    assert len(drilldown) == 5
