"""Conservative, auditable firm-name to FRN resolution."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


def normalise_firm_name(value: object) -> str:
    """Normalise case and whitespace without deleting meaningful punctuation."""
    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    return re.sub(r"\s+", " ", text)


def build_firm_crosswalk(metrics: pd.DataFrame, aliases: pd.DataFrame) -> pd.DataFrame:
    """Resolve distinct metric firm observations using unique exact legal-name evidence."""
    required_metrics = {"reporting_period", "firm_name"}
    required_aliases = {"reporting_period", "firm_name", "frn"}
    if not required_metrics <= set(metrics.columns):
        raise ValueError(f"Metrics lack columns: {sorted(required_metrics - set(metrics.columns))}")
    if not required_aliases <= set(aliases.columns):
        raise ValueError(f"Aliases lack columns: {sorted(required_aliases - set(aliases.columns))}")

    observed = metrics[["reporting_period", "firm_name"]].drop_duplicates().copy()
    observed["normalised_firm_name"] = observed.firm_name.map(normalise_firm_name)
    reference = aliases[aliases.frn.fillna("").astype(str).str.strip().ne("")][
        ["reporting_period", "firm_name", "frn"]
    ].drop_duplicates().copy()
    reference["frn"] = reference.frn.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    reference["normalised_firm_name"] = reference.firm_name.map(normalise_firm_name)

    records: list[dict[str, Any]] = []
    grouped = {key: group for key, group in reference.groupby("normalised_firm_name", sort=False)}
    for row in observed.itertuples(index=False):
        evidence = grouped.get(row.normalised_firm_name)
        base = {"reporting_period": row.reporting_period, "firm_name": row.firm_name,
                "normalised_firm_name": row.normalised_firm_name}
        if evidence is None or evidence.empty:
            records.append({**base, "resolved_frn": "", "match_status": "unmatched",
                            "match_method": "no_exact_legal_name_reference", "match_confidence": "none",
                            "candidate_frn_count": 0,
                            "candidate_frns": "", "evidence_periods": "", "evidence_rows": 0})
            continue
        frns = sorted(evidence.frn.unique())
        periods = sorted(evidence.reporting_period.unique())
        if len(frns) > 1:
            records.append({**base, "resolved_frn": "", "match_status": "ambiguous",
                            "match_method": "exact_name_multiple_frns", "match_confidence": "none",
                            "candidate_frn_count": len(frns),
                            "candidate_frns": "|".join(frns), "evidence_periods": "|".join(periods),
                            "evidence_rows": len(evidence)})
            continue
        same_period = row.reporting_period in set(evidence.reporting_period)
        records.append({**base, "resolved_frn": frns[0], "match_status": "matched",
                        "match_method": "exact_name_same_period" if same_period else "exact_name_global_unique",
                        "match_confidence": "high" if same_period else "medium",
                        "candidate_frn_count": 1, "candidate_frns": frns[0],
                        "evidence_periods": "|".join(periods), "evidence_rows": len(evidence)})
    columns = ["reporting_period", "firm_name", "normalised_firm_name", "resolved_frn",
               "match_status", "match_method", "match_confidence", "candidate_frn_count", "candidate_frns",
               "evidence_periods", "evidence_rows"]
    return pd.DataFrame(records, columns=columns).sort_values(
        ["reporting_period", "normalised_firm_name"]
    ).reset_index(drop=True)


def enrich_metrics(metrics: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Add resolution fields without replacing source FRN or changing row count."""
    fields = ["reporting_period", "firm_name", "resolved_frn", "match_status", "match_method",
              "match_confidence"]
    if crosswalk[["reporting_period", "firm_name"]].duplicated().any():
        raise ValueError("Firm crosswalk is not unique by reporting period and firm name.")
    enriched = metrics.merge(crosswalk[fields], on=["reporting_period", "firm_name"], how="left",
                             validate="many_to_one")
    if len(enriched) != len(metrics):
        raise ValueError("Firm resolution changed the metric row count.")
    if enriched.match_status.isna().any():
        raise ValueError("Some metric rows have no firm resolution status.")
    return enriched


def run_firm_resolution(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    metrics_path = input_dir / "complaint_metrics.csv"
    aliases_path = input_dir / "firm_aliases.csv"
    if not metrics_path.exists() or not aliases_path.exists():
        raise FileNotFoundError("Extracted complaint_metrics.csv and firm_aliases.csv are required.")
    metrics = pd.read_csv(metrics_path, dtype={"frn": str}, low_memory=False)
    aliases = pd.read_csv(aliases_path, dtype={"frn": str}, low_memory=False).fillna("")
    crosswalk = build_firm_crosswalk(metrics, aliases)
    enriched = enrich_metrics(metrics, crosswalk)
    output_dir.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(output_dir / "firm_identity_crosswalk.csv", index=False)
    enriched.to_csv(output_dir / "complaint_metrics_resolved.csv", index=False)
    crosswalk[crosswalk.match_status.eq("unmatched")].to_csv(
        output_dir / "unmatched_firms.csv", index=False
    )
    crosswalk[crosswalk.match_status.eq("ambiguous")].to_csv(
        output_dir / "ambiguous_firms.csv", index=False
    )
    status_counts = crosswalk.match_status.value_counts().to_dict()
    method_counts = crosswalk.match_method.value_counts().to_dict()
    summary = {
        "distinct_period_firm_pairs": len(crosswalk),
        "metric_rows_input": len(metrics),
        "metric_rows_output": len(enriched),
        "row_count_preserved": len(metrics) == len(enriched),
        "match_status_counts": status_counts,
        "match_method_counts": method_counts,
        "matched_pair_rate": round(status_counts.get("matched", 0) / len(crosswalk), 6) if len(crosswalk) else 0,
        "rules": [
            "Only exact case-and-whitespace-normalised legal firm names are matched.",
            "An FRN is assigned only when all reference evidence for that name has one unique FRN.",
            "Source FRNs are preserved; resolved_frn is a separate derived field.",
            "Unmatched and ambiguous names are never guessed.",
        ],
    }
    import json
    (output_dir / "firm_resolution_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary
