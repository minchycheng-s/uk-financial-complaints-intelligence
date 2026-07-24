"""Cross-period sheet and column schema comparisons."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import pandas as pd

from customer_harm.profiling.headers import normalise_text


def canonical_sheet_name(name: str) -> str:
    """Map observed FCA sheet-title variants to a stable comparison role."""
    text = normalise_text(name).replace("–", "-")
    rules = [
        (("context", "intermediation"), "context_intermediation"),
        (("context", "provision"), "context_provision"),
        (("joint reporter", "consumer credit"), "consumer_credit_joint_reporters"),
        (("joint reporter",), "main_return_joint_reporters"),
        (("trading name",), "trading_names"),
        (("consumer credit",), "consumer_credit"),
        (("upheld",), "percentage_upheld"),
    ]
    for terms, role in rules:
        if all(term in text for term in terms):
            return role
    if "3 day" in text and any(term in text for term in ("8", ">3", "after")):
        return "percentage_after_3_days_within_8_weeks"
    if "3 day" in text:
        return "percentage_within_3_days"
    if "opened" in text:
        return "opened"
    if "closed" in text:
        return "closed"
    if "note" in text:
        return "notes"
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def classify_sheet_type(canonical_sheet: str) -> str:
    """Assign a structural role that controls profiling, not business cleaning."""
    if canonical_sheet in {
        "opened", "closed", "percentage_within_3_days",
        "percentage_after_3_days_within_8_weeks", "percentage_upheld",
    }:
        return "metric_wide_table"
    if canonical_sheet == "consumer_credit":
        return "consumer_credit_metric_table"
    if canonical_sheet in {"context_intermediation", "context_provision"}:
        return "context_rate_table"
    if canonical_sheet == "trading_names":
        return "firm_alias_reference"
    if canonical_sheet in {"main_return_joint_reporters", "consumer_credit_joint_reporters"}:
        return "joint_reporter_reference"
    if canonical_sheet == "notes":
        return "product_reference"
    return "unclassified"


def _column_map(frame: pd.DataFrame, period: str, role: str) -> dict[str, dict[str, Any]]:
    subset = frame[(frame["reporting_period"] == period) & (frame["canonical_sheet"] == role)]
    return {
        row.normalised_column: {"name": row.column, "dtype": row.storage_dtype,
                                "semantic_type": row.semantic_type, "position": row.column_position,
                                "format": row.number_format_class,
                                "missing_percent": row.missing_percent}
        for row in subset.itertuples()
    }


def _rename_pairs(
    old_columns: dict[str, dict[str, Any]], new_columns: dict[str, dict[str, Any]],
    removed: set[str], added: set[str],
) -> list[tuple[float, str, str]]:
    """Suggest renames from text plus supporting position/type evidence."""
    pairs: list[tuple[float, str, str]] = []
    for old in removed:
        for new in added:
            text_similarity = SequenceMatcher(None, old, new).ratio()
            same_position = old_columns[old]["position"] == new_columns[new]["position"]
            same_semantic_type = old_columns[old]["semantic_type"] == new_columns[new]["semantic_type"]
            confidence = text_similarity * 0.7 + same_position * 0.2 + same_semantic_type * 0.1
            if confidence >= 0.72:
                pairs.append((confidence, old, new))
    selected: list[tuple[float, str, str]] = []
    used_old: set[str] = set()
    used_new: set[str] = set()
    for confidence, old, new in sorted(pairs, reverse=True):
        if old not in used_old and new not in used_new:
            selected.append((confidence, old, new))
            used_old.add(old)
            used_new.add(new)
    return selected


def compare_schemas(columns: pd.DataFrame, sheets: pd.DataFrame) -> pd.DataFrame:
    """Describe cross-period changes with explicit evidence and review status."""
    output_columns = [
        "previous_period", "current_period", "canonical_sheet", "previous_sheet", "current_sheet",
        "change_type", "previous_column", "current_column", "previous_position", "current_position",
        "previous_storage_dtype", "current_storage_dtype", "previous_semantic_type",
        "current_semantic_type", "previous_format", "current_format", "previous_value",
        "current_value", "confidence", "evidence", "review_status",
    ]
    if sheets.empty or columns.empty:
        return pd.DataFrame(columns=output_columns)
    records: list[dict[str, Any]] = []
    def add(base: dict[str, Any], change_type: str, old: dict[str, Any] | None = None,
            new: dict[str, Any] | None = None, previous_value: Any = None,
            current_value: Any = None, confidence: float | None = None,
            evidence: str = "") -> None:
        review_status = "manual_review" if change_type in {
            "possible_column_renamed", "semantic_type_changed", "number_format_changed",
            "header_position_changed", "sheet_added", "sheet_removed", "column_added", "column_removed",
        } else "informational"
        records.append({
            **base, "change_type": change_type,
            "previous_column": old.get("name") if old else None,
            "current_column": new.get("name") if new else None,
            "previous_position": old.get("position") if old else None,
            "current_position": new.get("position") if new else None,
            "previous_storage_dtype": old.get("dtype") if old else None,
            "current_storage_dtype": new.get("dtype") if new else None,
            "previous_semantic_type": old.get("semantic_type") if old else None,
            "current_semantic_type": new.get("semantic_type") if new else None,
            "previous_format": old.get("format") if old else None,
            "current_format": new.get("format") if new else None,
            "previous_value": previous_value, "current_value": current_value,
            "confidence": confidence, "evidence": evidence, "review_status": review_status,
        })
    periods = sorted(sheets["reporting_period"].unique())
    for previous, current in zip(periods, periods[1:]):
        old_sheets = set(sheets.loc[sheets.reporting_period == previous, "canonical_sheet"])
        new_sheets = set(sheets.loc[sheets.reporting_period == current, "canonical_sheet"])
        for role in sorted(old_sheets | new_sheets):
            old_sheet_rows = sheets[(sheets.reporting_period == previous) & (sheets.canonical_sheet == role)]
            new_sheet_rows = sheets[(sheets.reporting_period == current) & (sheets.canonical_sheet == role)]
            previous_sheet = old_sheet_rows.iloc[0].sheet if not old_sheet_rows.empty else None
            current_sheet = new_sheet_rows.iloc[0].sheet if not new_sheet_rows.empty else None
            base = {"previous_period": previous, "current_period": current,
                    "canonical_sheet": role, "previous_sheet": previous_sheet,
                    "current_sheet": current_sheet}
            if role not in old_sheets or role not in new_sheets:
                change = "sheet_added" if role in new_sheets else "sheet_removed"
                add(base, change, previous_value=previous_sheet, current_value=current_sheet,
                    evidence=f"Canonical sheet role {role!r} is present in only one period.")
                continue
            old_sheet = old_sheet_rows.iloc[0]
            new_sheet = new_sheet_rows.iloc[0]
            if old_sheet.header_row != new_sheet.header_row:
                add(base, "header_position_changed", previous_value=old_sheet.header_row,
                    current_value=new_sheet.header_row,
                    evidence="Selected header row differs between consecutive periods.")
            old = _column_map(columns, previous, role)
            new = _column_map(columns, current, role)
            removed, added = set(old) - set(new), set(new) - set(old)
            renames = _rename_pairs(old, new, removed, added)
            for rename_confidence, old_name, new_name in renames:
                similarity = round(rename_confidence, 4)
                add(base, "possible_column_renamed", old[old_name], new[new_name],
                    old[old_name]["name"], new[new_name]["name"], similarity,
                    f"Composite confidence {similarity} uses header text, position and semantic type; meaning is not assumed equivalent.")
                removed.remove(old_name)
                added.remove(new_name)
            for name in sorted(removed):
                add(base, "column_removed", old[name], previous_value=old[name]["name"],
                    evidence="Normalised header is absent from the current period.")
            for name in sorted(added):
                add(base, "column_added", new=new[name], current_value=new[name]["name"],
                    evidence="Normalised header is absent from the previous period.")
            for name in sorted(set(old) & set(new)):
                if old[name]["position"] != new[name]["position"]:
                    add(base, "column_order_changed", old[name], new[name], old[name]["position"],
                        new[name]["position"], evidence="The same normalised header moved position.")
                if old[name]["semantic_type"] != new[name]["semantic_type"]:
                    add(base, "semantic_type_changed", old[name], new[name], old[name]["semantic_type"],
                        new[name]["semantic_type"], evidence="Business-oriented value classification changed.")
                if old[name]["dtype"] != new[name]["dtype"]:
                    add(base, "storage_dtype_changed", old[name], new[name], old[name]["dtype"],
                        new[name]["dtype"], evidence="Pandas storage dtype changed; source meaning may be unchanged.")
                if old[name]["format"] != new[name]["format"]:
                    add(base, "number_format_changed", old[name], new[name], old[name]["format"],
                        new[name]["format"], evidence="Excel data-cell number-format class changed.")
    return pd.DataFrame(records, columns=output_columns)
