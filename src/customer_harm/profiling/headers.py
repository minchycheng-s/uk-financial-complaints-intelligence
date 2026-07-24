"""Explainable workbook header detection."""

from __future__ import annotations

import re
from typing import Any

# These anchors come from the observed FCA workbooks. Each table role gets only
# the terms expected in that structure, reducing accidental matches in data rows.
IDENTIFIER_TERMS = {
    "firm name",
    "firm group",
    "frn",
    "joint report",
    "joint reporting",
    "reporting period",
}

PRODUCT_GROUP_TERMS = {
    "banking and credit cards",
    "decumulation & pensions",
    "home finance",
    "insurance & pure protection",
    "investments",
}

METRIC_TABLE_TERMS = IDENTIFIER_TERMS | PRODUCT_GROUP_TERMS | {"grand total"}

CONSUMER_CREDIT_TERMS = IDENTIFIER_TERMS | {
    "reporting frequency",
    "semester",
    "grand total",
    "complaints received",
    "complaints closed",
    "complaints upheld",
    "percentage upheld",
}

CONTEXT_RATE_TERMS = IDENTIFIER_TERMS | PRODUCT_GROUP_TERMS | {
    "submission date",
}

FIRM_ALIAS_TERMS = {
    "firm name",
    "frn",
    "other trading names",
    "firm group",
}

JOINT_REPORTER_TERMS = {
    "firm name",
    "reporting period",
    "other firms included in return",
}

# Backwards-compatible public name for callers that do not yet select a role.
FIRM_TABLE_TERMS = METRIC_TABLE_TERMS

# Notes sheets contain explanatory prose followed by a separate product-taxonomy
# reference table.  These anchors identify that table rather than the prose.
PRODUCT_REFERENCE_TERMS = {
    "product group",
    "product/service name",
}

HEADER_TERM_PROFILES = {
    "metric_wide_table": METRIC_TABLE_TERMS,
    "consumer_credit_metric_table": CONSUMER_CREDIT_TERMS,
    "context_rate_table": CONTEXT_RATE_TERMS,
    "firm_alias_reference": FIRM_ALIAS_TERMS,
    "joint_reporter_reference": JOINT_REPORTER_TERMS,
    "product_reference": PRODUCT_REFERENCE_TERMS,
}


def classify_header_confidence(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Explain confidence using anchor matches and separation from the runner-up."""
    if not candidates:
        return {
            "runner_up_score": None,
            "score_margin": None,
            "header_confidence": "none",
            "requires_manual_review": True,
        }
    selected = candidates[0]
    runner_up_score = candidates[1]["score"] if len(candidates) > 1 else None
    margin = round(selected["score"] - runner_up_score, 4) if runner_up_score is not None else None
    keyword_matches = selected["keyword_matches"]
    if keyword_matches >= 2 and (margin is None or margin >= 2):
        confidence = "high"
    elif keyword_matches >= 1 and (margin is None or margin >= 1):
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "runner_up_score": runner_up_score,
        "score_margin": margin,
        "header_confidence": confidence,
        "requires_manual_review": confidence == "low",
    }


def normalise_text(value: Any) -> str:
    """Normalise a cell value for structural comparison."""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def score_header_candidates(
    matrix: list[list[Any]],
    scan_rows: int = 40,
    expected_terms: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Score early rows using density, uniqueness, text and adjacent-data signals."""
    terms = expected_terms if expected_terms is not None else FIRM_TABLE_TERMS
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(matrix[:scan_rows]):
        populated = [value for value in row if value is not None and str(value).strip()]
        if not populated:
            continue
        text_count = sum(isinstance(value, str) for value in populated)
        numeric_count = sum(isinstance(value, (int, float)) and not isinstance(value, bool) for value in populated)
        normalised = [normalise_text(value) for value in populated]
        keyword_count = sum(any(term in value for term in terms) for value in normalised)
        unique_ratio = len(set(normalised)) / len(normalised)
        text_ratio = text_count / len(populated)
        numeric_ratio = numeric_count / len(populated)
        next_row_count = 0
        if index + 1 < len(matrix):
            next_row_count = sum(
                bool(value is not None and str(value).strip()) for value in matrix[index + 1]
            )
        adjacency_ratio = min(next_row_count / max(len(populated), 1), 1.0)
        score = (
            len(populated) * 1.5
            + keyword_count * 2.0
            + unique_ratio * 2.0
            + text_ratio
            - numeric_ratio
            + adjacency_ratio
        )
        candidates.append({
            "row_number": index + 1,
            "score": round(score, 4),
            "non_empty_cells": len(populated),
            "keyword_matches": keyword_count,
            "unique_ratio": round(unique_ratio, 4),
            "text_ratio": round(text_ratio, 4),
            "numeric_ratio": round(numeric_ratio, 4),
            "adjacent_row_density": round(adjacency_ratio, 4),
            "values": " | ".join(str(value) for value in populated)[:1000],
        })
    return sorted(candidates, key=lambda item: (-item["score"], item["row_number"]))


def detect_header(
    matrix: list[list[Any]],
    scan_rows: int = 40,
    expected_terms: set[str] | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Return the zero-based best header row and all ranked candidates."""
    candidates = score_header_candidates(matrix, scan_rows, expected_terms)
    return (candidates[0]["row_number"] - 1 if candidates else 0), candidates
