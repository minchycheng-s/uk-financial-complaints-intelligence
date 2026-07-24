"""Build measurement-safe firm/product trend and peer features."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

FEATURE_MAP = {
    ("opened", "complaints_opened", "count"): "complaints_opened_count",
    ("closed", "complaints_closed", "count"): "complaints_closed_count",
    ("consumer_credit", "complaints_opened", "count"): "complaints_opened_count",
    ("consumer_credit", "complaints_closed", "count"): "complaints_closed_count",
    ("consumer_credit", "complaints_upheld", "count"): "complaints_upheld_count",
    ("consumer_credit", "complaints_upheld", "percentage"): "complaints_upheld_pct",
    ("percentage_upheld", "complaints_upheld", "percentage"): "complaints_upheld_pct",
    ("percentage_within_3_days", "closed_within_3_days", "percentage"): "closed_within_3_days_pct",
    ("percentage_after_3_days_within_8_weeks", "closed_after_3_days_within_8_weeks", "percentage"):
        "closed_after_3_days_within_8_weeks_pct",
    ("context_provision", "complaints_in_context", "context_rate"): "context_provision_rate",
    ("context_intermediation", "complaints_in_context", "context_rate"): "context_intermediation_rate",
}

BASE_FEATURES = list(dict.fromkeys(FEATURE_MAP.values()))
TREND_FEATURES = ["complaints_opened_count", "context_provision_rate",
                  "context_intermediation_rate", "complaints_upheld_pct",
                  "closed_within_3_days_pct", "closed_after_3_days_within_8_weeks_pct"]
BENCHMARK_FEATURES = ["complaints_opened_count", "context_provision_rate",
                      "context_intermediation_rate", "complaints_upheld_pct",
                      "closed_within_3_days_pct", "closed_after_3_days_within_8_weeks_pct"]


def parse_source_window(value: object) -> tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]:
    text = str(value).strip()
    if " to " not in text:
        return pd.NaT, pd.NaT
    start_text, end_text = [part.strip() for part in text.split(" to ", 1)]
    def parse(part: str):
        format_string = "%Y-%m-%d" if len(part) >= 4 and part[:4].isdigit() else "%d-%m-%Y"
        return pd.to_datetime(part, format=format_string, errors="coerce")
    return parse(start_text), parse(end_text)


def _feature_name(row: pd.Series) -> str:
    key = (row.canonical_sheet, row.metric_name, row.measurement_unit)
    if key not in FEATURE_MAP:
        raise ValueError(f"No analytical feature mapping for {key}")
    return FEATURE_MAP[key]


def build_feature_tables(fact: pd.DataFrame, dim_firm: pd.DataFrame) -> dict[str, pd.DataFrame]:
    valid = fact[fact.is_analysis_ready_value.astype(str).str.casefold().eq("true") &
                 fact.is_product_level.astype(str).str.casefold().eq("true")].copy()
    valid["feature_name"] = valid.apply(_feature_name, axis=1)
    index = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
    collision = valid.duplicated(index + ["feature_name"])
    if collision.any():
        raise ValueError("Multiple valid source values map to the same firm/product observation feature.")
    features = valid.pivot(index=index, columns="feature_name", values="metric_value").reset_index()
    features.columns.name = None
    for column in BASE_FEATURES:
        if column not in features:
            features[column] = np.nan
        features[column] = pd.to_numeric(features[column], errors="coerce")
    names = dim_firm[["firm_key", "resolved_frn", "display_firm_name",
                      "identity_match_status", "identity_match_confidence"]]
    features = features.merge(names, on="firm_key", how="left", validate="many_to_one")
    windows = features.source_reporting_period.map(parse_source_window)
    features["observation_start"] = [value[0] for value in windows]
    features["observation_end"] = [value[1] for value in windows]
    features["observation_days"] = (features.observation_end - features.observation_start).dt.days + 1
    features["closed_within_8_weeks_pct"] = (
        features.closed_within_3_days_pct + features.closed_after_3_days_within_8_weeks_pct
    )
    features["opened_minus_closed_count"] = (
        features.complaints_opened_count - features.complaints_closed_count
    )

    features = features.sort_values(
        ["firm_key", "product_group", "observation_end", "reporting_period", "source_reporting_period"],
        na_position="last"
    ).reset_index(drop=True)
    groups = features.groupby(["firm_key", "product_group"], sort=False, dropna=False)
    for column in TREND_FEATURES:
        previous = groups[column].shift(1)
        features[f"previous_{column}"] = previous
        features[f"change_{column}"] = features[column] - previous
        features[f"pct_change_{column}"] = np.where(
            previous.notna() & previous.ne(0), (features[column] - previous) / previous, np.nan
        )

    benchmark_records = []
    for (period, product), group in features.groupby(["reporting_period", "product_group"], sort=True):
        record: dict[str, Any] = {"reporting_period": period, "product_group": product,
                                  "firm_observation_count": len(group)}
        for column in BENCHMARK_FEATURES:
            values = group[column].dropna()
            record[f"{column}_peer_count"] = len(values)
            record[f"{column}_median"] = values.median() if len(values) else np.nan
            record[f"{column}_q25"] = values.quantile(0.25) if len(values) else np.nan
            record[f"{column}_q75"] = values.quantile(0.75) if len(values) else np.nan
        benchmark_records.append(record)
        if len(group):
            group_index = group.index
            for column in BENCHMARK_FEATURES:
                features.loc[group_index, f"{column}_peer_percentile"] = group[column].rank(
                    method="average", pct=True, na_option="keep"
                )
    benchmarks = pd.DataFrame(benchmark_records)
    return {"firm_product_period_features": features,
            "product_period_benchmarks": benchmarks}


def validate_feature_tables(tables: dict[str, pd.DataFrame], valid_product_fact_rows: int) -> list[dict[str, str]]:
    features = tables["firm_product_period_features"]
    issues = []
    grain = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
    checks = {
        "feature_grain_unique": not features.duplicated(grain).any(),
        "firm_key_complete": features.firm_key.ne("").all(),
        "reporting_window_dates_parsed": features.observation_start.notna().all() and features.observation_end.notna().all(),
        "reporting_window_order_valid": features.observation_end.ge(features.observation_start).all(),
        "all_valid_fact_values_consumed": int(features[BASE_FEATURES].notna().sum().sum()) == valid_product_fact_rows,
    }
    for rule, passed in checks.items():
        if not passed:
            issues.append({"severity": "error", "rule": rule,
                           "message": f"Feature validation failed: {rule}"})
    return issues


def run_feature_build(processed_dir: Path, output_dir: Path) -> dict[str, Any]:
    fact_path, firms_path = processed_dir / "fact_firm_complaints.csv", processed_dir / "dim_firm.csv"
    if not fact_path.exists() or not firms_path.exists():
        raise FileNotFoundError("Processed fact_firm_complaints.csv and dim_firm.csv are required.")
    fact = pd.read_csv(fact_path, dtype={"resolved_frn": str}, low_memory=False).fillna("")
    firms = pd.read_csv(firms_path, dtype={"resolved_frn": str}).fillna("")
    valid_product_rows = int(fact.is_analysis_ready_value.astype(str).str.casefold().eq("true").mul(
        fact.is_product_level.astype(str).str.casefold().eq("true")
    ).sum())
    tables = build_feature_tables(fact, firms)
    issues = validate_feature_tables(tables, valid_product_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        output_dir / "feature_validation.csv", index=False
    )
    features = tables["firm_product_period_features"]
    summary = {"valid_product_fact_rows": valid_product_rows,
               "feature_rows": len(features),
               "benchmark_rows": len(tables["product_period_benchmarks"]),
               "firms": features.firm_key.nunique(), "products": features.product_group.nunique(),
               "reporting_periods": features.reporting_period.nunique(),
               "base_feature_non_null_counts": features[BASE_FEATURES].notna().sum().to_dict(),
               "validation_status": "failed" if issues else "passed", "validation_issues": issues}
    (output_dir / "feature_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if issues:
        raise ValueError(f"Feature validation failed: {issues}")
    return summary
