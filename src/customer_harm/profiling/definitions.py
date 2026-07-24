"""Profile product labels, Notes taxonomies and publication definitions."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

import pandas as pd

from customer_harm.profiling.headers import normalise_text

PRODUCT_GROUPS = {
    "banking and credit cards",
    "decumulation & pensions",
    "home finance",
    "insurance & pure protection",
    "investments",
}
FOOTNOTE_PATTERN = re.compile(r"\s*\(([a-z])\)\s*$", re.IGNORECASE)
MEASUREMENT_PATTERN = re.compile(r"\s*\((per\s+1,?000.+)\)\s*$", re.IGNORECASE)


def normalise_product_group(value: Any) -> tuple[str, str | None, str | None]:
    """Separate a product group from source footnotes and measurement wording."""
    text = re.sub(r"\s+", " ", str(value).strip())
    footnote_match = FOOTNOTE_PATTERN.search(text)
    footnote = footnote_match.group(1).casefold() if footnote_match else None
    without_footnote = FOOTNOTE_PATTERN.sub("", text).strip()
    measurement_match = MEASUREMENT_PATTERN.search(without_footnote)
    measurement = measurement_match.group(1).strip() if measurement_match else None
    base = MEASUREMENT_PATTERN.sub("", without_footnote).strip()
    return normalise_text(base), measurement, footnote


def extract_notes_content(
    matrix: list[list[Any]],
    header_index: int,
    source: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract a review taxonomy and narrative definitions while preserving raw values."""
    taxonomy: list[dict[str, Any]] = []
    definitions: list[dict[str, Any]] = []
    current_group: str | None = None
    current_section = "preamble"
    section_sequence: dict[str, int] = {}

    for row_index, row in enumerate(matrix[:header_index], 1):
        values = [str(value).strip() for value in row if value is not None and str(value).strip()]
        if not values:
            continue
        text = " | ".join(values)
        if len(text) <= 100:
            current_section = re.sub(r"[^a-z0-9]+", "_", normalise_text(text)).strip("_")
            record_type = "heading"
            sequence = 0
        else:
            record_type = "narrative"
            section_sequence[current_section] = section_sequence.get(current_section, 0) + 1
            sequence = section_sequence[current_section]
        key = current_section if record_type == "heading" else f"{current_section}__{sequence}"
        definitions.append({**source, "source_row_number": row_index, "definition_key": key,
                            "definition_type": record_type, "section": current_section,
                            "definition_text": text, "definition_text_hash": _text_hash(text)})

    for row_index, row in enumerate(matrix[header_index + 1 :], header_index + 2):
        raw_group = row[0] if len(row) > 0 else None
        raw_product = row[1] if len(row) > 1 else None
        group_text = str(raw_group).strip() if raw_group is not None else ""
        product_text = str(raw_product).strip() if raw_product is not None else ""
        if group_text and not product_text and re.match(r"^\([a-z]\)\s+", group_text, re.IGNORECASE):
            marker = group_text[1:2].casefold()
            definitions.append({**source, "source_row_number": row_index,
                                "definition_key": f"footnote_{marker}", "definition_type": "footnote",
                                "section": "product_taxonomy", "definition_text": group_text,
                                "definition_text_hash": _text_hash(group_text)})
            continue
        if not product_text:
            continue
        normalised_group = None
        footnote = None
        if group_text:
            normalised_group, _, footnote = normalise_product_group(group_text)
            current_group = normalised_group
        taxonomy.append({
            **source,
            "source_row_number": row_index,
            "raw_product_group": group_text or None,
            "inherited_product_group": current_group,
            "raw_product_service_name": product_text,
            "normalised_product_service_name": normalise_text(product_text),
            "footnote_marker": footnote,
            "group_was_inherited": not bool(group_text),
        })
    return taxonomy, definitions


def build_product_group_inventory(columns: pd.DataFrame) -> pd.DataFrame:
    """Identify product-group headers and contextual measurement definitions."""
    records: list[dict[str, Any]] = []
    eligible = columns[columns["sheet_type"].isin(
        ["metric_wide_table", "context_rate_table"]
    )]
    for row in eligible.itertuples():
        normalised_group, measurement, footnote = normalise_product_group(row.column)
        if normalised_group in PRODUCT_GROUPS:
            label_type = "product_group"
        elif normalised_group == "grand total":
            label_type = "total"
        elif str(row.column).startswith("unnamed_"):
            label_type = "unexpected_blank_header"
        else:
            continue
        records.append({
            "workbook": row.workbook, "reporting_period": row.reporting_period,
            "sheet": row.sheet, "canonical_sheet": row.canonical_sheet,
            "column_position": row.column_position, "raw_product_label": row.column,
            "normalised_product_group": normalised_group,
            "measurement_basis": measurement, "footnote_marker": footnote,
            "label_type": label_type,
        })
    return pd.DataFrame(records, columns=[
        "workbook", "reporting_period", "sheet", "canonical_sheet", "column_position",
        "raw_product_label", "normalised_product_group", "measurement_basis",
        "footnote_marker", "label_type",
    ])


def compare_product_groups(inventory: pd.DataFrame) -> pd.DataFrame:
    """Compare product labels and measurement wording between consecutive periods."""
    output: list[dict[str, Any]] = []
    output_columns = ["previous_period", "current_period", "canonical_sheet",
                      "normalised_product_group", "change_type", "previous_value", "current_value"]
    if inventory.empty:
        return pd.DataFrame(columns=output_columns)
    periods = sorted(inventory.reporting_period.unique())
    for previous, current in zip(periods, periods[1:]):
        roles = set(inventory.loc[inventory.reporting_period == previous, "canonical_sheet"]) | set(
            inventory.loc[inventory.reporting_period == current, "canonical_sheet"]
        )
        for role in sorted(roles):
            old = inventory[(inventory.reporting_period == previous) &
                            (inventory.canonical_sheet == role) &
                            (inventory.label_type == "product_group")]
            new = inventory[(inventory.reporting_period == current) &
                            (inventory.canonical_sheet == role) &
                            (inventory.label_type == "product_group")]
            old_map = {row.normalised_product_group: row for row in old.itertuples()}
            new_map = {row.normalised_product_group: row for row in new.itertuples()}
            for group in sorted(old_map.keys() | new_map.keys()):
                base = {"previous_period": previous, "current_period": current,
                        "canonical_sheet": role, "normalised_product_group": group}
                if group not in old_map:
                    output.append({**base, "change_type": "product_group_added",
                                   "previous_value": None, "current_value": new_map[group].raw_product_label})
                elif group not in new_map:
                    output.append({**base, "change_type": "product_group_removed",
                                   "previous_value": old_map[group].raw_product_label, "current_value": None})
                else:
                    old_row, new_row = old_map[group], new_map[group]
                    if old_row.raw_product_label != new_row.raw_product_label:
                        output.append({**base, "change_type": "product_label_changed",
                                       "previous_value": old_row.raw_product_label,
                                       "current_value": new_row.raw_product_label})
                    if _none(old_row.measurement_basis) != _none(new_row.measurement_basis):
                        output.append({**base, "change_type": "measurement_basis_changed",
                                       "previous_value": _none(old_row.measurement_basis),
                                       "current_value": _none(new_row.measurement_basis)})
    return pd.DataFrame(output, columns=output_columns)


def compare_taxonomies(
    taxonomy: pd.DataFrame, available_periods: set[str], expected_periods: Iterable[str]
) -> pd.DataFrame:
    """Compare detailed product membership, making missing Notes sheets explicit."""
    records: list[dict[str, Any]] = []
    periods = sorted(expected_periods)
    for previous, current in zip(periods, periods[1:]):
        if previous not in available_periods or current not in available_periods:
            records.append({"previous_period": previous, "current_period": current,
                            "change_type": "product_reference_unavailable",
                            "product_group": None, "product_service": None,
                            "previous_value": previous in available_periods,
                            "current_value": current in available_periods})
            continue
        old = taxonomy[taxonomy.reporting_period == previous]
        new = taxonomy[taxonomy.reporting_period == current]
        old_map = {row.normalised_product_service_name: row.inherited_product_group for row in old.itertuples()}
        new_map = {row.normalised_product_service_name: row.inherited_product_group for row in new.itertuples()}
        for product in sorted(old_map.keys() | new_map.keys()):
            if product not in old_map:
                records.append({"previous_period": previous, "current_period": current,
                                "change_type": "product_service_added", "product_group": new_map[product],
                                "product_service": product, "previous_value": None, "current_value": new_map[product]})
            elif product not in new_map:
                records.append({"previous_period": previous, "current_period": current,
                                "change_type": "product_service_removed", "product_group": old_map[product],
                                "product_service": product, "previous_value": old_map[product], "current_value": None})
            elif old_map[product] != new_map[product]:
                records.append({"previous_period": previous, "current_period": current,
                                "change_type": "product_group_reassigned", "product_group": new_map[product],
                                "product_service": product, "previous_value": old_map[product],
                                "current_value": new_map[product]})
    return pd.DataFrame(records, columns=["previous_period", "current_period", "change_type",
                                          "product_group", "product_service",
                                          "previous_value", "current_value"])


def compare_definitions(
    definitions: pd.DataFrame, available_periods: set[str], expected_periods: Iterable[str]
) -> pd.DataFrame:
    """Compare Notes narrative/footnote text by stable section key."""
    records: list[dict[str, Any]] = []
    periods = sorted(expected_periods)
    for previous, current in zip(periods, periods[1:]):
        if previous not in available_periods or current not in available_periods:
            records.append({"previous_period": previous, "current_period": current,
                            "definition_key": None, "change_type": "definition_reference_unavailable",
                            "previous_text": None, "current_text": None,
                            "previous_hash": None, "current_hash": None})
            continue
        old = {row.definition_key: row for row in definitions[definitions.reporting_period == previous].itertuples()}
        new = {row.definition_key: row for row in definitions[definitions.reporting_period == current].itertuples()}
        for key in sorted(old.keys() | new.keys()):
            if key not in old:
                change = "definition_added"
            elif key not in new:
                change = "definition_removed"
            elif old[key].definition_text_hash != new[key].definition_text_hash:
                change = "definition_text_changed"
            else:
                continue
            records.append({"previous_period": previous, "current_period": current,
                            "definition_key": key, "change_type": change,
                            "previous_text": old[key].definition_text if key in old else None,
                            "current_text": new[key].definition_text if key in new else None,
                            "previous_hash": old[key].definition_text_hash if key in old else None,
                            "current_hash": new[key].definition_text_hash if key in new else None})
    return pd.DataFrame(records, columns=["previous_period", "current_period", "definition_key",
                                          "change_type", "previous_text", "current_text",
                                          "previous_hash", "current_hash"])


def _text_hash(text: str) -> str:
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


def _none(value: Any) -> Any:
    return None if pd.isna(value) else value
