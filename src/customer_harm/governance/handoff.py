"""Build a business-review handoff without granting or implying approval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from customer_harm.governance.actions import (
    FINAL_APPROVALS,
    FINAL_STATUSES,
    load_and_validate_register,
)


def build_business_review_handoff(
    register_path: Path,
    report_path: Path,
    gate_path: Path,
) -> dict[str, Any]:
    """Create an evidence-linked review pack and conservative release gate."""
    actions = load_and_validate_register(register_path)
    repository_root = register_path.resolve().parents[2]

    missing_evidence = [
        f"{row['action_id']}:{row['evidence_reference']}"
        for row in actions.to_dict("records")
        if row["evidence_reference"]
        and not (repository_root / row["evidence_reference"]).exists()
    ]
    open_actions = actions.loc[~actions["status"].isin(FINAL_STATUSES)]
    pending_approvals = actions.loc[
        actions["action_id"].isin(["ACT-006", "ACT-007"])
        & ~actions["approval_status"].isin(FINAL_APPROVALS)
    ]
    methodology = actions.loc[actions["action_id"] == "ACT-006"]
    methodology_approved = bool(
        not methodology.empty
        and methodology.iloc[0]["approval_status"]
        in {"approved", "approved_with_conditions"}
    )
    gate = {
        "register": register_path.as_posix(),
        "evidence_references_valid": not missing_evidence,
        "missing_evidence_references": missing_evidence,
        "open_action_count": int(len(open_actions)),
        "unassigned_open_action_count": int((open_actions["owner"] == "").sum()),
        "pending_governance_decision_count": int(len(pending_approvals)),
        "methodology_operationally_approved": methodology_approved,
        "operational_release_authorised": bool(
            methodology_approved
            and not missing_evidence
            and len(pending_approvals) == 0
        ),
    }

    lines = [
        "# Business review handoff",
        "",
        "## Current outcome",
        "",
        "The analytical evidence is ready for business review. Operational release "
        f"is **{'authorised' if gate['operational_release_authorised'] else 'not authorised'}**.",
        "",
        f"- Open actions: **{gate['open_action_count']}**",
        f"- Unassigned open actions: **{gate['unassigned_open_action_count']}**",
        f"- Pending governance decisions: **{gate['pending_governance_decision_count']}**",
        "- Evidence references valid: "
        f"**{'yes' if gate['evidence_references_valid'] else 'no'}**",
        "",
        "## Required meeting roles",
        "",
        "- Accountable business owner: owns the decision and implementation.",
        "- Complaints/conduct-risk specialist: tests the business interpretation.",
        "- Data or methodology owner: explains rules, limitations and lineage.",
        "- Independent reviewer: challenges and records the final review.",
        "",
        "## Action-by-action agenda",
        "",
    ]
    for row in actions.to_dict("records"):
        lines.extend(
            [
                f"### {row['action_id']} — {row['action_title']}",
                "",
                f"- Priority: `{row['priority']}`",
                f"- Current status: `{row['status']}`",
                f"- Approval status: `{row['approval_status']}`",
                f"- Evidence: `{row['evidence_reference']}`",
                f"- Decision required: {row['scope']}",
                "",
            ]
        )
    lines.extend(
        [
            "## How to record a decision",
            "",
            "Update `data/mappings/management_action_register.csv` rather than this "
            "generated report. Add the owner and due date first. A final action "
            "also requires decision rationale, completion evidence, reviewer and "
            "ISO review timestamp. ACT-006 and ACT-007 additionally require an "
            "`approval_status` of `approved`, `approved_with_conditions` or "
            "`rejected`.",
            "",
            "After the meeting, regenerate and validate:",
            "",
            "```bash",
            ".venv/bin/python -m customer_harm.governance.cli",
            ".venv/bin/python -m customer_harm.governance.handoff_cli",
            "```",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return gate
