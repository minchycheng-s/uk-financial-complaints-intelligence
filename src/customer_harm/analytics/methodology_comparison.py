"""Compare two warning-methodology outputs and replay reviewed cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

KEYS = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]


def compare_methodologies(v1: pd.DataFrame, v2: pd.DataFrame,
                          reviews: pd.DataFrame) -> dict[str, pd.DataFrame]:
    columns = KEYS + ["display_firm_name", "warning_score", "priority_band",
                      "triggered_rule_ids"]
    comparison = v1[columns].merge(
        v2[columns], on=KEYS, validate="one_to_one", suffixes=("_v1", "_v2")
    )
    comparison["band_changed"] = comparison.priority_band_v1.ne(comparison.priority_band_v2)
    comparison["score_change"] = comparison.warning_score_v2 - comparison.warning_score_v1
    transitions = comparison.groupby(
        ["priority_band_v1", "priority_band_v2"], as_index=False
    ).size().rename(columns={"size": "observation_count"})
    reviewed = reviews.merge(comparison, on=KEYS, validate="one_to_one")
    reviewed["review_alignment_v2"] = reviewed.apply(_review_alignment, axis=1)
    return {"observation_band_comparison": comparison,
            "band_transition_summary": transitions,
            "reviewed_case_comparison": reviewed}


def _review_alignment(row: pd.Series) -> str:
    outcome, v2_band = row.review_outcome, row.priority_band_v2
    if outcome == "coherent_priority_case":
        return "aligned" if v2_band == "priority_review" else "needs_review"
    if outcome == "likely_false_positive":
        return "aligned" if v2_band in {"no_current_signal", "monitor", "insufficient_data"} else "needs_review"
    if outcome == "potential_false_negative":
        return "aligned" if v2_band in {"monitor", "review", "priority_review"} else "needs_review"
    return "not_targeted_by_revision"


def run_methodology_comparison(v1_path: Path, v2_path: Path, reviews_path: Path,
                               output_dir: Path) -> dict[str, Any]:
    inputs = [v1_path, v2_path, reviews_path]
    if missing := [str(path) for path in inputs if not path.exists()]:
        raise FileNotFoundError(f"Methodology comparison inputs do not exist: {missing}")
    tables = compare_methodologies(
        pd.read_csv(v1_path, low_memory=False), pd.read_csv(v2_path, low_memory=False),
        pd.read_csv(reviews_path, low_memory=False),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    observations = tables["observation_band_comparison"]
    reviewed = tables["reviewed_case_comparison"]
    summary = {
        "observation_count": len(observations),
        "v1_priority_review_count": int(observations.priority_band_v1.eq("priority_review").sum()),
        "v2_priority_review_count": int(observations.priority_band_v2.eq("priority_review").sum()),
        "changed_band_count": int(observations.band_changed.sum()),
        "reviewed_case_count": len(reviewed),
        "targeted_review_cases": int(reviewed.review_alignment_v2.ne("not_targeted_by_revision").sum()),
        "targeted_cases_aligned": int(reviewed.review_alignment_v2.eq("aligned").sum()),
        "targeted_cases_needing_review": int(reviewed.review_alignment_v2.eq("needs_review").sum()),
    }
    (output_dir / "methodology_comparison_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
