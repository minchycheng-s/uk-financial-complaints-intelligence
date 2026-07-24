# Management review and approval workflow

## Purpose

Phase 3 converts the analytical findings into a controlled action and approval
process. It does not approve the warning methodology and does not convert
analytical signals into findings of customer harm or misconduct.

The durable record is:

`data/mappings/management_action_register.csv`

The generated status view is:

`docs/management_action_status.md`

## Step-by-step operating process

1. A management sponsor assigns an owner and due date to each open action.
2. The owner reviews the evidence reference and records progress through
   `planned`, `in_progress` or `blocked`.
3. Investigation results are recorded in `decision_rationale` and linked or
   described in `completion_evidence`.
4. A reviewer who can challenge the result records their name and ISO-format
   review timestamp.
5. The action can then move to `completed`, `accepted_risk` or `cancelled`.
6. Approval actions require an explicit `approval_status`: `approved`,
   `approved_with_conditions` or `rejected`. Blank metadata cannot confer
   approval.
7. Regenerate the status report and commit the register with its supporting
   evidence.

## Register fields

| Field | Meaning |
|---|---|
| `action_id` | Stable unique action identifier |
| `finding_id` | Finding or governance requirement that created the action |
| `action_title` | Short management-readable description |
| `priority` | `critical`, `high`, `medium` or `low` |
| `scope` | Exact work expected |
| `owner` | Named accountable owner |
| `due_date` | ISO date or timestamp |
| `status` | Workflow status |
| `approval_status` | Separate approval decision state |
| `decision_rationale` | Reason for the final action or approval decision |
| `evidence_reference` | Repository path or controlled evidence reference |
| `completion_evidence` | Evidence that the action outcome was implemented |
| `reviewer` | Person who reviewed the completed decision |
| `reviewed_at` | ISO review date or timestamp |

## Validation rules

- Action IDs must be unique.
- Priority, action status and approval status must use their controlled values.
- Final action statuses require an owner, rationale, completion evidence,
  reviewer and review timestamp.
- Final approval decisions require rationale, reviewer and review timestamp.
- Dates must use ISO format.
- A pending approval is always reported as not operationally approved.

Run:

```bash
.venv/bin/python -m customer_harm.governance.cli
```

An invalid register returns exit code `2`; no valid-looking status report is
produced from invalid governance data.

## Approval boundary

The project currently remains an analytical candidate. Only an authorised
business owner can approve operational use. Updating code, generating a report,
completing analytical case reviews or assembling Tableau dashboards does not
grant that approval.
