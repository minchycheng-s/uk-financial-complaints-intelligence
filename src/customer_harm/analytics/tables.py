"""Build validated analysis-ready fact and dimension tables."""

from __future__ import annotations

import hashlib
import json
import re
from calendar import monthrange
from pathlib import Path
from typing import Any

import pandas as pd

from customer_harm.matching.resolution import normalise_firm_name


def stable_key(prefix: str, *values: object, length: int = 16) -> str:
    text = "|".join(str(value) for value in values)
    return f"{prefix}:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:length].upper()}"


def firm_key(resolved_frn: object, firm_name: object) -> str:
    frn = str(resolved_frn).strip()
    if frn and frn.casefold() != "nan":
        cleaned_frn = re.sub(r"\.0$", "", frn)
        return f"FRN:{cleaned_frn}"
    return stable_key("NAME", normalise_firm_name(firm_name))


def _load_quality_decisions(path: Path) -> pd.DataFrame:
    columns = ["reporting_period", "source_workbook", "source_sheet", "source_row", "source_column",
               "quality_flag", "quality_review_status", "reviewer", "reviewed_at", "reviewer_comment"]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    decisions = pd.read_csv(path, dtype=str).fillna("")
    missing = set(columns) - set(decisions.columns)
    if missing:
        raise ValueError(f"Metric quality decisions lack columns: {sorted(missing)}")
    keys = columns[:5]
    if decisions.duplicated(keys).any():
        raise ValueError("Metric quality decisions contain duplicate source cells.")
    return decisions[columns]


def build_analysis_tables(metrics: pd.DataFrame, quality_decisions: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data = metrics.copy()
    for column in ["resolved_frn", "source_reporting_period", "measurement_basis", "value_reason"]:
        if column not in data:
            data[column] = ""
    data["resolved_frn"] = data.resolved_frn.fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
    data["firm_key"] = [firm_key(frn, name) for frn, name in zip(data.resolved_frn, data.firm_name)]
    data["product_key"] = data.product_group.map(lambda value: f"PRODUCT:{value}")
    data["metric_key"] = [stable_key("METRIC", sheet, metric, unit)
                          for sheet, metric, unit in zip(data.canonical_sheet,
                                                        data.metric_name, data.measurement_unit)]
    data["fact_id"] = [stable_key("FACT", workbook, sheet, row, column, length=20)
                       for workbook, sheet, row, column in zip(data.source_workbook, data.source_sheet,
                                                               data.source_row, data.source_column)]
    quality_keys = ["reporting_period", "source_workbook", "source_sheet", "source_row", "source_column"]
    for column in ["source_row", "source_column"]:
        data[column] = data[column].astype(str).str.replace(r"\.0$", "", regex=True)
        quality_decisions[column] = quality_decisions[column].astype(str).str.replace(r"\.0$", "", regex=True)
    quality_fields = quality_keys + ["quality_flag", "quality_review_status", "reviewer",
                                     "reviewed_at", "reviewer_comment"]
    data = data.merge(quality_decisions[quality_fields], on=quality_keys, how="left", validate="one_to_one")
    outlier = (data.measurement_unit.eq("percentage") & data.value_status.eq("valid") &
               ((pd.to_numeric(data.metric_value, errors="coerce") < 0) |
                (pd.to_numeric(data.metric_value, errors="coerce") > 1)))
    data["quality_flag"] = data.quality_flag.fillna("")
    data.loc[outlier & data.quality_flag.eq(""), "quality_flag"] = "percentage_above_expected_range"
    data["quality_review_status"] = data.quality_review_status.fillna("")
    data.loc[outlier & data.quality_review_status.eq(""), "quality_review_status"] = "pending_review"
    data.loc[data.quality_review_status.eq(""), "quality_review_status"] = "not_flagged"
    data["quality_reviewer"] = data.reviewer.fillna("")
    data["quality_reviewed_at"] = data.reviewed_at.fillna("")
    data["quality_review_comment"] = data.reviewer_comment.fillna("")
    data["is_valid_value"] = data.value_status.eq("valid")
    data["is_product_level"] = ~data.product_group.eq("grand_total")
    data["is_analysis_ready_value"] = data.is_valid_value & ~data.quality_review_status.eq("pending_review")

    fact_columns = ["fact_id", "firm_key", "reporting_period", "source_reporting_period",
        "product_key", "metric_key", "firm_name", "resolved_frn", "raw_firm_group",
        "joint_reporting_flag", "canonical_sheet", "metric_name", "product_group", "metric_value",
        "measurement_unit", "measurement_basis", "value_status", "value_reason", "quality_flag",
        "quality_review_status", "quality_reviewer", "quality_reviewed_at", "quality_review_comment",
        "is_valid_value", "is_product_level", "is_analysis_ready_value", "raw_value", "raw_header",
        "source_workbook", "source_sheet", "source_row", "source_column"]
    fact = data[fact_columns].copy()

    firm_observations = data[["firm_key", "resolved_frn", "firm_name", "reporting_period",
                              "match_status", "match_method", "match_confidence"]].drop_duplicates()
    latest = firm_observations.sort_values(["firm_key", "reporting_period", "firm_name"]).groupby(
        "firm_key", as_index=False
    ).tail(1)
    coverage = firm_observations.groupby("firm_key", as_index=False).agg(
        first_reporting_period=("reporting_period", "min"),
        last_reporting_period=("reporting_period", "max"),
        observed_name_count=("firm_name", "nunique"),
    )
    dim_firm = latest.merge(coverage, on="firm_key", validate="one_to_one").rename(
        columns={"firm_name": "display_firm_name", "match_status": "identity_match_status",
                 "match_method": "identity_match_method", "match_confidence": "identity_match_confidence"}
    )[["firm_key", "resolved_frn", "display_firm_name", "identity_match_status",
       "identity_match_method", "identity_match_confidence", "first_reporting_period",
       "last_reporting_period", "observed_name_count"]].sort_values("firm_key")

    periods = sorted(data.reporting_period.unique())
    period_rows = []
    for index, period in enumerate(periods):
        year = int(period[:4]); half = int(period[-1])
        start_month, end_month = (1, 6) if half == 1 else (7, 12)
        period_rows.append({"reporting_period": period, "year": year, "half": half,
            "period_start": f"{year}-{start_month:02d}-01",
            "period_end": f"{year}-{end_month:02d}-{monthrange(year, end_month)[1]:02d}",
            "previous_reporting_period": periods[index - 1] if index else ""})
    dim_reporting_period = pd.DataFrame(period_rows)

    product_order = ["banking_and_credit_cards", "decumulation_and_pensions", "home_finance",
                     "insurance_and_pure_protection", "investments", "consumer_credit", "grand_total"]
    dim_product_group = pd.DataFrame([{"product_key": f"PRODUCT:{value}",
        "product_group": value, "product_group_label": value.replace("_", " ").title(),
        "is_grand_total": value == "grand_total", "display_order": index + 1}
        for index, value in enumerate(product_order)])

    dim_metric = data[["metric_key", "canonical_sheet", "metric_name", "measurement_unit"]].drop_duplicates()
    dim_metric["is_additive"] = dim_metric.measurement_unit.eq("count")
    dim_metric["metric_label"] = dim_metric.metric_name.str.replace("_", " ").str.title()
    dim_metric = dim_metric.sort_values(["metric_name", "measurement_unit", "canonical_sheet"])
    return {"fact_firm_complaints": fact, "dim_firm": dim_firm.reset_index(drop=True),
            "dim_reporting_period": dim_reporting_period, "dim_product_group": dim_product_group,
            "dim_metric": dim_metric.reset_index(drop=True)}


def validate_analysis_tables(tables: dict[str, pd.DataFrame], input_rows: int) -> list[dict[str, Any]]:
    fact = tables["fact_firm_complaints"]
    issues = []
    checks = {
        "fact_row_count_preserved": len(fact) == input_rows,
        "fact_id_unique": not fact.fact_id.duplicated().any(),
        "source_cell_unique": not fact.duplicated(["source_workbook", "source_sheet", "source_row", "source_column"]).any(),
        "firm_key_complete": fact.firm_key.ne("").all(),
        "firm_foreign_key_valid": set(fact.firm_key) <= set(tables["dim_firm"].firm_key),
        "product_foreign_key_valid": set(fact.product_key) <= set(tables["dim_product_group"].product_key),
        "metric_foreign_key_valid": set(fact.metric_key) <= set(tables["dim_metric"].metric_key),
        "period_foreign_key_valid": set(fact.reporting_period) <= set(tables["dim_reporting_period"].reporting_period),
    }
    for rule, passed in checks.items():
        if not passed:
            issues.append({"severity": "error", "rule": rule, "message": f"Analysis-table check failed: {rule}"})
    pending_quality = int(fact.quality_review_status.eq("pending_review").sum())
    if pending_quality:
        issues.append({"severity": "warning", "rule": "pending_metric_quality_review",
                       "message": f"{pending_quality} fact rows have pending quality review."})
    return issues


def run_analysis_table_build(input_path: Path, quality_decisions_path: Path,
                             output_dir: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Reviewed metric input does not exist: {input_path}")
    metrics = pd.read_csv(input_path, dtype={"frn": str, "resolved_frn": str}, low_memory=False)
    quality = _load_quality_decisions(quality_decisions_path)
    tables = build_analysis_tables(metrics, quality)
    issues = validate_analysis_tables(tables, len(metrics))
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        output_dir / "analysis_table_validation.csv", index=False
    )
    fact = tables["fact_firm_complaints"]
    summary = {"input_rows": len(metrics), "fact_rows": len(fact),
               "row_count_preserved": len(metrics) == len(fact),
               "dimension_rows": {name: len(frame) for name, frame in tables.items() if name.startswith("dim_")},
               "resolved_fact_rows": int(fact.resolved_frn.fillna("").ne("").sum()),
               "unresolved_fact_rows": int(fact.resolved_frn.fillna("").eq("").sum()),
               "valid_fact_rows": int(fact.is_valid_value.sum()),
               "analysis_ready_value_rows": int(fact.is_analysis_ready_value.sum()),
               "confirmed_quality_flags": int(fact.quality_review_status.eq("source_value_confirmed").sum()),
               "validation_status": "failed" if any(i["severity"] == "error" for i in issues) else "passed_with_warnings" if issues else "passed",
               "validation_issues": issues}
    (output_dir / "analysis_table_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if summary["validation_status"] == "failed":
        raise ValueError(f"Analysis-table validation failed: {issues}")
    return summary
