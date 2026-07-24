"""Build reproducible evidence for management actions ACT-002 to ACT-005."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

KEYS = ["firm_key", "product_group", "reporting_period"]


def build_action_evidence(
    observations_path: Path,
    rules_path: Path,
    output_dir: Path,
    latest_period: str = "2025-H2",
) -> dict[str, Any]:
    """Build priority, rule-driver, Consumer Credit and coverage work queues."""
    for path in [observations_path, rules_path]:
        if not path.exists():
            raise FileNotFoundError(f"Action-evidence input not found: {path}")
    observations = pd.read_csv(observations_path, low_memory=False)
    rules = pd.read_csv(rules_path, low_memory=False)
    latest = observations.loc[
        observations["reporting_period"].eq(latest_period)
    ].copy()
    latest_rules = rules.loc[rules["reporting_period"].eq(latest_period)].copy()

    priority = latest.loc[latest["priority_band"].eq("priority_review")].copy()
    priority_columns = [
        "firm_key",
        "display_firm_name",
        "product_group",
        "product_group_label",
        "reporting_period",
        "warning_score",
        "coverage_status",
        "triggered_rule_count",
        "persistent_rule_count",
        "triggered_signal_families",
        "triggered_rule_ids",
        "review_flags",
        "review_disposition",
        "review_comment",
    ]
    priority_queue = priority[priority_columns].sort_values(
        ["warning_score", "display_firm_name"], ascending=[False, True]
    )

    triggered = latest_rules.loc[latest_rules["triggered"]].copy()
    rule_drivers = triggered.groupby(
        ["rule_id", "rule_label", "rule_category", "score_family"], as_index=False
    ).agg(
        triggered_observations=("firm_key", "size"),
        persistent_triggers=("persistent_trigger", "sum"),
        product_groups=("product_group", "nunique"),
    )
    rule_drivers["persistent_share"] = (
        rule_drivers["persistent_triggers"]
        / rule_drivers["triggered_observations"]
    )
    rule_drivers = rule_drivers.sort_values(
        ["triggered_observations", "persistent_triggers"], ascending=False
    )

    consumer = latest.loc[
        latest["product_group"].eq("consumer_credit")
        & latest["priority_band"].isin(["monitor", "review"])
    ].copy()
    consumer_rule_ids = triggered.loc[
        triggered["product_group"].eq("consumer_credit")
    ].groupby(KEYS)["rule_id"].agg(lambda values: "|".join(sorted(values)))
    consumer = consumer.merge(
        consumer_rule_ids.rename("triggered_rule_ids_rebuilt"),
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    consumer_columns = [
        "firm_key",
        "display_firm_name",
        "reporting_period",
        "priority_band",
        "complaints_opened_count",
        "previous_complaints_opened_count",
        "pct_change_complaints_opened_count",
        "complaints_upheld_pct",
        "warning_score",
        "coverage_status",
        "triggered_rule_ids_rebuilt",
    ]
    consumer_queue = consumer.sort_values(
        ["priority_band_sort_order", "warning_score", "complaints_opened_count"],
        ascending=[True, False, False],
    )[consumer_columns]

    insufficient = latest.loc[
        latest["priority_band"].eq("insufficient_data")
    ].copy()
    insufficient_rules = latest_rules.merge(
        insufficient[KEYS], on=KEYS, validate="many_to_one"
    )
    ineligible = insufficient_rules.loc[~insufficient_rules["eligible"]].copy()
    reason_counts = ineligible.pivot_table(
        index=KEYS,
        columns="eligibility_reason",
        values="rule_id",
        aggfunc="count",
        fill_value=0,
    ).reset_index()
    family_gaps = ineligible.groupby(KEYS)["score_family"].agg(
        lambda values: "|".join(sorted(set(values)))
    ).rename("ineligible_signal_families")
    insufficient_queue = insufficient.merge(
        reason_counts, on=KEYS, how="left", validate="one_to_one"
    ).merge(
        family_gaps, on=KEYS, how="left", validate="one_to_one"
    )
    for column in ["missing_required_feature", "peer_group_below_minimum"]:
        if column not in insufficient_queue:
            insufficient_queue[column] = 0
        insufficient_queue[column] = (
            insufficient_queue[column].fillna(0).astype(int)
        )
    insufficient_queue["recommended_treatment"] = "restore_or_source_missing_features"
    insufficient_queue.loc[
        insufficient_queue["peer_group_below_minimum"].gt(0),
        "recommended_treatment",
    ] = "review_peer_group_minimum_and_do_not_classify"
    insufficient_columns = [
        "firm_key",
        "display_firm_name",
        "product_group",
        "product_group_label",
        "reporting_period",
        "eligible_rule_count",
        "coverage_status",
        "missing_required_feature",
        "peer_group_below_minimum",
        "ineligible_signal_families",
        "recommended_treatment",
    ]
    insufficient_queue = insufficient_queue[insufficient_columns].sort_values(
        ["product_group_label", "display_firm_name"]
    )

    coverage_summary = insufficient_queue.groupby(
        "product_group_label", as_index=False
    ).agg(
        insufficient_observations=("firm_key", "size"),
        zero_eligible_rules=("eligible_rule_count", lambda values: int((values == 0).sum())),
        one_or_two_eligible_rules=(
            "eligible_rule_count",
            lambda values: int(values.isin([1, 2]).sum()),
        ),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    priority_queue.to_csv(output_dir / "latest_priority_queue.csv", index=False)
    rule_drivers.to_csv(output_dir / "latest_rule_drivers.csv", index=False)
    consumer_queue.to_csv(
        output_dir / "consumer_credit_monitoring_queue.csv", index=False
    )
    insufficient_queue.to_csv(
        output_dir / "insufficient_evidence_queue.csv", index=False
    )
    coverage_summary.to_csv(
        output_dir / "insufficient_evidence_summary.csv", index=False
    )

    summary = {
        "latest_period": latest_period,
        "latest_priority_observations": int(len(priority_queue)),
        "latest_triggered_rule_rows": int(len(triggered)),
        "consumer_credit_monitor_and_review_observations": int(len(consumer_queue)),
        "consumer_credit_monitor_observations": int(
            (consumer_queue["priority_band"] == "monitor").sum()
        ),
        "insufficient_evidence_observations": int(len(insufficient_queue)),
        "zero_eligible_rule_observations": int(
            (insufficient_queue["eligible_rule_count"] == 0).sum()
        ),
        "one_or_two_eligible_rule_observations": int(
            insufficient_queue["eligible_rule_count"].isin([1, 2]).sum()
        ),
        "business_approval_status": "pending_business_review",
    }
    (output_dir / "action_evidence_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
