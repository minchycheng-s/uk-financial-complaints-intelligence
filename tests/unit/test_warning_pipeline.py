from pathlib import Path

import numpy as np
import pandas as pd

from customer_harm.analytics.warnings import (
    evaluate_warning_rules, load_methodology, prepare_warning_features, validate_warning_outputs,
)


def _methodology() -> dict:
    return {
        "methodology_id": "test_v1", "methodology_status": "analytical_prototype",
        "minimum_peer_size": 1, "minimum_eligible_rules_for_classification": 1,
        "maximum_persistence_bonus": 2,
        "priority_bands": [
            {"minimum_score": 3, "label": "review"},
            {"minimum_score": 1, "label": "monitor"},
            {"minimum_score": 0, "label": "none"},
        ],
        "rules": [{
            "rule_id": "UPHELD_HIGH", "label": "High upheld", "category": "outcome",
            "points": 3, "peer_count_feature": "complaints_upheld_pct_peer_count",
            "conditions": [{"feature": "complaints_upheld_pct_peer_percentile",
                            "operator": ">=", "threshold": 0.9}],
        }],
    }


def _features() -> pd.DataFrame:
    rows = []
    for period, end, upheld in [("2025-H1", "2025-06-30", 0.9),
                                ("2025-H2", "2025-12-31", 0.95)]:
        rows.append({"firm_key": "FRN:1", "reporting_period": period,
            "source_reporting_period": period, "product_group": "home_finance",
            "display_firm_name": "Example", "resolved_frn": "1",
            "observation_start": end, "observation_end": end,
            "complaints_opened_count": 10, "complaints_upheld_pct": upheld,
            "closed_within_3_days_pct": 0.2,
            "closed_after_3_days_within_8_weeks_pct": 0.6,
            "context_provision_rate": np.nan, "context_intermediation_rate": np.nan,
            "complaints_upheld_pct_peer_percentile": 1.0})
    return pd.DataFrame(rows)


def test_repository_methodology_is_valid_and_versioned() -> None:
    methodology = load_methodology(Path("config/warning_methodology.json"))
    assert methodology["methodology_id"] == "fca_complaint_early_warning_v1"
    assert methodology["methodology_status"] == "analytical_prototype"
    assert len(methodology["rules"]) == 8


def test_trigger_persistence_and_score_are_explainable() -> None:
    indicators, summary = evaluate_warning_rules(_features(), _methodology())
    assert indicators.triggered.tolist() == [True, True]
    assert indicators.persistent_trigger.tolist() == [False, True]
    assert summary.warning_score.tolist() == [3, 4]
    assert set(summary.priority_band) == {"review"}
    assert validate_warning_outputs(indicators, summary, 2, 1) == []


def test_missing_rule_feature_is_ineligible_not_zero_risk() -> None:
    features = _features()
    features["complaints_upheld_pct_peer_percentile"] = np.nan
    indicators, summary = evaluate_warning_rules(features, _methodology())
    assert not indicators.eligible.any()
    assert not indicators.triggered.any()
    assert set(summary.priority_band) == {"insufficient_data"}


def test_invalid_negative_derived_closure_rate_becomes_missing() -> None:
    features = _features().iloc[[0]].copy()
    features["closed_within_3_days_pct"] = 0.8
    features["closed_after_3_days_within_8_weeks_pct"] = 0.4
    prepared = prepare_warning_features(features)
    assert pd.isna(prepared.iloc[0].closed_over_8_weeks_pct)


def test_family_cap_prevents_correlated_rules_from_double_counting() -> None:
    methodology = _methodology()
    methodology["family_point_caps"] = {"outcome": 2}
    _, summary = evaluate_warning_rules(_features(), methodology)
    assert summary.uncapped_base_warning_score.tolist() == [3, 3]
    assert summary.base_warning_score.tolist() == [2, 2]
    assert summary.point_cap_reduction.tolist() == [1, 1]
