import json
from pathlib import Path

import pandas as pd

from customer_harm.governance.actions import REQUIRED_COLUMNS
from customer_harm.governance.handoff import build_business_review_handoff


def test_handoff_does_not_authorise_pending_methodology(tmp_path: Path) -> None:
    project = tmp_path / "project"
    register = project / "data" / "mappings" / "actions.csv"
    evidence = project / "docs" / "evidence.md"
    register.parent.mkdir(parents=True)
    evidence.parent.mkdir(parents=True)
    evidence.write_text("evidence\n", encoding="utf-8")
    row = {column: "" for column in REQUIRED_COLUMNS}
    row.update(
        {
            "action_id": "ACT-006",
            "finding_id": "GOVERNANCE",
            "action_title": "Approve methodology",
            "priority": "critical",
            "scope": "Approve or reject.",
            "status": "planned",
            "approval_status": "pending",
            "evidence_reference": "docs/evidence.md",
        }
    )
    pd.DataFrame([row]).to_csv(register, index=False)

    report = project / "docs" / "handoff.md"
    gate_path = project / "data" / "processed" / "gate.json"
    gate = build_business_review_handoff(register, report, gate_path)

    assert gate["evidence_references_valid"] is True
    assert gate["operational_release_authorised"] is False
    assert "not authorised" in report.read_text(encoding="utf-8")
    assert json.loads(gate_path.read_text())["methodology_operationally_approved"] is False
