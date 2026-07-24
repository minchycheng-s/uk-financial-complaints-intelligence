"""Validate management actions and produce a concise governance report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = [
    "action_id",
    "finding_id",
    "action_title",
    "priority",
    "scope",
    "owner",
    "due_date",
    "status",
    "approval_status",
    "decision_rationale",
    "evidence_reference",
    "completion_evidence",
    "reviewer",
    "reviewed_at",
]

PRIORITIES = {"critical", "high", "medium", "low"}
STATUSES = {
    "planned",
    "in_progress",
    "blocked",
    "completed",
    "accepted_risk",
    "cancelled",
}
APPROVAL_STATUSES = {
    "not_requested",
    "pending",
    "approved",
    "approved_with_conditions",
    "rejected",
}
FINAL_STATUSES = {"completed", "accepted_risk", "cancelled"}
FINAL_APPROVALS = {"approved", "approved_with_conditions", "rejected"}


def _clean(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _validate_date(value: str, field: str, action_id: str) -> None:
    if not value:
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"{action_id}: {field} must use ISO format; received {value!r}"
        ) from exc


def load_and_validate_register(path: Path) -> pd.DataFrame:
    """Load an action register and enforce its governance rules."""
    if not path.exists():
        raise FileNotFoundError(f"Management action register not found: {path}")

    actions = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in REQUIRED_COLUMNS if column not in actions.columns]
    if missing:
        raise ValueError(f"Action register is missing columns: {missing}")

    actions = actions[REQUIRED_COLUMNS].copy()
    for column in REQUIRED_COLUMNS:
        actions[column] = actions[column].map(_clean)

    if actions.empty:
        raise ValueError("Action register must contain at least one action")
    if (actions["action_id"] == "").any():
        raise ValueError("Every action requires an action_id")
    duplicates = actions.loc[
        actions["action_id"].duplicated(keep=False), "action_id"
    ].unique()
    if len(duplicates):
        raise ValueError(f"Duplicate action IDs: {sorted(duplicates)}")

    for row in actions.to_dict("records"):
        action_id = row["action_id"]
        if not row["action_title"] or not row["scope"]:
            raise ValueError(f"{action_id}: action_title and scope are required")
        if row["priority"] not in PRIORITIES:
            raise ValueError(
                f"{action_id}: priority must be one of {sorted(PRIORITIES)}"
            )
        if row["status"] not in STATUSES:
            raise ValueError(f"{action_id}: status must be one of {sorted(STATUSES)}")
        if row["approval_status"] not in APPROVAL_STATUSES:
            raise ValueError(
                f"{action_id}: approval_status must be one of "
                f"{sorted(APPROVAL_STATUSES)}"
            )

        _validate_date(row["due_date"], "due_date", action_id)
        _validate_date(row["reviewed_at"], "reviewed_at", action_id)

        if row["status"] in FINAL_STATUSES:
            required = ["owner", "decision_rationale", "completion_evidence",
                        "reviewer", "reviewed_at"]
            absent = [field for field in required if not row[field]]
            if absent:
                raise ValueError(
                    f"{action_id}: final status requires fields {absent}"
                )

        if row["approval_status"] in FINAL_APPROVALS:
            required = ["decision_rationale", "reviewer", "reviewed_at"]
            absent = [field for field in required if not row[field]]
            if absent:
                raise ValueError(
                    f"{action_id}: final approval requires fields {absent}"
                )

    return actions


def _markdown_table(actions: pd.DataFrame) -> list[str]:
    lines = [
        "| Action | Priority | Status | Approval | Owner | Due date |",
        "|---|---|---|---|---|---|",
    ]
    for row in actions.to_dict("records"):
        lines.append(
            f"| {row['action_id']}: {row['action_title']} "
            f"| {row['priority']} | {row['status']} | {row['approval_status']} "
            f"| {row['owner'] or 'Unassigned'} | {row['due_date'] or 'Not set'} |"
        )
    return lines


def build_governance_report(
    register_path: Path,
    report_path: Path,
    summary_path: Path,
) -> dict[str, Any]:
    """Validate the register and write human- and machine-readable summaries."""
    actions = load_and_validate_register(register_path)

    status_counts = actions["status"].value_counts().sort_index().to_dict()
    approval_counts = (
        actions["approval_status"].value_counts().sort_index().to_dict()
    )
    open_actions = actions.loc[~actions["status"].isin(FINAL_STATUSES)].copy()
    unassigned = int((open_actions["owner"] == "").sum())
    pending_approval = int((actions["approval_status"] == "pending").sum())
    methodology_rows = actions.loc[actions["action_id"] == "ACT-006"]
    methodology_approved = bool(
        not methodology_rows.empty
        and methodology_rows.iloc[0]["approval_status"]
        in {"approved", "approved_with_conditions"}
    )

    summary: dict[str, Any] = {
        "register": str(register_path),
        "action_count": int(len(actions)),
        "open_action_count": int(len(open_actions)),
        "unassigned_open_action_count": unassigned,
        "pending_approval_count": pending_approval,
        "status_counts": status_counts,
        "approval_status_counts": approval_counts,
        "methodology_operationally_approved": methodology_approved,
    }

    report_lines = [
        "# Management action and approval status",
        "",
        "This report is generated from "
        f"`{register_path.as_posix()}`. The register is the durable record; "
        "this document is a status view.",
        "",
        "## Current gate",
        "",
        f"- Total actions: **{len(actions)}**",
        f"- Open actions: **{len(open_actions)}**",
        f"- Unassigned open actions: **{unassigned}**",
        f"- Pending approval decisions: **{pending_approval}**",
        "- Methodology operationally approved: "
        f"**{'yes' if summary['methodology_operationally_approved'] else 'no'}**",
        "",
        "A pending analytical candidate must not be represented as approved. "
        "Completing an action also requires named ownership, rationale, evidence "
        "and independent review metadata.",
        "",
        "## Action register",
        "",
        *_markdown_table(actions),
        "",
        "## Required next decisions",
        "",
    ]
    if open_actions.empty:
        report_lines.append("- No open actions.")
    else:
        for row in open_actions.to_dict("records"):
            report_lines.append(
                f"- **{row['action_id']} — {row['action_title']}**: "
                f"{row['scope']}"
            )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
