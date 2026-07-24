"""Create a Tableau assembly pack and dependency-free dashboard preview."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_presentation_tables(product: pd.DataFrame,
                              firm_period: pd.DataFrame) -> dict[str, pd.DataFrame]:
    latest_period = product.loc[product.is_latest_reporting_period, "reporting_period"].iloc[0]
    latest = product[product.reporting_period.eq(latest_period)].copy()
    priority = product[product.is_priority_review].copy()
    kpis = pd.DataFrame([{
        "latest_reporting_period": latest_period,
        "latest_firm_count": latest.firm_key.nunique(),
        "latest_firm_product_observations": len(latest),
        "latest_priority_observations": int(latest.is_priority_review.sum()),
        "latest_priority_firms": latest.loc[latest.is_priority_review, "firm_key"].nunique(),
        "latest_insufficient_data_observations": int(latest.priority_band.eq("insufficient_data").sum()),
        "all_period_open_source_anomalies": int(product.is_source_anomaly.sum()),
        "methodology_id": product.methodology_id.iloc[0],
        "methodology_status": product.methodology_status.iloc[0],
    }])
    trend = product.groupby("reporting_period", as_index=False).agg(
        firm_count=("firm_key", "nunique"), observation_count=("product_group", "size"),
        priority_review=("priority_band", lambda x: int(x.eq("priority_review").sum())),
        review=("priority_band", lambda x: int(x.eq("review").sum())),
        monitor=("priority_band", lambda x: int(x.eq("monitor").sum())),
        no_current_signal=("priority_band", lambda x: int(x.eq("no_current_signal").sum())),
        insufficient_data=("priority_band", lambda x: int(x.eq("insufficient_data").sum())),
    ).merge(product[["reporting_period", "period_end"]].drop_duplicates(),
            on="reporting_period", validate="one_to_one").sort_values("period_end")
    product_snapshot = latest.groupby(
        ["product_group", "product_group_label", "display_order"], as_index=False
    ).agg(
        firm_observations=("firm_key", "size"),
        priority_review=("priority_band", lambda x: int(x.eq("priority_review").sum())),
        review=("priority_band", lambda x: int(x.eq("review").sum())),
        monitor=("priority_band", lambda x: int(x.eq("monitor").sum())),
        insufficient_data=("priority_band", lambda x: int(x.eq("insufficient_data").sum())),
    ).sort_values("display_order")
    queue_columns = [
        "firm_key", "display_firm_name", "resolved_frn", "reporting_period",
        "source_reporting_period", "product_group", "product_group_label", "warning_score",
        "triggered_rule_count", "persistent_rule_count", "triggered_rule_ids",
        "independent_signal_family_count", "triggered_signal_families", "review_disposition",
        "review_flags", "review_comment", "source_check_status", "source_check_resolution",
        "is_source_anomaly", "business_approval_status",
    ]
    queue = priority[[column for column in queue_columns if column in priority]].copy()
    disposition_order = {
        "source_anomaly_requires_business_review": 1,
        "retain_priority_review": 2,
        "retain_priority_review_with_statistical_caveat": 3,
        "retain_priority_review_with_definition_caveat": 4,
        "retain_priority_review_borderline": 5,
    }
    queue["review_queue_sort_order"] = queue.review_disposition.map(disposition_order)
    queue = queue.sort_values(
        ["review_queue_sort_order", "warning_score", "reporting_period", "display_firm_name"],
        ascending=[True, False, False, True]
    )
    quality = pd.DataFrame([
        {"quality_measure": "Open source anomaly", "observation_count": int(product.is_source_anomaly.sum()),
         "interpretation": "Confirmed source inconsistency requiring business treatment."},
        {"quality_measure": "Statistical caveat", "observation_count": int(
            priority.review_disposition.eq("retain_priority_review_with_statistical_caveat").sum()),
         "interpretation": "Source confirmed; percentage evidence has 20–49 closed complaints."},
        {"quality_measure": "Definition caveat", "observation_count": int(
            priority.review_disposition.eq("retain_priority_review_with_definition_caveat").sum()),
         "interpretation": "Source confirmed; FCA context denominator definition is required."},
        {"quality_measure": "Insufficient data", "observation_count": int(
            product.priority_band.eq("insufficient_data").sum()),
         "interpretation": "Too few eligible rules for classification; not a low-risk result."},
        {"quality_measure": "Unresolved firm identity", "observation_count": int(
            product.identity_match_status.ne("matched").sum()),
         "interpretation": "Stable name key retained; FRN not assigned."},
    ])
    return {"executive_kpis": kpis, "executive_period_trend": trend,
            "executive_product_snapshot": product_snapshot, "priority_review_queue": queue,
            "data_quality_summary": quality}


def workbook_manifest() -> dict[str, Any]:
    notice = ("Analytical prioritisation only; not evidence of misconduct or customer harm. "
              "Pending business approval.")
    return {
        "workbook_name": "UK Financial Complaints and Customer Harm Intelligence",
        "status": "tableau_assembly_pack",
        "notice": notice,
        "data_model": {"relationship_mode": "logical_relationships_not_physical_flattening",
            "primary_source": "data/processed/reporting/dashboard_firm_product_period.csv",
            "relationship_contract": "See tableau/dashboard_requirements.md"},
        "dashboards": [
            {"name": "Executive Overview", "size": "1366x768",
             "sources": ["executive_kpis", "executive_period_trend", "executive_product_snapshot"],
             "filters": ["reporting_period", "product_group_label"],
             "actions": ["Firm selection opens Priority Review Queue"]},
            {"name": "Priority Review Queue", "size": "1366x768",
             "sources": ["priority_review_queue", "dashboard_firm_product_period"],
             "filters": ["reporting_period", "product_group_label", "review_disposition",
                         "display_firm_name"],
             "default_sort": "review_queue_sort_order asc, warning_score desc"},
            {"name": "Firm and Product Explorer", "size": "1366x768",
             "sources": ["dashboard_firm_product_period", "dashboard_peer_benchmarks"],
             "filters": ["display_firm_name", "product_group_label", "reporting_period"]},
            {"name": "Rule Explanation", "size": "1366x768",
             "sources": ["dashboard_warning_rule_detail"],
             "filters": ["display_firm_name", "product_group_label", "reporting_period",
                         "rule_status"]},
            {"name": "Data Quality and Coverage", "size": "1366x768",
             "sources": ["data_quality_summary", "dashboard_source_metric_detail"],
             "filters": ["reporting_period", "product_group_label", "identity_match_status"]},
        ],
        "prohibited": ["sum percentages", "sum context rates", "sum rule rows",
                       "convert insufficient_data to zero", "infer misconduct from a band"],
    }


def _bars_svg(trend: pd.DataFrame) -> str:
    width, height, margin = 780, 260, 38
    maximum = max(1, int(trend[["priority_review", "review", "monitor"]].sum(axis=1).max()))
    bar_width = (width - margin * 2) / len(trend) * .64
    blocks = []
    colours = [("priority_review", "#9f2d3f"), ("review", "#d77b24"), ("monitor", "#d5ad3b")]
    for index, row in enumerate(trend.itertuples(index=False)):
        x = margin + index * ((width - margin * 2) / len(trend)) + 8
        y = height - 34
        for field, colour in colours:
            value = getattr(row, field)
            segment = value / maximum * (height - 72)
            y -= segment
            blocks.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
                          f'height="{segment:.1f}" fill="{colour}"><title>{field}: {value}</title></rect>')
        blocks.append(f'<text x="{x + bar_width/2:.1f}" y="{height-14}" text-anchor="middle" '
                      f'class="axis">{html.escape(row.reporting_period)}</text>')
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Warning observations by period">' + "".join(blocks) + "</svg>"


def render_preview(tables: dict[str, pd.DataFrame], manifest: dict[str, Any]) -> str:
    k = tables["executive_kpis"].iloc[0]
    trend = tables["executive_period_trend"]
    products = tables["executive_product_snapshot"]
    queue = tables["priority_review_queue"]
    cards = [("Firms", int(k.latest_firm_count)), ("Priority firms", int(k.latest_priority_firms)),
             ("Priority observations", int(k.latest_priority_observations)),
             ("Insufficient data", int(k.latest_insufficient_data_observations)),
             ("Open source anomalies", int(k.all_period_open_source_anomalies))]
    card_html = "".join(f'<div class="card"><span>{html.escape(label)}</span><strong>{value:,}</strong></div>'
                        for label, value in cards)
    product_rows = "".join(
        f'<tr><td>{html.escape(row.product_group_label)}</td><td>{row.firm_observations}</td>'
        f'<td>{row.priority_review}</td><td>{row.review}</td><td>{row.monitor}</td></tr>'
        for row in products.itertuples(index=False))
    queue_rows = "".join(
        f'<tr><td>{html.escape(str(row.display_firm_name))}</td><td>{html.escape(str(row.product_group_label))}</td>'
        f'<td>{html.escape(str(row.reporting_period))}</td><td>{int(row.warning_score)}</td>'
        f'<td>{html.escape(str(row.review_disposition).replace("_", " "))}</td></tr>'
        for row in queue.head(12).itertuples(index=False))
    notice = html.escape(manifest["notice"])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Complaints intelligence preview</title>
<style>body{{margin:0;background:#f3f5f7;color:#17212b;font:14px Arial,sans-serif}}header{{background:#18354a;color:white;padding:22px 32px}}header h1{{margin:0 0 6px}}.notice{{background:#fff3cd;color:#654f00;padding:10px 32px}}main{{padding:22px 32px}}.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.card,.panel{{background:white;border:1px solid #dbe1e6;border-radius:7px;padding:16px}}.card span{{display:block;color:#596875}}.card strong{{display:block;font-size:28px;margin-top:8px}}.grid{{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;margin-top:16px}}h2{{font-size:18px;margin:0 0 12px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #e5e9ed;text-align:left}}th{{color:#53616d;font-size:12px;text-transform:uppercase}}.axis{{font-size:11px;fill:#596875}}.legend span{{margin-right:18px}}.p{{color:#9f2d3f}}.r{{color:#d77b24}}.m{{color:#9a7712}}footer{{padding:18px 32px;color:#65727d}}</style></head>
<body><header><h1>UK Financial Complaints Intelligence</h1><div>Executive Overview · {html.escape(str(k.latest_reporting_period))}</div></header>
<div class="notice">{notice}</div><main><section class="cards">{card_html}</section>
<section class="grid"><div class="panel"><h2>Warning observations by reporting period</h2><div class="legend"><span class="p">■ Priority</span><span class="r">■ Review</span><span class="m">■ Monitor</span></div>{_bars_svg(trend)}</div>
<div class="panel"><h2>Latest product snapshot</h2><table><thead><tr><th>Product</th><th>Firms</th><th>Priority</th><th>Review</th><th>Monitor</th></tr></thead><tbody>{product_rows}</tbody></table></div></section>
<section class="panel" style="margin-top:16px"><h2>Priority review queue — strongest and caveated cases</h2><table><thead><tr><th>Firm</th><th>Product</th><th>Period</th><th>Score</th><th>Disposition</th></tr></thead><tbody>{queue_rows}</tbody></table></section></main>
<footer>Preview generated from validated reporting tables. Assemble the five production dashboards in Tableau Desktop using workbook_manifest.json.</footer></body></html>'''


def validate_pack(tables: dict[str, pd.DataFrame]) -> list[dict[str, str]]:
    kpis = tables["executive_kpis"].iloc[0]
    queue = tables["priority_review_queue"]
    checks = {
        "latest_period_present": bool(kpis.latest_reporting_period),
        "priority_queue_has_135_rows": len(queue) == 135,
        "priority_queue_reviews_complete": queue.review_disposition.notna().all(),
        "single_open_source_anomaly": int(kpis.all_period_open_source_anomalies) == 1,
        "period_trend_has_ten_periods": len(tables["executive_period_trend"]) == 10,
        "product_snapshot_has_six_products": len(tables["executive_product_snapshot"]) == 6,
    }
    return [{"severity": "error", "rule": rule,
             "message": f"Tableau delivery-pack validation failed: {rule}"}
            for rule, passed in checks.items() if not passed]


def run_tableau_pack(reporting_dir: Path, tableau_dir: Path) -> dict[str, Any]:
    product = pd.read_csv(reporting_dir / "dashboard_firm_product_period.csv", low_memory=False)
    firm_period = pd.read_csv(reporting_dir / "dashboard_firm_period.csv", low_memory=False)
    tables = build_presentation_tables(product, firm_period)
    manifest = workbook_manifest()
    issues = validate_pack(tables)
    presentation_dir = reporting_dir / "presentation"
    presentation_dir.mkdir(parents=True, exist_ok=True)
    tableau_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(presentation_dir / f"{name}.csv", index=False)
    (tableau_dir / "workbook_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (tableau_dir / "dashboard_preview.html").write_text(
        render_preview(tables, manifest), encoding="utf-8"
    )
    pd.DataFrame(issues, columns=["severity", "rule", "message"]).to_csv(
        presentation_dir / "tableau_pack_validation.csv", index=False
    )
    summary = {"status": "failed" if issues else "passed",
               "native_tableau_workbook_created": False,
               "native_workbook_reason": "Tableau Desktop/SDK unavailable in build environment",
               "presentation_table_rows": {name: len(frame) for name, frame in tables.items()},
               "dashboard_count": len(manifest["dashboards"]), "validation_issues": issues}
    (presentation_dir / "tableau_pack_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if issues:
        raise ValueError(f"Tableau delivery-pack validation failed: {issues}")
    return summary
