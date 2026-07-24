"""Build evidence packs for persistent firm-product warning investigations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

CASE_KEYS = ["firm_key", "product_group"]
DECISION_COLUMNS = [
    "case_id",
    "firm_key",
    "product_group",
    "display_firm_name",
    "review_status",
    "root_cause_category",
    "management_decision",
    "decision_rationale",
    "action_required",
    "owner",
    "due_date",
    "evidence_reference",
    "reviewer",
    "reviewed_at",
    "business_approval_status",
]
REVIEW_STATUSES = {"pending", "in_progress", "completed", "blocked"}
ROOT_CAUSES = {
    "",
    "operational_process",
    "business_mix",
    "reporting_practice",
    "source_definition",
    "data_quality",
    "multiple_factors",
    "not_determined",
}
MANAGEMENT_DECISIONS = {
    "",
    "continue_monitoring",
    "remediation_required",
    "methodology_treatment_required",
    "no_further_action",
    "escalate_for_business_review",
}


def select_persistent_cases(
    observations: pd.DataFrame, latest_period: str, case_count: int = 6
) -> pd.DataFrame:
    """Select latest priority cases with the strongest priority persistence."""
    required = {
        *CASE_KEYS,
        "reporting_period",
        "display_firm_name",
        "product_group_label",
        "priority_band",
        "warning_score",
        "persistent_rule_count",
        "triggered_rule_ids",
        "review_disposition",
        "coverage_status",
    }
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"Observation table lacks columns: {sorted(missing)}")

    priority = observations.loc[
        observations["priority_band"].eq("priority_review")
    ].copy()
    history = priority.groupby(CASE_KEYS, as_index=False).agg(
        priority_periods=("reporting_period", "nunique"),
        first_priority_period=("reporting_period", "min"),
        last_priority_period=("reporting_period", "max"),
        maximum_warning_score=("warning_score", "max"),
        periods_with_persistent_rules=(
            "persistent_rule_count",
            lambda values: int((values > 0).sum()),
        ),
    )
    latest = priority.loc[priority["reporting_period"].eq(latest_period)].copy()
    latest = latest.merge(history, on=CASE_KEYS, validate="one_to_one")
    latest = latest.sort_values(
        ["priority_periods", "warning_score", "display_firm_name"],
        ascending=[False, False, True],
    ).head(case_count)
    if len(latest) != case_count:
        raise ValueError(
            f"Expected {case_count} latest persistent cases; found {len(latest)}"
        )

    latest = latest.reset_index(drop=True)
    latest.insert(
        0,
        "case_id",
        [f"PCR-{number:03d}" for number in range(1, len(latest) + 1)],
    )
    return latest[
        [
            "case_id",
            *CASE_KEYS,
            "display_firm_name",
            "product_group_label",
            "priority_periods",
            "first_priority_period",
            "last_priority_period",
            "periods_with_persistent_rules",
            "maximum_warning_score",
            "warning_score",
            "triggered_rule_ids",
            "review_disposition",
            "coverage_status",
        ]
    ].rename(columns={"warning_score": "latest_warning_score"})


def validate_case_decisions(path: Path, expected_cases: pd.DataFrame) -> pd.DataFrame:
    """Validate the durable human-decision file without inventing conclusions."""
    if not path.exists():
        raise FileNotFoundError(f"Persistent-case decision register not found: {path}")
    decisions = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(DECISION_COLUMNS) - set(decisions.columns)
    if missing:
        raise ValueError(f"Decision register lacks columns: {sorted(missing)}")
    decisions = decisions[DECISION_COLUMNS].copy()
    if decisions["case_id"].duplicated().any():
        raise ValueError("Decision register contains duplicate case IDs")
    if set(decisions["case_id"]) != set(expected_cases["case_id"]):
        raise ValueError("Decision register does not match the generated case scope")

    for row in decisions.to_dict("records"):
        if row["review_status"] not in REVIEW_STATUSES:
            raise ValueError(f"{row['case_id']}: invalid review_status")
        if row["root_cause_category"] not in ROOT_CAUSES:
            raise ValueError(f"{row['case_id']}: invalid root_cause_category")
        if row["management_decision"] not in MANAGEMENT_DECISIONS:
            raise ValueError(f"{row['case_id']}: invalid management_decision")
        if row["review_status"] == "completed":
            required = [
                "root_cause_category",
                "management_decision",
                "decision_rationale",
                "owner",
                "evidence_reference",
                "reviewer",
                "reviewed_at",
            ]
            absent = [field for field in required if not row[field].strip()]
            if absent:
                raise ValueError(
                    f"{row['case_id']}: completed review requires {absent}"
                )
    return decisions


def _decision_template(cases: pd.DataFrame) -> pd.DataFrame:
    template = cases[
        ["case_id", "firm_key", "product_group", "display_firm_name"]
    ].copy()
    template["review_status"] = "pending"
    template["root_cause_category"] = ""
    template["management_decision"] = ""
    template["decision_rationale"] = ""
    template["action_required"] = ""
    template["owner"] = ""
    template["due_date"] = ""
    template["evidence_reference"] = template["case_id"].map(
        lambda case_id: (
            "data/processed/governance/persistent_cases/"
            f"persistent_case_period_evidence.csv#{case_id}"
        )
    )
    template["reviewer"] = ""
    template["reviewed_at"] = ""
    template["business_approval_status"] = "pending_business_review"
    return template[DECISION_COLUMNS]


def build_persistent_case_pack(
    observations_path: Path,
    rules_path: Path,
    output_dir: Path,
    decisions_path: Path,
    report_path: Path,
    latest_period: str = "2025-H2",
    case_count: int = 6,
) -> dict[str, Any]:
    """Create case, period and rule evidence without overwriting human decisions."""
    for path in [observations_path, rules_path]:
        if not path.exists():
            raise FileNotFoundError(f"Persistent-case input not found: {path}")
    observations = pd.read_csv(observations_path, low_memory=False)
    rules = pd.read_csv(rules_path, low_memory=False)
    cases = select_persistent_cases(observations, latest_period, case_count)

    scoped = observations.merge(
        cases[["case_id", *CASE_KEYS]], on=CASE_KEYS, validate="many_to_one"
    )
    period_columns = [
        "case_id",
        "firm_key",
        "display_firm_name",
        "product_group",
        "product_group_label",
        "reporting_period",
        "source_reporting_period",
        "complaints_opened_count",
        "pct_change_complaints_opened_count",
        "complaints_upheld_pct",
        "closed_within_3_days_pct",
        "closed_after_3_days_within_8_weeks_pct",
        "context_provision_rate",
        "context_intermediation_rate",
        "warning_score",
        "coverage_status",
        "priority_band",
        "triggered_rule_count",
        "persistent_rule_count",
        "triggered_rule_ids",
        "persistent_trigger_ids",
        "review_disposition",
        "review_flags",
        "source_check_status",
        "source_check_resolution",
    ]
    period_evidence = scoped[period_columns].sort_values(
        ["case_id", "reporting_period"]
    )

    rule_evidence = rules.loc[rules["triggered"]].merge(
        cases[["case_id", *CASE_KEYS]], on=CASE_KEYS, validate="many_to_one"
    )
    rule_columns = [
        "case_id",
        "firm_key",
        "product_group",
        "reporting_period",
        "rule_id",
        "rule_label",
        "rule_category",
        "score_family",
        "base_points",
        "previous_triggered",
        "persistent_trigger",
        "peer_count",
        "condition_evidence",
    ]
    rule_evidence = rule_evidence[rule_columns].sort_values(
        ["case_id", "reporting_period", "rule_id"]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    cases.to_csv(output_dir / "persistent_case_summary.csv", index=False)
    period_evidence.to_csv(
        output_dir / "persistent_case_period_evidence.csv", index=False
    )
    rule_evidence.to_csv(
        output_dir / "persistent_case_rule_evidence.csv", index=False
    )

    if not decisions_path.exists():
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        _decision_template(cases).to_csv(decisions_path, index=False)
    decisions = validate_case_decisions(decisions_path, cases)

    joined = cases.merge(
        decisions[["case_id", "review_status", "owner", "management_decision"]],
        on="case_id",
        validate="one_to_one",
    )
    lines = [
        "# Persistent-case investigation status",
        "",
        f"Scope: the {case_count} strongest persistent cases that remain in "
        f"`priority_review` in {latest_period}.",
        "",
        "These are analytical investigation cases, not findings of misconduct "
        "or customer harm.",
        "",
        "| Case | Firm and product | Priority periods | Latest score | Status | Owner |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in joined.to_dict("records"):
        lines.append(
            f"| {row['case_id']} | {row['display_firm_name']} — "
            f"{row['product_group_label']} | {row['priority_periods']} | "
            f"{int(row['latest_warning_score'])} | {row['review_status']} | "
            f"{row['owner'] or 'Unassigned'} |"
        )
    lines += [
        "",
        "Preliminary analytical assessments are recorded, but internal business "
        "evidence, named ownership and independent review are still required "
        "before any case can be completed.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = {
        "latest_period": latest_period,
        "case_count": int(len(cases)),
        "period_evidence_rows": int(len(period_evidence)),
        "triggered_rule_evidence_rows": int(len(rule_evidence)),
        "review_status_counts": decisions["review_status"].value_counts().to_dict(),
        "completed_reviews": int((decisions["review_status"] == "completed").sum()),
        "business_approval_status": "pending_business_review",
    }
    (output_dir / "persistent_case_pack_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
