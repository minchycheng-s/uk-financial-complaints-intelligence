"""Build validated, Tableau-ready tables from reviewed analytical outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

OBSERVATION_KEYS = ["firm_key", "reporting_period", "source_reporting_period", "product_group"]
PERIOD_BAND_ORDER = ["priority_review", "review", "monitor", "no_current_signal", "insufficient_data"]


def _read(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Reporting input does not exist: {path}")
    return pd.read_csv(path, low_memory=False, **kwargs)


def build_firm_product_dashboard(features: pd.DataFrame, warnings: pd.DataFrame,
                                 reviews: pd.DataFrame, periods: pd.DataFrame,
                                 products: pd.DataFrame) -> pd.DataFrame:
    warning_columns = OBSERVATION_KEYS + [
        "eligible_rule_count", "triggered_rule_count", "persistent_rule_count",
        "triggered_rule_ids", "uncapped_base_warning_score", "base_warning_score",
        "family_score_evidence", "point_cap_reduction", "persistence_bonus",
        "warning_score", "coverage_status", "priority_band", "methodology_id",
        "methodology_status",
    ]
    data = features.merge(warnings[warning_columns], on=OBSERVATION_KEYS,
                          validate="one_to_one")
    review_columns = OBSERVATION_KEYS + [
        "independent_signal_family_count", "triggered_signal_families",
        "persistent_trigger_ids", "review_flags", "review_disposition",
        "review_comment", "review_method", "reviewer", "reviewed_at",
        "business_approval_status", "source_check_status", "source_check_resolution",
        "source_check_evidence",
    ]
    available_review_columns = [column for column in review_columns if column in reviews]
    data = data.merge(reviews[available_review_columns], on=OBSERVATION_KEYS,
                      how="left", validate="one_to_one")
    data = data.merge(periods, on="reporting_period", validate="many_to_one")
    data = data.merge(products[["product_group", "product_group_label", "display_order"]],
                      on="product_group", validate="many_to_one")
    band_order = {band: index + 1 for index, band in enumerate(PERIOD_BAND_ORDER)}
    data["priority_band_sort_order"] = data.priority_band.map(band_order)
    data["has_current_signal"] = data.triggered_rule_count.gt(0)
    data["is_priority_review"] = data.priority_band.eq("priority_review")
    data["is_reviewed_priority"] = data.is_priority_review & data.review_disposition.notna()
    data["is_source_anomaly"] = data.review_disposition.eq(
        "source_anomaly_requires_business_review"
    )
    data["review_display_status"] = "not_required"
    data.loc[data.is_priority_review, "review_display_status"] = "priority_review_pending"
    data.loc[data.is_reviewed_priority, "review_display_status"] = "analytical_review_complete"
    data.loc[data.is_source_anomaly, "review_display_status"] = "source_anomaly_open"
    latest_period = periods.sort_values("period_end").reporting_period.iloc[-1]
    data["is_latest_reporting_period"] = data.reporting_period.eq(latest_period)
    data["methodology_notice"] = (
        "Analytical prioritisation only; not evidence of misconduct or customer harm. "
        "Pending business approval."
    )
    return data.sort_values(
        ["period_end", "priority_band_sort_order", "warning_score", "display_firm_name",
         "display_order"], ascending=[False, True, False, True, True]
    ).reset_index(drop=True)


def build_firm_period_dashboard(product: pd.DataFrame) -> pd.DataFrame:
    keys = ["firm_key", "reporting_period"]
    base = product.groupby(keys, as_index=False).agg(
        display_firm_name=("display_firm_name", "first"),
        resolved_frn=("resolved_frn", "first"), year=("year", "first"),
        half=("half", "first"), period_start=("period_start", "first"),
        period_end=("period_end", "first"),
        product_observation_count=("product_group", "size"),
        products_with_current_signal=("has_current_signal", "sum"),
        maximum_warning_score=("warning_score", "max"),
        total_triggered_rules=("triggered_rule_count", "sum"),
        total_persistent_rules=("persistent_rule_count", "sum"),
        source_anomaly_count=("is_source_anomaly", "sum"),
        is_latest_reporting_period=("is_latest_reporting_period", "first"),
    )
    for band in PERIOD_BAND_ORDER:
        counts = product.assign(_value=product.priority_band.eq(band)).groupby(keys)._value.sum()
        base[f"{band}_product_count"] = base.set_index(keys).index.map(counts).fillna(0).astype(int)
    priority_products = product[product.is_priority_review].groupby(keys).product_group_label.agg(
        lambda values: "|".join(sorted(set(values)))
    )
    base["priority_review_products"] = base.set_index(keys).index.map(priority_products).fillna("")
    base["has_priority_review_product"] = base.priority_review_product_count.gt(0)
    return base.sort_values(["period_end", "maximum_warning_score", "display_firm_name"],
                            ascending=[False, False, True]).reset_index(drop=True)


def build_rule_dashboard(indicators: pd.DataFrame,
                         product: pd.DataFrame) -> pd.DataFrame:
    context_columns = OBSERVATION_KEYS + [
        "product_group_label", "priority_band", "priority_band_sort_order",
        "warning_score", "coverage_status", "review_disposition",
        "review_display_status", "business_approval_status", "is_source_anomaly",
        "is_latest_reporting_period", "methodology_notice",
    ]
    available = [column for column in context_columns if column in product]
    data = indicators.merge(product[available], on=OBSERVATION_KEYS,
                            validate="many_to_one")
    data["rule_status"] = "not_triggered"
    data.loc[~data.eligible, "rule_status"] = "ineligible"
    data.loc[data.triggered, "rule_status"] = "triggered"
    data.loc[data.persistent_trigger, "rule_status"] = "triggered_persistent"
    return data.sort_values(
        ["reporting_period", "display_firm_name", "product_group", "triggered", "rule_id"],
        ascending=[False, True, True, False, True]
    ).reset_index(drop=True)


def build_metric_detail(fact: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    data = fact.merge(products[["product_group", "product_group_label"]],
                      on="product_group", how="left", validate="many_to_one")
    data["metric_display_value"] = data.metric_value
    data["source_cell"] = (data.source_sheet.astype(str) + "!R" +
                           data.source_row.astype(str) + "C" + data.source_column.astype(str))
    return data.sort_values(["reporting_period", "firm_key", "product_group", "metric_name"])


def data_dictionary() -> pd.DataFrame:
    rows = [
        ("dashboard_firm_product_period", "firm_key + reporting_period + source_reporting_period + product_group", "Primary trend, warning and review table; one observation per firm/product/window."),
        ("dashboard_firm_period", "firm_key + reporting_period", "Executive navigation table; product counts are pre-aggregated."),
        ("dashboard_warning_rule_detail", "observation grain + rule_id", "Explainable rule eligibility, evidence, trigger and persistence. Do not sum complaint metrics here."),
        ("dashboard_peer_benchmarks", "reporting_period + product_group", "Product-period medians and quartiles for reference lines."),
        ("dashboard_source_metric_detail", "fact_id", "Source-cell values and lineage; filter is_analysis_ready_value for numeric charts."),
    ]
    return pd.DataFrame(rows, columns=["table_name", "grain", "safe_use"])


def validate_reporting(tables: dict[str, pd.DataFrame], feature_rows: int,
                       rule_count: int) -> list[dict[str, str]]:
    product = tables["dashboard_firm_product_period"]
    rules = tables["dashboard_warning_rule_detail"]
    checks = {
        "firm_product_row_count": len(product) == feature_rows,
        "firm_product_grain_unique": not product.duplicated(OBSERVATION_KEYS).any(),
        "rule_row_count": len(rules) == feature_rows * rule_count,
        "rule_grain_unique": not rules.duplicated(OBSERVATION_KEYS + ["rule_id"]).any(),
        "firm_period_grain_unique": not tables["dashboard_firm_period"].duplicated(
            ["firm_key", "reporting_period"]
        ).any(),
        "all_priority_cases_reviewed": product.loc[
            product.is_priority_review, "review_disposition"
        ].notna().all(),
        "exactly_one_open_source_anomaly": product.is_source_anomaly.sum() == 1,
        "v2_methodology_only": product.methodology_id.eq(
            "fca_complaint_early_warning_v2_candidate"
        ).all(),
    }
    return [{"severity": "error", "rule": rule,
             "message": f"Dashboard reporting validation failed: {rule}"}
            for rule, passed in checks.items() if not passed]


def run_reporting_build(processed_dir: Path, output_dir: Path) -> dict[str, Any]:
    features = _read(processed_dir / "features/firm_product_period_features.csv")
    warnings = _read(processed_dir / "warnings_v2/firm_product_warning_summary.csv")
    indicators = _read(processed_dir / "warnings_v2/warning_indicators.csv")
    reviews = _read(Path("data/mappings/warning_v2_priority_review_decisions.csv"))
    periods = _read(processed_dir / "dim_reporting_period.csv")
    products = _read(processed_dir / "dim_product_group.csv")
    benchmarks = _read(processed_dir / "features/product_period_benchmarks.csv")
    fact = _read(processed_dir / "fact_firm_complaints.csv")
    product = build_firm_product_dashboard(features, warnings, reviews, periods, products)
    tables = {
        "dashboard_firm_product_period": product,
        "dashboard_firm_period": build_firm_period_dashboard(product),
        "dashboard_warning_rule_detail": build_rule_dashboard(indicators, product),
        "dashboard_peer_benchmarks": benchmarks.merge(
            products[["product_group", "product_group_label", "display_order"]],
            on="product_group", validate="many_to_one"
        ),
        "dashboard_source_metric_detail": build_metric_detail(fact, products),
        "dashboard_data_dictionary": data_dictionary(),
    }
    issues = validate_reporting(tables, len(features), indicators.rule_id.nunique())
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        output_dir / "dashboard_validation.csv", index=False
    )
    summary = {
        "methodology_id": "fca_complaint_early_warning_v2_candidate",
        "dashboard_status": "analytical_candidate_pending_business_review",
        "table_rows": {name: len(frame) for name, frame in tables.items()},
        "latest_reporting_period": periods.sort_values("period_end").reporting_period.iloc[-1],
        "priority_review_observations": int(product.is_priority_review.sum()),
        "priority_review_firms": int(product.loc[product.is_priority_review, "firm_key"].nunique()),
        "open_source_anomalies": int(product.is_source_anomaly.sum()),
        "validation_status": "failed" if issues else "passed",
        "validation_issues": issues,
    }
    (output_dir / "dashboard_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if issues:
        raise ValueError(f"Dashboard reporting validation failed: {issues}")
    return summary
