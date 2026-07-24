"""Non-destructive semantic and missing-marker profiling for worksheet columns."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from numbers import Number
from typing import Any

import pandas as pd

from customer_harm.profiling.headers import normalise_text

MISSING_MARKERS = {"-", "--", "—", "–", "missing", "null", "none"}
SUPPRESSED_MARKERS = {"*", "**", "[x]", "suppressed", "not published"}
NOT_APPLICABLE_MARKERS = {"n/a", "na", "n.a.", "not applicable", "not_applicable"}
EXCEL_ERRORS = {"#div/0!", "#n/a", "#name?", "#null!", "#num!", "#ref!", "#value!"}
IDENTIFIER_HEADERS = {
    "firm name", "firm group", "group", "frn", "joint report", "joint reporting",
    "reporting period", "reporting frequency", "semester", "submission date",
    "other firms included in return", "other trading names", "product group",
    "product/service name",
}


def _value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return "date"
    if isinstance(value, Number) and not isinstance(value, bool):
        return "numeric"
    return "text"


def _text_marker(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = normalise_text(value)
    if not text:
        return "blank"
    if text in MISSING_MARKERS:
        return "missing_marker"
    if text in SUPPRESSED_MARKERS:
        return "suppressed"
    if text in NOT_APPLICABLE_MARKERS:
        return "not_applicable"
    if text in EXCEL_ERRORS or (text.startswith("#") and text.endswith(("!", "?"))):
        return "excel_error"
    return None


def profile_values(series: pd.Series, column: str, number_format_class: str) -> dict[str, Any]:
    """Return explainable value-shape metrics without replacing source values."""
    values = series.tolist()
    null_count = sum(pd.isna(value) for value in values)
    text_values = [value for value in values if isinstance(value, str)]
    blank_string_count = sum(value == "" for value in text_values)
    whitespace_string_count = sum(value != "" and not value.strip() for value in text_values)
    markers = Counter(marker for value in values if (marker := _text_marker(value)) is not None)
    substantive = [
        value for value in values
        if not pd.isna(value) and _text_marker(value) is None
    ]
    kinds = Counter(_value_kind(value) for value in substantive)
    numeric_values = [float(value) for value in substantive if _value_kind(value) == "numeric"]
    text_substantive = [value for value in substantive if isinstance(value, str)]
    parsed_text = pd.to_numeric(pd.Series(text_substantive, dtype="string"), errors="coerce") if text_substantive else pd.Series(dtype="Float64")
    parseable_text_count = int(parsed_text.notna().sum())
    numeric_candidate_count = len(numeric_values) + len(text_substantive)
    numeric_parse_success = (
        (len(numeric_values) + parseable_text_count) / numeric_candidate_count * 100
        if numeric_candidate_count else None
    )
    normalised_column = normalise_text(column)
    if not substantive:
        semantic_type = "empty"
    elif normalised_column in IDENTIFIER_HEADERS:
        semantic_type = "identifier"
    elif number_format_class == "percentage" or "percentage" in normalised_column:
        semantic_type = "percentage"
    elif number_format_class == "currency" or "redress" in normalised_column:
        semantic_type = "currency"
    elif set(kinds) == {"date"}:
        semantic_type = "date"
    elif set(kinds) == {"boolean"}:
        semantic_type = "boolean"
    elif set(kinds) == {"numeric"}:
        semantic_type = "integer_like" if all(value.is_integer() for value in numeric_values) else "decimal_like"
    elif set(kinds) == {"text"} and numeric_parse_success == 100:
        semantic_type = "numeric_text"
    elif set(kinds) == {"text"}:
        semantic_type = "text"
    else:
        semantic_type = "mixed"
    non_numeric_examples = [
        value for value in text_substantive
        if pd.isna(pd.to_numeric(value, errors="coerce"))
    ][:3]
    return {
        "semantic_type": semantic_type,
        "python_type_counts": json.dumps(dict(sorted(kinds.items()))),
        "null_count": int(null_count),
        "blank_string_count": int(blank_string_count),
        "whitespace_string_count": int(whitespace_string_count),
        "missing_marker_count": int(markers["missing_marker"]),
        "suppressed_marker_count": int(markers["suppressed"]),
        "not_applicable_marker_count": int(markers["not_applicable"]),
        "excel_error_count": int(markers["excel_error"]),
        "zero_count": sum(value == 0 for value in numeric_values),
        "negative_count": sum(value < 0 for value in numeric_values),
        "numeric_parse_success_percent": round(numeric_parse_success, 4) if numeric_parse_success is not None else None,
        "minimum_numeric_value": min(numeric_values) if numeric_values else None,
        "maximum_numeric_value": max(numeric_values) if numeric_values else None,
        "non_numeric_examples": json.dumps(non_numeric_examples, ensure_ascii=False),
    }
