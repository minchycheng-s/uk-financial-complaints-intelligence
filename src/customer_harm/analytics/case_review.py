"""Validate and summarise manual warning-case review decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

CASE_KEYS = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
ALLOWED_OUTCOMES = {
    "coherent_priority_case", "useful_monitoring_case", "likely_false_positive",
    "no_material_signal_confirmed", "potential_false_negative", "insufficient_context",
    "data_quality_concern",
}


def merge_case_reviews(sample: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    required = set(CASE_KEYS + ["review_outcome", "reviewer", "reviewed_at", "review_comment"])
    missing = required - set(decisions.columns)
    if missing:
        raise ValueError(f"Warning case decisions lack columns: {sorted(missing)}")
    if decisions.duplicated(CASE_KEYS).any():
        raise ValueError("Warning case decisions contain duplicate case keys.")
    invalid = set(decisions.review_outcome) - ALLOWED_OUTCOMES
    if invalid:
        raise ValueError(f"Invalid warning case outcomes: {sorted(invalid)}")
    if decisions.reviewer.eq("").any() or decisions.reviewed_at.eq("").any():
        raise ValueError("Every warning case decision requires reviewer and reviewed_at metadata.")
    sample_keys = set(map(tuple, sample[CASE_KEYS].astype(str).to_numpy()))
    decision_keys = set(map(tuple, decisions[CASE_KEYS].astype(str).to_numpy()))
    if sample_keys != decision_keys:
        raise ValueError("Warning case decisions must cover the sampled case keys exactly.")
    base = sample.drop(columns=["review_status", "reviewer", "reviewed_at", "review_comment"],
                       errors="ignore")
    return base.merge(decisions, on=CASE_KEYS, how="left", validate="one_to_one")


def run_case_review(sample_path: Path, decisions_path: Path,
                    output_dir: Path) -> dict[str, Any]:
    if not sample_path.exists() or not decisions_path.exists():
        raise FileNotFoundError("Warning review sample and decision register are required.")
    sample = pd.read_csv(sample_path, dtype=str).fillna("")
    decisions = pd.read_csv(decisions_path, dtype=str).fillna("")
    results = merge_case_reviews(sample, decisions)
    crosstab = pd.crosstab(results.priority_band, results.review_outcome).reset_index()
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "warning_case_review_results.csv", index=False)
    crosstab.to_csv(output_dir / "warning_case_review_crosstab.csv", index=False)
    counts = results.review_outcome.value_counts().to_dict()
    summary = {"sample_cases": len(sample), "decisions_recorded": len(decisions),
        "complete_decision_coverage": len(sample) == len(decisions),
        "review_outcome_counts": counts,
        "priority_cases_reviewed": int(results.priority_band.eq("priority_review").sum()),
        "coherent_priority_cases": int(((results.priority_band == "priority_review") &
                                         (results.review_outcome == "coherent_priority_case")).sum()),
        "likely_false_positive_cases": int(results.review_outcome.eq("likely_false_positive").sum()),
        "potential_false_negative_cases": int(results.review_outcome.eq("potential_false_negative").sum()),
        "recommended_methodology_status": "revision_required_before_approval",
        "recommended_revisions": [
            "Add minimum-volume or denominator support to percentage-based outcome rules.",
            "Review category-level point caps so peer and deterioration rules on the same metric do not overstate independent evidence.",
            "Review the 90th-percentile gate for volume pressure against the observed potential false negative.",
            "Retain insufficient-data suppression and rule-level traceability.",
        ]}
    (output_dir / "warning_case_review_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
