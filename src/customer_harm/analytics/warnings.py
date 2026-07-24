"""Explainable early-warning indicators for investigation prioritisation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def load_methodology(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Warning methodology does not exist: {path}")
    methodology = json.loads(path.read_text(encoding="utf-8"))
    required = {"methodology_id", "methodology_status", "minimum_peer_size",
                "minimum_eligible_rules_for_classification", "maximum_persistence_bonus",
                "priority_bands", "rules"}
    missing = required - set(methodology)
    if missing:
        raise ValueError(f"Warning methodology lacks fields: {sorted(missing)}")
    rule_ids = [rule["rule_id"] for rule in methodology["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("Warning methodology contains duplicate rule IDs.")
    return methodology


def _operator(value: float, operator: str, threshold: float) -> bool:
    operations = {">=": lambda: value >= threshold, ">": lambda: value > threshold,
                  "<=": lambda: value <= threshold, "<": lambda: value < threshold,
                  "==": lambda: value == threshold}
    if operator not in operations:
        raise ValueError(f"Unsupported warning-rule operator: {operator}")
    return bool(operations[operator]())


def prepare_warning_features(features: pd.DataFrame) -> pd.DataFrame:
    data = features.copy()
    numeric_inputs = ["closed_within_3_days_pct", "closed_after_3_days_within_8_weeks_pct"]
    for column in numeric_inputs:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["closed_over_8_weeks_pct"] = 1 - (
        data.closed_within_3_days_pct + data.closed_after_3_days_within_8_weeks_pct
    )
    invalid_closure_derivation = ~data.closed_over_8_weeks_pct.between(0, 1, inclusive="both")
    data.loc[invalid_closure_derivation, "closed_over_8_weeks_pct"] = np.nan
    peer_features = ["complaints_opened_count", "complaints_upheld_pct",
                     "context_provision_rate", "context_intermediation_rate",
                     "closed_over_8_weeks_pct"]
    for feature in peer_features:
        grouped = data.groupby(["reporting_period", "product_group"])[feature]
        data[f"{feature}_peer_count"] = grouped.transform("count")
        if f"{feature}_peer_percentile" not in data:
            data[f"{feature}_peer_percentile"] = grouped.rank(
                method="average", pct=True, na_option="keep"
            )
    return data


def evaluate_warning_rules(features: pd.DataFrame,
                           methodology: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = prepare_warning_features(features)
    observation_keys = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
    identity_fields = observation_keys + ["display_firm_name", "resolved_frn",
                                           "observation_start", "observation_end"]
    records = []
    minimum_peer_size = int(methodology["minimum_peer_size"])
    for row in data.itertuples(index=False):
        values = row._asdict()
        for rule in methodology["rules"]:
            conditions = rule["conditions"]
            condition_values = {item["feature"]: values.get(item["feature"]) for item in conditions}
            peer_count = values.get(rule["peer_count_feature"])
            missing_features = [name for name, value in condition_values.items() if pd.isna(value)]
            eligible = not missing_features and pd.notna(peer_count) and float(peer_count) >= minimum_peer_size
            if not eligible:
                reason = "missing_required_feature" if missing_features else "peer_group_below_minimum"
                triggered = False
            else:
                triggered = all(_operator(float(condition_values[item["feature"]]),
                                          item["operator"], float(item["threshold"]))
                                for item in conditions)
                reason = "conditions_met" if triggered else "conditions_not_met"
            record = {field: values.get(field, "") for field in identity_fields}
            record.update({"methodology_id": methodology["methodology_id"],
                "rule_id": rule["rule_id"], "rule_label": rule["label"],
                "rule_category": rule["category"],
                "score_family": rule.get("score_family", rule["category"]),
                "eligible": eligible,
                "triggered": triggered, "eligibility_reason": reason,
                "peer_count": int(peer_count) if pd.notna(peer_count) else 0,
                "condition_evidence": json.dumps(condition_values, default=_json_default, sort_keys=True),
                "base_points": int(rule["points"]) if triggered else 0})
            records.append(record)
    indicators = pd.DataFrame(records)
    indicators = indicators.sort_values(
        ["firm_key", "product_group", "rule_id", "observation_end", "reporting_period",
         "source_reporting_period"]
    ).reset_index(drop=True)
    group = indicators.groupby(["firm_key", "product_group", "rule_id"], sort=False)
    indicators["previous_triggered"] = group.triggered.shift(1).fillna(False).astype(bool)
    indicators["persistent_trigger"] = indicators.triggered & indicators.previous_triggered

    family_scores = indicators.groupby(observation_keys + ["score_family"], as_index=False).agg(
        uncapped_family_points=("base_points", "sum")
    )
    caps = methodology.get("family_point_caps", {})
    family_scores["family_point_cap"] = family_scores.score_family.map(caps)
    family_scores["capped_family_points"] = family_scores.uncapped_family_points
    has_cap = family_scores.family_point_cap.notna()
    family_scores.loc[has_cap, "capped_family_points"] = np.minimum(
        family_scores.loc[has_cap, "uncapped_family_points"],
        family_scores.loc[has_cap, "family_point_cap"],
    )
    score_totals = family_scores.groupby(observation_keys, as_index=False).agg(
        uncapped_base_warning_score=("uncapped_family_points", "sum"),
        base_warning_score=("capped_family_points", "sum"),
    )
    family_evidence = family_scores.groupby(observation_keys, as_index=False).apply(
        lambda rows: json.dumps({row.score_family: {
            "uncapped_points": int(row.uncapped_family_points),
            "cap": int(row.family_point_cap) if pd.notna(row.family_point_cap) else None,
            "capped_points": int(row.capped_family_points),
        } for row in rows.itertuples(index=False)}, sort_keys=True)
    ).rename(columns={None: "family_score_evidence"})

    aggregate = indicators.groupby(observation_keys, as_index=False).agg(
        display_firm_name=("display_firm_name", "first"), resolved_frn=("resolved_frn", "first"),
        observation_start=("observation_start", "first"), observation_end=("observation_end", "first"),
        eligible_rule_count=("eligible", "sum"), triggered_rule_count=("triggered", "sum"),
        persistent_rule_count=("persistent_trigger", "sum"),
        triggered_rule_ids=("rule_id", lambda values: "|".join(values[indicators.loc[values.index, "triggered"]])),
    )
    aggregate = aggregate.merge(score_totals, on=observation_keys, validate="one_to_one")
    aggregate = aggregate.merge(family_evidence, on=observation_keys, validate="one_to_one")
    aggregate["point_cap_reduction"] = (
        aggregate.uncapped_base_warning_score - aggregate.base_warning_score
    )
    maximum_bonus = int(methodology["maximum_persistence_bonus"])
    aggregate["persistence_bonus"] = aggregate.persistent_rule_count.clip(upper=maximum_bonus)
    aggregate["warning_score"] = aggregate.base_warning_score + aggregate.persistence_bonus
    minimum_rules = int(methodology["minimum_eligible_rules_for_classification"])
    aggregate["coverage_status"] = np.select(
        [aggregate.eligible_rule_count >= 6, aggregate.eligible_rule_count >= minimum_rules],
        ["broad", "partial"], default="limited"
    )
    aggregate["priority_band"] = aggregate.warning_score.map(
        lambda score: _priority_band(int(score), methodology["priority_bands"])
    )
    aggregate.loc[aggregate.eligible_rule_count < minimum_rules, "priority_band"] = "insufficient_data"
    aggregate["methodology_id"] = methodology["methodology_id"]
    aggregate["methodology_status"] = methodology["methodology_status"]
    return indicators, aggregate


def _json_default(value: Any):
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return str(value)


def _priority_band(score: int, bands: list[dict[str, Any]]) -> str:
    ordered = sorted(bands, key=lambda item: int(item["minimum_score"]), reverse=True)
    return next(item["label"] for item in ordered if score >= int(item["minimum_score"]))


def build_firm_period_summary(product_summary: pd.DataFrame) -> pd.DataFrame:
    def joined(values):
        return "|".join(sorted(set(str(value) for value in values if str(value))))
    return product_summary.groupby(["firm_key", "reporting_period"], as_index=False).agg(
        display_firm_name=("display_firm_name", "first"), resolved_frn=("resolved_frn", "first"),
        product_observation_count=("product_group", "size"),
        products_with_signals=("product_group", lambda values: joined(
            values[product_summary.loc[values.index, "triggered_rule_count"] > 0])),
        products_priority_review=("product_group", lambda values: joined(
            values[product_summary.loc[values.index, "priority_band"] == "priority_review"])),
        maximum_product_warning_score=("warning_score", "max"),
        total_triggered_rules=("triggered_rule_count", "sum"),
        total_persistent_rules=("persistent_rule_count", "sum"),
        insufficient_data_products=("priority_band", lambda values: int((values == "insufficient_data").sum())),
    )


def validate_warning_outputs(indicators: pd.DataFrame, product_summary: pd.DataFrame,
                             feature_rows: int, rule_count: int) -> list[dict[str, str]]:
    issues = []
    observation_keys = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
    checks = {
        "indicator_row_count": len(indicators) == feature_rows * rule_count,
        "indicator_rule_grain_unique": not indicators.duplicated(observation_keys + ["rule_id"]).any(),
        "product_summary_row_count": len(product_summary) == feature_rows,
        "product_summary_grain_unique": not product_summary.duplicated(observation_keys).any(),
        "ineligible_rules_not_triggered": not indicators.loc[~indicators.eligible, "triggered"].any(),
        "scores_non_negative": product_summary.warning_score.ge(0).all(),
        "insufficient_data_not_prioritised": product_summary.loc[
            product_summary.priority_band.eq("insufficient_data"), "eligible_rule_count"
        ].lt(3).all(),
    }
    for rule, passed in checks.items():
        if not passed:
            issues.append({"severity": "error", "rule": rule,
                           "message": f"Warning-output validation failed: {rule}"})
    return issues


def run_warning_build(feature_path: Path, methodology_path: Path,
                      output_dir: Path) -> dict[str, Any]:
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature input does not exist: {feature_path}")
    features = pd.read_csv(feature_path, dtype={"resolved_frn": str}, low_memory=False)
    methodology = load_methodology(methodology_path)
    indicators, product_summary = evaluate_warning_rules(features, methodology)
    firm_summary = build_firm_period_summary(product_summary)
    issues = validate_warning_outputs(indicators, product_summary, len(features), len(methodology["rules"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    indicators.to_csv(output_dir / "warning_indicators.csv", index=False)
    product_summary.to_csv(output_dir / "firm_product_warning_summary.csv", index=False)
    firm_summary.to_csv(output_dir / "firm_period_warning_summary.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        output_dir / "warning_validation.csv", index=False
    )
    snapshot = {**methodology, "source_methodology_file": str(methodology_path)}
    (output_dir / "warning_methodology_snapshot.json").write_text(
        json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
    )
    summary = {"methodology_id": methodology["methodology_id"],
               "methodology_status": methodology["methodology_status"],
               "feature_rows": len(features), "indicator_rows": len(indicators),
               "product_warning_rows": len(product_summary), "firm_period_rows": len(firm_summary),
               "eligible_indicators": int(indicators.eligible.sum()),
               "triggered_indicators": int(indicators.triggered.sum()),
               "persistent_indicators": int(indicators.persistent_trigger.sum()),
               "priority_band_counts": product_summary.priority_band.value_counts().to_dict(),
               "validation_status": "failed" if issues else "passed", "validation_issues": issues}
    (output_dir / "warning_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if issues:
        raise ValueError(f"Warning validation failed: {issues}")
    return summary
