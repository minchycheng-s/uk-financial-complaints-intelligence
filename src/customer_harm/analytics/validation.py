"""Sensitivity analysis and review sampling for warning-methodology validation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd

from customer_harm.analytics.warnings import evaluate_warning_rules, load_methodology

OBSERVATION_KEYS = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]


def build_scenarios(baseline: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    """Create one-at-a-time alternatives around the versioned baseline."""
    scenarios = [("baseline", f"Configured {baseline['methodology_id']} methodology",
                  copy.deepcopy(baseline))]

    def add(scenario_id: str, description: str, mutate) -> None:
        methodology = copy.deepcopy(baseline)
        mutate(methodology)
        scenarios.append((scenario_id, description, methodology))

    def peer_threshold(methodology, value):
        for rule in methodology["rules"]:
            for condition in rule["conditions"]:
                if condition["feature"].endswith("_peer_percentile") and condition["threshold"] == 0.9:
                    condition["threshold"] = value

    add("peer_high_85", "High-peer threshold reduced from 90th to 85th percentile",
        lambda method: peer_threshold(method, 0.85))
    add("peer_high_95", "High-peer threshold increased from 90th to 95th percentile",
        lambda method: peer_threshold(method, 0.95))

    def condition_threshold(methodology, feature, value):
        for rule in methodology["rules"]:
            for condition in rule["conditions"]:
                if condition["feature"] == feature:
                    condition["threshold"] = value

    add("context_growth_20", "Context deterioration threshold reduced from 25% to 20%",
        lambda method: [condition_threshold(method, feature, 0.2) for feature in
                        ["pct_change_context_provision_rate", "pct_change_context_intermediation_rate"]])
    add("context_growth_50", "Context deterioration threshold increased from 25% to 50%",
        lambda method: [condition_threshold(method, feature, 0.5) for feature in
                        ["pct_change_context_provision_rate", "pct_change_context_intermediation_rate"]])
    add("upheld_change_03", "Upheld deterioration reduced from five to three percentage points",
        lambda method: condition_threshold(method, "change_complaints_upheld_pct", 0.03))
    add("upheld_change_10", "Upheld deterioration increased from five to ten percentage points",
        lambda method: condition_threshold(method, "change_complaints_upheld_pct", 0.10))
    add("over_8_weeks_05", "Beyond-eight-weeks threshold reduced from 10% to 5%",
        lambda method: condition_threshold(method, "closed_over_8_weeks_pct", 0.05))
    add("over_8_weeks_20", "Beyond-eight-weeks threshold increased from 10% to 20%",
        lambda method: condition_threshold(method, "closed_over_8_weeks_pct", 0.20))

    def priority_threshold(methodology, value):
        next(band for band in methodology["priority_bands"] if band["label"] == "priority_review")[
            "minimum_score"] = value
    configured_priority = next(
        int(band["minimum_score"]) for band in baseline["priority_bands"]
        if band["label"] == "priority_review"
    )
    lower_priority = max(1, configured_priority - 1 if configured_priority <= 6 else configured_priority - 2)
    upper_priority = configured_priority + 2
    add(f"priority_score_{lower_priority}",
        f"Priority-review boundary reduced from {configured_priority} to {lower_priority} points",
        lambda method: priority_threshold(method, lower_priority))
    add(f"priority_score_{upper_priority}",
        f"Priority-review boundary increased from {configured_priority} to {upper_priority} points",
        lambda method: priority_threshold(method, upper_priority))
    add("minimum_peer_10", "Minimum peer group reduced from 20 to 10",
        lambda method: method.update(minimum_peer_size=10))
    add("minimum_peer_30", "Minimum peer group increased from 20 to 30",
        lambda method: method.update(minimum_peer_size=30))
    add("minimum_rules_2", "Minimum eligible rules reduced from three to two",
        lambda method: method.update(minimum_eligible_rules_for_classification=2))
    add("minimum_rules_4", "Minimum eligible rules increased from three to four",
        lambda method: method.update(minimum_eligible_rules_for_classification=4))
    return scenarios


def run_sensitivity(features: pd.DataFrame, methodology: dict[str, Any]) -> dict[str, pd.DataFrame]:
    summaries = []
    observation_results = []
    indicator_results = {}
    for scenario_id, description, scenario_method in build_scenarios(methodology):
        indicators, product = evaluate_warning_rules(features, scenario_method)
        indicator_results[scenario_id] = indicators
        product = product.copy()
        product["scenario_id"] = scenario_id
        product["scenario_description"] = description
        observation_results.append(product)
        counts = product.priority_band.value_counts()
        summaries.append({"scenario_id": scenario_id, "scenario_description": description,
            "observation_count": len(product), "triggered_rule_count": int(product.triggered_rule_count.sum()),
            "persistent_rule_count": int(product.persistent_rule_count.sum()),
            "mean_warning_score": product.warning_score.mean(),
            "maximum_warning_score": product.warning_score.max(),
            **{f"band_{band}": int(counts.get(band, 0)) for band in
               ["priority_review", "review", "monitor", "no_current_signal", "insufficient_data"]}})
    observations = pd.concat(observation_results, ignore_index=True)
    baseline = observations[observations.scenario_id.eq("baseline")][
        OBSERVATION_KEYS + ["priority_band", "warning_score"]
    ].rename(columns={"priority_band": "baseline_priority_band", "warning_score": "baseline_warning_score"})
    compared = observations.merge(baseline, on=OBSERVATION_KEYS, validate="many_to_one")
    transitions = compared.groupby(
        ["scenario_id", "scenario_description", "baseline_priority_band", "priority_band"],
        as_index=False
    ).size().rename(columns={"size": "observation_count", "priority_band": "scenario_priority_band"})
    stability = compared.groupby(OBSERVATION_KEYS, as_index=False).agg(
        display_firm_name=("display_firm_name", "first"),
        baseline_priority_band=("baseline_priority_band", "first"),
        baseline_warning_score=("baseline_warning_score", "first"),
        minimum_scenario_score=("warning_score", "min"), maximum_scenario_score=("warning_score", "max"),
        distinct_scenario_bands=("priority_band", "nunique"),
        scenario_bands=("priority_band", lambda values: "|".join(sorted(set(values)))),
        scenarios_same_as_baseline=("priority_band", lambda values: int(
            (values == compared.loc[values.index, "baseline_priority_band"]).sum())),
    )
    stability["scenario_count"] = len(build_scenarios(methodology))
    stability["band_stability_rate"] = stability.scenarios_same_as_baseline / stability.scenario_count
    return {"sensitivity_scenarios": pd.DataFrame(summaries),
            "sensitivity_observation_results": observations,
            "sensitivity_band_transitions": transitions,
            "sensitivity_observation_stability": stability,
            "baseline_indicators": indicator_results["baseline"]}


def select_review_sample(product_summary: pd.DataFrame, indicators: pd.DataFrame,
                         features: pd.DataFrame, per_band: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select deterministic current examples from every baseline band."""
    latest_period = max(product_summary.reporting_period)
    current = product_summary[product_summary.reporting_period.eq(latest_period)].copy()
    selected = []
    for band in ["priority_review", "review", "monitor", "no_current_signal", "insufficient_data"]:
        candidates = current[current.priority_band.eq(band)].copy()
        if band == "insufficient_data":
            candidates = candidates.sort_values(
                ["triggered_rule_count", "eligible_rule_count", "display_firm_name", "product_group"],
                ascending=[False, True, True, True]
            )
        else:
            candidates = candidates.sort_values(
                ["warning_score", "triggered_rule_count", "display_firm_name", "product_group"],
                ascending=[False, False, True, True]
            )
        selected.append(candidates.head(per_band))
    sample = pd.concat(selected, ignore_index=True)
    feature_columns = OBSERVATION_KEYS + [
        "complaints_opened_count", "complaints_upheld_pct", "closed_within_8_weeks_pct",
        "context_provision_rate", "context_intermediation_rate",
        "pct_change_complaints_opened_count", "change_complaints_upheld_pct",
        "pct_change_context_provision_rate", "pct_change_context_intermediation_rate",
    ]
    sample = sample.merge(features[feature_columns], on=OBSERVATION_KEYS, how="left", validate="one_to_one")
    sample["review_status"] = "pending_case_review"
    sample["reviewer"] = ""
    sample["reviewed_at"] = ""
    sample["review_comment"] = ""
    drilldown = sample[OBSERVATION_KEYS].merge(indicators, on=OBSERVATION_KEYS,
                                               how="left", validate="one_to_many")
    return sample, drilldown


def validate_methodology_validation(tables: dict[str, pd.DataFrame], feature_rows: int,
                                    scenario_count: int) -> list[dict[str, str]]:
    issues = []
    observations = tables["sensitivity_observation_results"]
    sample = tables["warning_review_sample"]
    checks = {
        "all_scenario_observations_present": len(observations) == feature_rows * scenario_count,
        "scenario_observation_grain_unique": not observations.duplicated(OBSERVATION_KEYS + ["scenario_id"]).any(),
        "baseline_present": observations.scenario_id.eq("baseline").sum() == feature_rows,
        "sample_grain_unique": not sample.duplicated(OBSERVATION_KEYS).any(),
        "sample_decisions_pending": sample.review_status.eq("pending_case_review").all(),
        "stability_rate_valid": tables["sensitivity_observation_stability"].band_stability_rate.between(0, 1).all(),
    }
    for rule, passed in checks.items():
        if not passed:
            issues.append({"severity": "error", "rule": rule,
                           "message": f"Methodology-validation check failed: {rule}"})
    return issues


def run_methodology_validation(feature_path: Path, methodology_path: Path,
                               output_dir: Path, per_band: int = 5) -> dict[str, Any]:
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature input does not exist: {feature_path}")
    features = pd.read_csv(feature_path, dtype={"resolved_frn": str}, low_memory=False)
    methodology = load_methodology(methodology_path)
    tables = run_sensitivity(features, methodology)
    baseline_product = tables["sensitivity_observation_results"].query("scenario_id == 'baseline'").drop(
        columns=["scenario_id", "scenario_description"]
    )
    sample, drilldown = select_review_sample(
        baseline_product, tables.pop("baseline_indicators"), features, per_band
    )
    tables["warning_review_sample"] = sample
    tables["warning_review_sample_drilldown"] = drilldown
    scenario_count = len(build_scenarios(methodology))
    issues = validate_methodology_validation(tables, len(features), scenario_count)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        output_dir / "methodology_validation_checks.csv", index=False
    )
    scenario_summary = tables["sensitivity_scenarios"]
    baseline_priority = int(scenario_summary.loc[
        scenario_summary.scenario_id.eq("baseline"), "band_priority_review"].iloc[0])
    summary = {"methodology_id": methodology["methodology_id"], "scenario_count": scenario_count,
               "feature_rows": len(features), "scenario_observation_rows": len(tables["sensitivity_observation_results"]),
               "review_sample_rows": len(sample), "review_drilldown_rows": len(drilldown),
               "baseline_priority_review_count": baseline_priority,
               "fully_stable_observations": int(tables["sensitivity_observation_stability"].band_stability_rate.eq(1).sum()),
               "validation_status": "failed" if issues else "passed", "validation_issues": issues}
    (output_dir / "methodology_validation_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if issues:
        raise ValueError(f"Methodology validation failed: {issues}")
    return summary
