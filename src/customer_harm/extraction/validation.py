"""Validation rules for extracted records."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


def validate_metrics(metrics: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if metrics.empty:
        return [{"severity": "error", "rule": "metrics_not_empty", "count": 0,
                 "message": "No complaint metrics were extracted."}]
    required = ["reporting_period", "firm_name", "metric_name", "product_group",
                "measurement_unit", "source_workbook", "source_sheet", "source_row", "source_column"]
    for column in required:
        count = int(metrics[column].isna().sum() + metrics[column].astype(str).eq("").sum())
        if count:
            issues.append({"severity": "error", "rule": f"required_{column}", "count": count,
                           "message": f"{count} metric records lack {column}."})
    valid = metrics[metrics.value_status.eq("valid")]
    negative_counts = valid[(valid.measurement_unit == "count") & (valid.metric_value < 0)]
    if len(negative_counts):
        issues.append({"severity": "error", "rule": "non_negative_counts",
                       "count": len(negative_counts), "message": "Negative complaint counts found."})
    fractional_counts = valid[(valid.measurement_unit == "count") &
                              ((valid.metric_value % 1).abs() > 1e-9)]
    if len(fractional_counts):
        issues.append({"severity": "error", "rule": "integer_counts",
                       "count": len(fractional_counts), "message": "Fractional complaint counts found."})
    pct_outliers = valid[(valid.measurement_unit == "percentage") &
                         ((valid.metric_value < 0) | (valid.metric_value > 1))]
    if len(pct_outliers):
        issues.append({"severity": "warning", "rule": "percentage_expected_scale",
                       "count": len(pct_outliers),
                       "message": "Percentage values outside the expected 0-to-1 source scale were retained for review."})
    return issues


def summarise_status(frame: pd.DataFrame, column: str = "value_status") -> dict[str, int]:
    if frame.empty or column not in frame:
        return {}
    return dict(Counter(frame[column].astype(str)))


def build_total_reconciliation(metrics: pd.DataFrame) -> pd.DataFrame:
    """Reconcile additive count totals; percentages and rates are intentionally excluded."""
    columns = ["reporting_period", "firm_name", "canonical_sheet", "metric_name",
               "source_workbook", "source_sheet", "source_row", "component_count",
               "valid_component_count", "reported_total", "calculated_total", "difference",
               "reconciliation_status", "reconciliation_reason"]
    count_metrics = metrics[metrics.measurement_unit.eq("count")]
    records: list[dict[str, Any]] = []
    keys = ["reporting_period", "firm_name", "canonical_sheet", "metric_name",
            "source_workbook", "source_sheet", "source_row"]
    for key, group in count_metrics.groupby(keys, dropna=False, sort=False):
        totals = group[group.product_group.eq("grand_total")]
        if totals.empty:
            continue
        total = totals.iloc[0]
        components = group[~group.product_group.eq("grand_total")]
        valid_components = components[components.value_status.eq("valid")]
        record = dict(zip(keys, key))
        record.update({"component_count": len(components),
                       "valid_component_count": len(valid_components),
                       "reported_total": total.metric_value,
                       "calculated_total": pd.NA, "difference": pd.NA})
        if total.value_status != "valid":
            record.update({"reconciliation_status": "not_comparable",
                           "reconciliation_reason": "reported_total_not_valid"})
        elif components.empty:
            record.update({"reconciliation_status": "not_comparable",
                           "reconciliation_reason": "no_product_components"})
        elif len(valid_components) != len(components):
            record.update({"reconciliation_status": "not_comparable",
                           "reconciliation_reason": "one_or_more_components_missing"})
        else:
            calculated = float(valid_components.metric_value.sum())
            difference = float(total.metric_value) - calculated
            record.update({"calculated_total": calculated, "difference": difference,
                           "reconciliation_status": "matched" if abs(difference) < 1e-9 else "mismatch",
                           "reconciliation_reason": "" if abs(difference) < 1e-9 else "reported_total_differs_from_component_sum"})
        records.append(record)
    return pd.DataFrame(records, columns=columns)


def reconciliation_issues(sheet_reconciliation: pd.DataFrame,
                          total_reconciliation: pd.DataFrame) -> list[dict[str, Any]]:
    issues = []
    sheet_mismatches = int(sheet_reconciliation.reconciliation_status.ne("matched").sum())
    if sheet_mismatches:
        issues.append({"severity": "error", "rule": "sheet_record_reconciliation",
                       "count": sheet_mismatches,
                       "message": "Metric sheets have extracted-record count mismatches."})
    total_mismatches = int(total_reconciliation.reconciliation_status.eq("mismatch").sum())
    if total_mismatches:
        issues.append({"severity": "warning", "rule": "count_total_reconciliation",
                       "count": total_mismatches,
                       "message": "Reported count totals differ from the sum of available product components."})
    return issues
