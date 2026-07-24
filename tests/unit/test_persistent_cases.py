from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from customer_harm.governance.persistent_cases import (
    DECISION_COLUMNS,
    select_persistent_cases,
    validate_case_decisions,
)


def _observations() -> pd.DataFrame:
    rows = []
    for number in range(1, 4):
        for period_index, period in enumerate(["2024-H2", "2025-H1", "2025-H2"]):
            rows.append(
                {
                    "firm_key": f"F{number}",
                    "product_group": "investments",
                    "reporting_period": period,
                    "display_firm_name": f"Firm {number}",
                    "product_group_label": "Investments",
                    "priority_band": (
                        "priority_review"
                        if period_index >= 3 - number
                        else "review"
                    ),
                    "warning_score": number + 7,
                    "persistent_rule_count": number,
                    "triggered_rule_ids": "RULE-A",
                    "review_disposition": "retain_priority_review",
                    "coverage_status": "broad",
                }
            )
    return pd.DataFrame(rows)


def test_selects_latest_cases_by_persistence_then_score() -> None:
    result = select_persistent_cases(_observations(), "2025-H2", case_count=2)

    assert result["display_firm_name"].tolist() == ["Firm 3", "Firm 2"]
    assert result["case_id"].tolist() == ["PCR-001", "PCR-002"]


def test_completed_decision_requires_review_evidence(tmp_path: Path) -> None:
    cases = select_persistent_cases(_observations(), "2025-H2", case_count=1)
    row = {column: "" for column in DECISION_COLUMNS}
    row.update(
        {
            "case_id": "PCR-001",
            "firm_key": "F3",
            "product_group": "investments",
            "display_firm_name": "Firm 3",
            "review_status": "completed",
            "business_approval_status": "pending_business_review",
        }
    )
    path = tmp_path / "decisions.csv"
    pd.DataFrame([row], columns=DECISION_COLUMNS).to_csv(path, index=False)

    with pytest.raises(ValueError, match="completed review requires"):
        validate_case_decisions(path, cases)
