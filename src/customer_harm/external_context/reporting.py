"""Build Tableau-ready external-context reporting tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_economic_context_dashboard(
    boe: pd.DataFrame, ons: pd.DataFrame
) -> pd.DataFrame:
    """Create one economic-context row per reporting period."""
    value_wide = ons.pivot(
        index="reporting_period", columns="indicator_name", values="period_end_value"
    ).add_suffix("_period_end").reset_index()
    mean_wide = ons.pivot(
        index="reporting_period", columns="indicator_name", values="period_mean"
    ).add_suffix("_period_mean").reset_index()
    data = boe.merge(value_wide, on="reporting_period", validate="one_to_one")
    data = data.merge(mean_wide, on="reporting_period", validate="one_to_one")
    data["context_interpretation_notice"] = (
        "Economic context supports interpretation only; it does not establish causation "
        "and does not change the warning score."
    )
    return data.sort_values("period_start").reset_index(drop=True)


def build_product_period_context_dashboard(product: pd.DataFrame) -> pd.DataFrame:
    """Aggregate complaint observations safely to product-period grain."""
    data = product.copy()
    numeric = [
        "complaints_opened_count", "complaints_upheld_pct",
        "closed_within_3_days_pct", "closed_after_3_days_within_8_weeks_pct",
        "context_provision_rate", "context_intermediation_rate",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    grouped = data.groupby(
        ["reporting_period", "product_group", "product_group_label", "display_order"],
        as_index=False,
    ).agg(
        firm_observation_count=("firm_key", "size"),
        distinct_firm_count=("firm_key", "nunique"),
        firms_with_opened_count=("complaints_opened_count", "count"),
        complaints_opened_total=("complaints_opened_count", "sum"),
        complaints_opened_median=("complaints_opened_count", "median"),
        complaints_upheld_pct_median=("complaints_upheld_pct", "median"),
        closed_within_3_days_pct_median=("closed_within_3_days_pct", "median"),
        closed_after_3_days_within_8_weeks_pct_median=(
            "closed_after_3_days_within_8_weeks_pct", "median"
        ),
        context_provision_rate_median=("context_provision_rate", "median"),
        context_intermediation_rate_median=("context_intermediation_rate", "median"),
        priority_review_observations=("is_priority_review", "sum"),
        current_signal_observations=("has_current_signal", "sum"),
        source_anomaly_observations=("is_source_anomaly", "sum"),
    )
    coverage = data.assign(
        insufficient_data_observations=data.priority_band.eq("insufficient_data"),
        no_current_signal_observations=data.priority_band.eq("no_current_signal"),
        review_observations=data.priority_band.eq("review"),
        monitor_observations=data.priority_band.eq("monitor"),
    ).groupby(["reporting_period", "product_group"], as_index=False).agg(
        insufficient_data_observations=("insufficient_data_observations", "sum"),
        no_current_signal_observations=("no_current_signal_observations", "sum"),
        review_observations=("review_observations", "sum"),
        monitor_observations=("monitor_observations", "sum"),
    )
    grouped = grouped.merge(
        coverage, on=["reporting_period", "product_group"], validate="one_to_one"
    )
    grouped = grouped.sort_values(["product_group", "reporting_period"])
    groups = grouped.groupby("product_group", sort=False)
    previous = groups.complaints_opened_total.shift(1)
    grouped["previous_complaints_opened_total"] = previous
    grouped["change_complaints_opened_total"] = grouped.complaints_opened_total - previous
    grouped["pct_change_complaints_opened_total"] = (
        grouped.change_complaints_opened_total / previous.where(previous.ne(0))
    )
    grouped["aggregation_notice"] = (
        "Counts are product-period aggregates. Percentages and context rates are "
        "firm medians and must not be summed."
    )
    return grouped.sort_values(["reporting_period", "display_order"]).reset_index(drop=True)


def validate_context_reporting(
    economic: pd.DataFrame,
    product: pd.DataFrame,
    expected_periods: int,
    expected_products: int,
) -> list[dict[str, str]]:
    checks = {
        "economic_period_grain_unique": economic.reporting_period.is_unique,
        "economic_period_count": len(economic) == expected_periods,
        "product_period_grain_unique": not product.duplicated(
            ["reporting_period", "product_group"]
        ).any(),
        "product_period_complete": len(product) == expected_periods * expected_products,
        "distinct_firms_not_above_observations": product.distinct_firm_count.le(
            product.firm_observation_count
        ).all(),
        "priority_not_above_observations": product.priority_review_observations.le(
            product.firm_observation_count
        ).all(),
    }
    return [
        {"severity": "error", "rule": rule,
         "message": f"External-context reporting validation failed: {rule}"}
        for rule, passed in checks.items() if not passed
    ]


def run_external_context_reporting(
    external_context_dir: Path,
    reporting_dir: Path,
) -> dict[str, Any]:
    required = {
        "boe": external_context_dir / "boe_half_year_context.csv",
        "ons": external_context_dir / "ons_half_year_context.csv",
        "product": reporting_dir / "dashboard_firm_product_period.csv",
    }
    missing = [path.as_posix() for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"External-context reporting inputs are missing: {missing}")
    boe = pd.read_csv(required["boe"])
    ons = pd.read_csv(required["ons"])
    product_source = pd.read_csv(required["product"], low_memory=False)
    economic = build_economic_context_dashboard(boe, ons)
    product = build_product_period_context_dashboard(product_source)
    issues = validate_context_reporting(
        economic, product,
        expected_periods=product_source.reporting_period.nunique(),
        expected_products=product_source.product_group.nunique(),
    )
    reporting_dir.mkdir(parents=True, exist_ok=True)
    economic.to_csv(reporting_dir / "dashboard_economic_context.csv", index=False)
    product.to_csv(reporting_dir / "dashboard_product_period_context.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        reporting_dir / "dashboard_external_context_validation.csv", index=False
    )
    summary = {
        "economic_context_rows": len(economic),
        "product_period_rows": len(product),
        "reporting_periods": economic.reporting_period.nunique(),
        "product_groups": product.product_group.nunique(),
        "warning_score_integration": False,
        "relationship_key": "reporting_period",
        "validation_status": "failed" if issues else "passed",
        "validation_issues": issues,
    }
    (reporting_dir / "dashboard_external_context_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if issues:
        raise ValueError(f"External-context reporting validation failed: {issues}")
    return summary
