"""Structured analytical review of every priority observation in a methodology run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

KEYS = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]


def build_priority_reviews(summary: pd.DataFrame, indicators: pd.DataFrame,
                           features: pd.DataFrame, previous_reviews: pd.DataFrame,
                           reviewer: str, reviewed_at: str,
                           source_resolutions: pd.DataFrame | None = None) -> pd.DataFrame:
    priority = summary.loc[summary.priority_band.eq("priority_review")].copy()
    triggered = indicators.loc[indicators.triggered].copy()
    families = triggered.groupby(KEYS, as_index=False).agg(
        independent_signal_family_count=("score_family", "nunique"),
        triggered_signal_families=("score_family", lambda x: "|".join(sorted(set(x)))),
        persistent_trigger_ids=("rule_id", lambda x: "|".join(sorted(set(
            x[triggered.loc[x.index, "persistent_trigger"]]
        )))),
    )
    feature_columns = KEYS + [
        "complaints_opened_count", "complaints_closed_count", "complaints_upheld_pct",
        "closed_within_8_weeks_pct", "context_provision_rate",
        "context_intermediation_rate", "identity_match_status",
    ]
    reviewed = priority.merge(families, on=KEYS, validate="one_to_one").merge(
        features[feature_columns], on=KEYS, validate="one_to_one", suffixes=("", "_feature")
    )
    previous_columns = KEYS + ["review_outcome", "review_comment"]
    reviewed = reviewed.merge(
        previous_reviews[previous_columns].rename(columns={
            "review_outcome": "previous_sample_review_outcome",
            "review_comment": "previous_sample_review_comment",
        }), on=KEYS, how="left", validate="one_to_one"
    )
    reviewed["review_flags"] = reviewed.apply(_review_flags, axis=1)
    reviewed["review_disposition"] = reviewed.apply(_disposition, axis=1)
    reviewed["review_comment"] = reviewed.apply(_comment, axis=1)
    if source_resolutions is not None:
        resolution_keys = ["reporting_period", "display_firm_name", "product_group"]
        required = set(resolution_keys + ["source_check_status", "source_check_resolution",
                                          "source_check_evidence", "resolved_disposition"])
        if missing := required - set(source_resolutions.columns):
            raise ValueError(f"Source-check resolutions lack columns: {sorted(missing)}")
        if source_resolutions.duplicated(resolution_keys).any():
            raise ValueError("Source-check resolutions contain duplicate case keys.")
        reviewed = reviewed.merge(source_resolutions[list(required)], on=resolution_keys,
                                  how="left", validate="one_to_one")
        has_resolution = reviewed.resolved_disposition.notna()
        reviewed.loc[has_resolution, "review_disposition"] = reviewed.loc[
            has_resolution, "resolved_disposition"
        ]
        reviewed.loc[has_resolution, "review_comment"] = reviewed.loc[
            has_resolution, "review_comment"
        ] + " Source-check resolution: " + reviewed.loc[has_resolution, "source_check_resolution"]
    reviewed["review_method"] = "structured_analytical_review_v1"
    reviewed["reviewer"] = reviewer
    reviewed["reviewed_at"] = reviewed_at
    reviewed["business_approval_status"] = "pending_business_review"
    return reviewed


def _review_flags(row: pd.Series) -> str:
    flags = []
    if row.complaints_closed_count < 50:
        flags.append("low_closed_denominator_20_to_49")
    closure = row.closed_within_8_weeks_pct
    if pd.notna(closure) and not 0 <= closure <= 1:
        flags.append("closure_percentage_outside_0_to_100")
    if ((pd.notna(row.context_provision_rate) and row.context_provision_rate > 1000) or
            (pd.notna(row.context_intermediation_rate) and row.context_intermediation_rate > 1000)):
        flags.append("context_rate_above_1000_check_units")
    if row.identity_match_status != "matched":
        flags.append("firm_identity_unmatched")
    return "|".join(flags)


def _disposition(row: pd.Series) -> str:
    if row.review_flags:
        return "source_check_required_before_reliance"
    if row.independent_signal_family_count >= 3 or row.warning_score >= 9:
        return "retain_priority_review"
    return "retain_priority_review_borderline"


def _comment(row: pd.Series) -> str:
    evidence = (f"Score {int(row.warning_score)} from {int(row.triggered_rule_count)} rules across "
                f"{int(row.independent_signal_family_count)} independent signal families "
                f"({row.triggered_signal_families}).")
    persistence = (f" Persistent rules: {row.persistent_trigger_ids}."
                   if row.persistent_trigger_ids else " No rule persisted from the prior period.")
    if row.review_flags:
        conclusion = (f" Keep in the priority queue, but verify {row.review_flags.replace('|', ', ')} "
                      "against the source workbook and definitions before relying on the score.")
    elif row.independent_signal_family_count >= 3 or row.warning_score >= 9:
        conclusion = " Multiple or reinforced signals support retaining priority-review status."
    else:
        conclusion = (" This is an exact-boundary case supported by two distinct families; retain for "
                      "review but rank below stronger priority cases.")
    return evidence + persistence + conclusion + " This is prioritisation evidence, not a harm finding."


def run_priority_review(summary_path: Path, indicators_path: Path, features_path: Path,
                        previous_reviews_path: Path, output_path: Path,
                        summary_output_path: Path, reviewer: str,
                        reviewed_at: str,
                        source_resolutions_path: Path | None = None) -> dict[str, Any]:
    paths = [summary_path, indicators_path, features_path, previous_reviews_path]
    if missing := [str(path) for path in paths if not path.exists()]:
        raise FileNotFoundError(f"Priority-review inputs do not exist: {missing}")
    source_resolutions = None
    if source_resolutions_path is not None and source_resolutions_path.exists():
        source_resolutions = pd.read_csv(source_resolutions_path, low_memory=False)
    reviews = build_priority_reviews(
        pd.read_csv(summary_path, low_memory=False),
        pd.read_csv(indicators_path, low_memory=False),
        pd.read_csv(features_path, low_memory=False),
        pd.read_csv(previous_reviews_path, low_memory=False), reviewer, reviewed_at,
        source_resolutions,
    )
    if reviews.duplicated(KEYS).any():
        raise ValueError("Priority-review decisions are not unique at observation grain.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    reviews.to_csv(output_path, index=False)
    result = {
        "priority_cases_reviewed": len(reviews),
        "complete_review_coverage": True,
        "review_disposition_counts": reviews.review_disposition.value_counts().to_dict(),
        "flag_counts": {
            flag: int(reviews.review_flags.str.contains(flag, regex=False).sum())
            for flag in sorted({item for value in reviews.review_flags for item in value.split("|") if item})
        },
        "previously_sampled_cases": int(reviews.previous_sample_review_outcome.notna().sum()),
        "source_checks_resolved_or_confirmed": int(
            reviews.get("source_check_status", pd.Series(dtype=str)).notna().sum()
        ),
        "business_approval_status": "pending_business_review",
    }
    summary_output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
