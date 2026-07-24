"""Value and measurement normalisation with raw-value preservation."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from customer_harm.extraction.mappings import normalise_label

IDENTIFIER_HEADERS = {
    "firm name": "firm_name",
    "firm group": "raw_firm_group",
    "group": "raw_firm_group",
    "joint report": "joint_reporting_flag",
    "joint reporting": "joint_reporting_flag",
    "reporting period": "source_reporting_period",
    "submission date": "source_reporting_period",
    "frn": "frn",
    "reporting frequency": "reporting_frequency",
    "semester": "semester",
}


def identifier_name(header: str) -> str | None:
    return IDENTIFIER_HEADERS.get(normalise_label(header))


def raw_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def normalise_metric_value(value: Any) -> tuple[float | None, str, str]:
    """Return numeric value, status and reason without turning absence into zero."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None, "missing", "blank_source_cell"
    if isinstance(value, bool):
        return None, "invalid", "boolean_in_metric_cell"
    if isinstance(value, (int, float)):
        return float(value), "valid", ""
    text = str(value).strip()
    if not text:
        return None, "missing", "blank_source_cell"
    if normalise_label(text) in {"null", "n/a", "na", "-"}:
        return None, "missing_marker", "source_missing_literal"
    if text.startswith("#"):
        return None, "invalid", "excel_error"
    cleaned = text.replace(",", "").replace("%", "")
    try:
        number = float(cleaned)
        if text.endswith("%"):
            number /= 100
        return number, "valid", ""
    except ValueError:
        return None, "invalid", "non_numeric_metric_value"


def context_basis(raw_header: str, canonical_sheet: str) -> str:
    match = re.search(r"\((per\s+1[,.]?000\s+[^)]*)\)", raw_header, flags=re.I)
    if match:
        return normalise_label(match.group(1)).replace(" ", "_").replace(",", "")
    if canonical_sheet == "context_provision":
        return "per_1000_accounts_or_policies_provided"
    return "per_1000_accounts_or_policies_sold"


def consumer_credit_measure(raw_header: str, reporting_period: str) -> tuple[str, str]:
    label = normalise_label(raw_header)
    if "received" in label:
        return "complaints_opened", "count"
    if "closed" in label:
        return "complaints_closed", "count"
    if "upheld" in label:
        percentage_periods = {
            "2021-H1", "2023-H1", "2024-H1", "2024-H2", "2025-H1", "2025-H2"
        }
        is_percentage = "%" in raw_header or "percentage" in label or reporting_period in percentage_periods
        return ("complaints_upheld", "percentage") if is_percentage else ("complaints_upheld", "count")
    return "", ""


def reviewed_metric_override(
    value: Any, reporting_period: str, canonical_sheet: str, product_group: str
) -> tuple[str, str] | None:
    """Apply only exceptions backed by an explicit profiling review decision."""
    if (value == "#N/A" and reporting_period == "2025-H2" and product_group == "grand_total"
            and canonical_sheet in {"percentage_within_3_days", "percentage_upheld"}):
        return "not_calculable", "no_component_values"
    return None
