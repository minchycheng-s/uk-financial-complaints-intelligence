"""Turn profiling evidence into an explicit, human-controlled review gate."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

APPROVED_DECISIONS = {"approved", "approved_with_conditions"}
DECISION_COLUMNS = ["review_item_id", "decision", "reviewer", "reviewed_at", "reviewer_comment"]


def build_review_register(frames: dict[str, pd.DataFrame], decisions_path: Path) -> pd.DataFrame:
    """Build stable review items and merge separately maintained human decisions."""
    items: list[dict[str, Any]] = []

    def add(category: str, scope: str, issue: str, evidence_file: str, severity: str,
            blocks_extraction: bool, recommended_action: str, proposed_decision: str) -> None:
        stable_text = f"{category}|{scope}|{issue}"
        item_id = f"REV-{hashlib.sha256(stable_text.encode('utf-8')).hexdigest()[:10].upper()}"
        items.append({
            "review_item_id": item_id, "category": category, "scope": scope,
            "issue": issue, "evidence_file": evidence_file, "severity": severity,
            "blocks_extraction": blocks_extraction, "recommended_action": recommended_action,
            "proposed_decision": proposed_decision,
        })

    inventory = frames["workbook_inventory"]
    if inventory.processing_status.eq("success").all():
        add("source_coverage", "all periods", "All expected workbooks processed successfully.",
            "workbook_inventory.csv", "info", False, "Retain hashes and exact-period validation.",
            "approve")

    warnings = frames["profiling_warnings"]
    warning_rules = {
        "FORMULA_WITHOUT_CACHED_VALUE": ("formula_values", "high", True,
            "Inspect formula text or recalculate in a controlled Excel-compatible process before extracting affected measures."),
        "EXCEL_ERROR_VALUES": ("excel_errors", "high", True,
            "Inspect the affected error cells and define whether they are invalid, unavailable or derivable."),
        "MIXED_VALUE_TYPES": ("mixed_column", "high", True,
            "Determine the meaning of the text value and unnamed column before extraction."),
        "CANDIDATE_MISSING_MARKERS": ("missing_markers", "medium", True,
            "Confirm the marker meaning and document its future missing-value category."),
        "EXCESSIVE_FORMATTED_RANGE": ("formatted_range", "low", False,
            "Accept value-based bounds while retaining the source-range warning."),
        "HEADER_NOT_FIRST_ROW": ("header_selection", "low", False,
            "Confirm row 9 as the Notes taxonomy header."),
        "NON_STANDARD_FILENAME": ("source_naming", "low", False,
            "Keep immutable raw names and use manifest source IDs."),
        "LOW_HEADER_CONFIDENCE": ("header_selection", "high", True,
            "Manually select or configure the correct header row."),
    }
    for row in warnings.itertuples():
        if row.warning_code not in warning_rules:
            continue
        category, severity, blocking, action = warning_rules[row.warning_code]
        scope = " / ".join(str(value) for value in (row.reporting_period, row.sheet) if pd.notna(value))
        add(category, scope or "workbook", row.message, "profiling_warnings.csv",
            severity, blocking, action, "approve_with_documented_rule" if not blocking else "investigate")

    schema = frames["schema_comparison"]
    for change_type in ["possible_column_renamed", "semantic_type_changed", "sheet_added", "sheet_removed"]:
        count = int(schema.change_type.eq(change_type).sum())
        if count:
            add("schema_changes", change_type, f"{count} {change_type} records require interpretation.",
                "schema_comparison.csv", "high" if change_type != "sheet_added" else "medium", True,
                "Review evidence and approve canonical mappings or period-specific exceptions.", "review_each_mapping")

    product_changes = frames["product_group_comparison"]
    measurement_count = int(product_changes.change_type.eq("measurement_basis_changed").sum())
    if measurement_count:
        add("product_definitions", "context sheets",
            f"{measurement_count} measurement-basis header changes appear across periods.",
            "product_group_comparison.csv", "high", True,
            "Confirm whether omitted per-1,000 wording changes meaning or presentation only.",
            "document_period_specific_definition")

    taxonomy = frames["product_taxonomy_inventory"]
    taxonomy_groups = set(taxonomy.inherited_product_group.dropna())
    if "insurance & protection" in taxonomy_groups:
        add("product_definitions", "insurance product group",
            "Notes uses 'Insurance & protection' while metric sheets use 'Insurance & pure protection'.",
            "product_taxonomy_inventory.csv", "high", True,
            "Approve or reject an explicit reviewed mapping; preserve both raw labels.", "review_mapping")

    taxonomy_comparison = frames["product_taxonomy_comparison"]
    unavailable = int(taxonomy_comparison.change_type.eq("product_reference_unavailable").sum())
    if unavailable:
        add("reference_availability", "Notes taxonomy",
            f"{unavailable} period transitions lack Notes reference evidence.",
            "product_taxonomy_comparison.csv", "medium", False,
            "Use the latest prior taxonomy only if explicitly approved and versioned.", "document_limitation")

    definition_changes = frames["reporting_definition_comparison"]
    text_changes = int(definition_changes.change_type.eq("definition_text_changed").sum())
    if text_changes:
        add("reporting_definitions", "Notes narrative",
            f"{text_changes} reporting-definition text changes were detected.",
            "reporting_definition_comparison.csv", "medium", False,
            "Review publication dates and stale period wording; record source text verbatim.", "document_source_wording")

    register = pd.DataFrame(items)
    decisions = _read_decisions(decisions_path)
    register = register.merge(decisions, on="review_item_id", how="left")
    register["decision_status"] = register["decision"].fillna("").map(
        lambda value: "approved" if value in APPROVED_DECISIONS
        else "rejected" if value == "rejected" else "pending_review"
    )
    return register


def review_gate_summary(register: pd.DataFrame) -> dict[str, Any]:
    """Calculate sign-off status without inferring human approval."""
    blocking = register[register.blocks_extraction.astype(bool)]
    rejected = blocking.decision_status.eq("rejected").sum()
    pending = blocking.decision_status.eq("pending_review").sum()
    status = "rejected" if rejected else "awaiting_manual_review" if pending else "approved"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profiling_review_status": status,
        "total_review_items": len(register),
        "blocking_review_items": len(blocking),
        "pending_blocking_items": int(pending),
        "rejected_blocking_items": int(rejected),
        "approved_blocking_items": int(blocking.decision_status.eq("approved").sum()),
        "extraction_authorised": status == "approved",
        "decision_source": "data/mappings/profiling_review_decisions.csv",
    }


def render_review_report(register: pd.DataFrame, gate: dict[str, Any]) -> str:
    """Render a concise reproducible review report for analysts and reviewers."""
    lines = [
        "# Workbook profiling review report", "",
        f"Review status: **{gate['profiling_review_status']}**", "",
        f"Extraction authorised: **{gate['extraction_authorised']}**", "",
        "This report is generated from profiling evidence. Only decisions recorded in "
        "`data/mappings/profiling_review_decisions.csv` count as human approval.", "",
        "## Review items", "",
        "| ID | Category | Scope | Severity | Blocks extraction | Status | Recommended action |",
        "|---|---|---|---|---:|---|---|",
    ]
    for row in register.itertuples():
        clean = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row.review_item_id} | {clean(row.category)} | {clean(row.scope)} | "
            f"{row.severity} | {bool(row.blocks_extraction)} | {row.decision_status} | "
            f"{clean(row.recommended_action)} |"
        )
    lines.extend(["", "## Gate rule", "",
                  "Profiling remains `awaiting_manual_review` until every blocking item has an "
                  "`approved` or `approved_with_conditions` decision with reviewer metadata.", ""])
    return "\n".join(lines)


def render_extraction_readiness(register: pd.DataFrame, gate: dict[str, Any]) -> str:
    """Document what is structurally understood and what remains blocked."""
    pending = register[(register.blocks_extraction.astype(bool)) &
                       (register.decision_status != "approved")]
    lines = [
        "# FCA extraction readiness", "",
        f"Current gate: **{gate['profiling_review_status']}**", "",
        "## Provisionally understood structures", "",
        "- Ten half-year workbooks and all 116 sheets are inventoried with immutable hashes.",
        "- Header positions and structural sheet types are profiled.",
        "- Firm metrics, context rates, firm aliases, joint reporters and Notes taxonomy are separated.",
        "- Product groups, detailed products, definitions, value markers, formulas and formats are inventoried.",
        "", "## Extraction blockers", "",
    ]
    if pending.empty:
        lines.append("No blocking review items remain. Extraction may proceed under recorded decisions.")
    else:
        for row in pending.itertuples():
            lines.append(f"- `{row.review_item_id}` — {row.scope}: {row.recommended_action}")
    lines.extend(["", "No cleaning, combination or canonical mapping is authorised while the gate is not approved.", ""])
    return "\n".join(lines)


def _read_decisions(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=DECISION_COLUMNS)
    decisions = pd.read_csv(path, dtype=str).fillna("")
    missing = set(DECISION_COLUMNS) - set(decisions.columns)
    if missing:
        raise ValueError(f"Review decisions file is missing columns: {sorted(missing)}")
    invalid = set(decisions.decision) - APPROVED_DECISIONS - {"rejected", ""}
    if invalid:
        raise ValueError(f"Invalid review decisions: {sorted(invalid)}")
    if decisions.review_item_id.duplicated().any():
        raise ValueError("Review decisions contain duplicate review_item_id values.")
    approved = decisions.decision.isin(APPROVED_DECISIONS)
    if (approved & ((decisions.reviewer == "") | (decisions.reviewed_at == ""))).any():
        raise ValueError("Approved decisions require reviewer and reviewed_at values.")
    return decisions[DECISION_COLUMNS]
