from __future__ import annotations

from pathlib import Path

import pandas as pd

from customer_harm.governance.action_evidence import build_action_evidence


def test_builds_distinct_management_work_queues(tmp_path: Path) -> None:
    observations = pd.DataFrame(
        [
            {
                "firm_key": "F1",
                "product_group": "consumer_credit",
                "reporting_period": "2025-H2",
                "display_firm_name": "Firm 1",
                "product_group_label": "Consumer Credit",
                "priority_band": "monitor",
                "priority_band_sort_order": 3,
                "warning_score": 2,
                "coverage_status": "partial",
                "complaints_opened_count": 200,
                "previous_complaints_opened_count": 100,
                "pct_change_complaints_opened_count": 1.0,
                "complaints_upheld_pct": 0.4,
                "eligible_rule_count": 3,
                "triggered_rule_count": 1,
                "persistent_rule_count": 0,
                "triggered_signal_families": "volume_pressure",
                "triggered_rule_ids": "OPENED_EXCEPTIONAL_GROWTH",
                "review_flags": "",
                "review_disposition": "",
                "review_comment": "",
            },
            {
                "firm_key": "F2",
                "product_group": "home_finance",
                "reporting_period": "2025-H2",
                "display_firm_name": "Firm 2",
                "product_group_label": "Home Finance",
                "priority_band": "insufficient_data",
                "priority_band_sort_order": 5,
                "warning_score": 0,
                "coverage_status": "limited",
                "complaints_opened_count": 10,
                "previous_complaints_opened_count": None,
                "pct_change_complaints_opened_count": None,
                "complaints_upheld_pct": None,
                "eligible_rule_count": 0,
                "triggered_rule_count": 0,
                "persistent_rule_count": 0,
                "triggered_signal_families": "",
                "triggered_rule_ids": "",
                "review_flags": "",
                "review_disposition": "",
                "review_comment": "",
            },
        ]
    )
    rules = pd.DataFrame(
        [
            {
                "firm_key": "F1",
                "product_group": "consumer_credit",
                "reporting_period": "2025-H2",
                "rule_id": "OPENED_EXCEPTIONAL_GROWTH",
                "rule_label": "Opened doubled",
                "rule_category": "growth",
                "score_family": "volume_pressure",
                "triggered": True,
                "persistent_trigger": False,
                "eligible": True,
                "eligibility_reason": "conditions_met",
            },
            {
                "firm_key": "F2",
                "product_group": "home_finance",
                "reporting_period": "2025-H2",
                "rule_id": "UPHELD_PEER_HIGH",
                "rule_label": "High upheld",
                "rule_category": "peer",
                "score_family": "complaint_outcome",
                "triggered": False,
                "persistent_trigger": False,
                "eligible": False,
                "eligibility_reason": "missing_required_feature",
            },
        ]
    )
    observation_path = tmp_path / "observations.csv"
    rule_path = tmp_path / "rules.csv"
    output_dir = tmp_path / "outputs"
    observations.to_csv(observation_path, index=False)
    rules.to_csv(rule_path, index=False)

    result = build_action_evidence(
        observation_path, rule_path, output_dir, "2025-H2"
    )

    assert result["consumer_credit_monitor_observations"] == 1
    assert result["insufficient_evidence_observations"] == 1
    assert (output_dir / "latest_rule_drivers.csv").exists()
    queue = pd.read_csv(output_dir / "insufficient_evidence_queue.csv")
    assert queue.loc[0, "recommended_treatment"] == "restore_or_source_missing_features"
