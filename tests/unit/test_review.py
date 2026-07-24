from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from customer_harm.profiling.review import build_review_register, review_gate_summary


def _frames() -> dict[str, pd.DataFrame]:
    return {
        "workbook_inventory": pd.DataFrame([{"processing_status": "success"}]),
        "profiling_warnings": pd.DataFrame([{
            "reporting_period": "2025-H1", "sheet": "Opened",
            "warning_code": "FORMULA_WITHOUT_CACHED_VALUE",
            "message": "1 formula cells have no cached result.",
        }]),
        "schema_comparison": pd.DataFrame(columns=["change_type"]),
        "product_group_comparison": pd.DataFrame(columns=["change_type"]),
        "product_taxonomy_inventory": pd.DataFrame(columns=["inherited_product_group"]),
        "product_taxonomy_comparison": pd.DataFrame(columns=["change_type"]),
        "reporting_definition_comparison": pd.DataFrame(columns=["change_type"]),
    }


def test_blocking_item_keeps_gate_awaiting_manual_review(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions.csv"
    decisions.write_text("review_item_id,decision,reviewer,reviewed_at,reviewer_comment\n", encoding="utf-8")

    register = build_review_register(_frames(), decisions)
    gate = review_gate_summary(register)

    assert gate["profiling_review_status"] == "awaiting_manual_review"
    assert gate["extraction_authorised"] is False
    assert gate["pending_blocking_items"] == 1


def test_valid_human_decision_can_approve_gate(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions.csv"
    decisions.write_text("review_item_id,decision,reviewer,reviewed_at,reviewer_comment\n", encoding="utf-8")
    initial = build_review_register(_frames(), decisions)
    item_id = initial.loc[initial.blocks_extraction, "review_item_id"].iloc[0]
    decisions.write_text(
        "review_item_id,decision,reviewer,reviewed_at,reviewer_comment\n"
        f"{item_id},approved,Analyst Name,2026-07-17,Formula handling reviewed\n",
        encoding="utf-8",
    )

    gate = review_gate_summary(build_review_register(_frames(), decisions))

    assert gate["profiling_review_status"] == "approved"
    assert gate["extraction_authorised"] is True


def test_approval_requires_reviewer_metadata(tmp_path: Path) -> None:
    decisions = tmp_path / "decisions.csv"
    decisions.write_text(
        "review_item_id,decision,reviewer,reviewed_at,reviewer_comment\n"
        "REV-UNKNOWN,approved,,,\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="require reviewer"):
        build_review_register(_frames(), decisions)
