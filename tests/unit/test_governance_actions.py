from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from customer_harm.governance.actions import (
    REQUIRED_COLUMNS,
    build_governance_report,
    load_and_validate_register,
)


def _row(**overrides: str) -> dict[str, str]:
    row = {column: "" for column in REQUIRED_COLUMNS}
    row.update(
        {
            "action_id": "ACT-001",
            "finding_id": "FINDING-01",
            "action_title": "Investigate persistent case",
            "priority": "high",
            "scope": "Review evidence across reporting periods.",
            "status": "planned",
            "approval_status": "not_requested",
            "evidence_reference": "docs/analytical_findings.md",
        }
    )
    row.update(overrides)
    return row


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    pd.DataFrame(rows, columns=REQUIRED_COLUMNS).to_csv(path, index=False)


def test_planned_action_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "actions.csv"
    _write(path, [_row()])

    actions = load_and_validate_register(path)

    assert actions.loc[0, "action_id"] == "ACT-001"


def test_duplicate_action_id_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "actions.csv"
    _write(path, [_row(), _row()])

    with pytest.raises(ValueError, match="Duplicate action IDs"):
        load_and_validate_register(path)


def test_completed_action_requires_audit_metadata(tmp_path: Path) -> None:
    path = tmp_path / "actions.csv"
    _write(path, [_row(status="completed")])

    with pytest.raises(ValueError, match="final status requires"):
        load_and_validate_register(path)


def test_final_approval_requires_review_metadata(tmp_path: Path) -> None:
    path = tmp_path / "actions.csv"
    _write(path, [_row(approval_status="approved")])

    with pytest.raises(ValueError, match="final approval requires"):
        load_and_validate_register(path)


def test_report_keeps_pending_methodology_unapproved(tmp_path: Path) -> None:
    register = tmp_path / "actions.csv"
    report = tmp_path / "status.md"
    summary = tmp_path / "summary.json"
    _write(register, [_row(approval_status="pending")])

    result = build_governance_report(register, report, summary)

    assert result["methodology_operationally_approved"] is False
    assert "Methodology operationally approved: **no**" in report.read_text()
    assert summary.exists()
