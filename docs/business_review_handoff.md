# Business review handoff

## Current outcome

The analytical evidence is ready for business review. Operational release is **not authorised**.

- Open actions: **7**
- Unassigned open actions: **7**
- Pending governance decisions: **2**
- Evidence references valid: **yes**

## Required meeting roles

- Accountable business owner: owns the decision and implementation.
- Complaints/conduct-risk specialist: tests the business interpretation.
- Data or methodology owner: explains rules, limitations and lineage.
- Independent reviewer: challenges and records the final review.

## Action-by-action agenda

### ACT-001 — Review persistent firm-product cases

- Priority: `critical`
- Current status: `in_progress`
- Approval status: `not_requested`
- Evidence: `docs/persistent_case_preliminary_assessment.md`
- Decision required: Complete longitudinal root-cause reviews for the six persistent cases identified in the analytical findings.

### ACT-002 — Complete the latest priority queue

- Priority: `high`
- Current status: `in_progress`
- Approval status: `not_requested`
- Evidence: `docs/latest_priority_queue_assessment.md`
- Decision required: Investigate all 13 latest priority-review observations, starting with Insurance and Pure Protection and Decumulation and Pensions.

### ACT-003 — Diagnose dominant rule drivers

- Priority: `high`
- Current status: `in_progress`
- Approval status: `not_requested`
- Evidence: `docs/rule_driver_assessment.md`
- Decision required: Review timeliness, upheld-percentage and context-rate evidence and document supported operational or definitional causes.

### ACT-004 — Establish Consumer Credit monitoring

- Priority: `medium`
- Current status: `in_progress`
- Approval status: `not_requested`
- Evidence: `docs/consumer_credit_monitoring.md`
- Decision required: Create a product-specific volume monitoring process without treating partial coverage as a low-risk conclusion.

### ACT-005 — Resolve insufficient-evidence cases

- Priority: `high`
- Current status: `in_progress`
- Approval status: `not_requested`
- Evidence: `docs/insufficient_evidence_assessment.md`
- Decision required: Assign and categorise the 71 latest insufficient-data observations, prioritising Home Finance.

### ACT-006 — Approve or reject warning methodology

- Priority: `critical`
- Current status: `planned`
- Approval status: `pending`
- Evidence: `docs/methodology_decision_brief.md`
- Decision required: Business owner must review the v2 rules, thresholds, family caps, persistence logic and bands before operational use.

### ACT-007 — Decide treatment of confirmed source anomaly

- Priority: `high`
- Current status: `planned`
- Approval status: `pending`
- Evidence: `docs/source_anomaly_decision_brief.md`
- Decision required: Document whether and how the confirmed historical closure-percentage inconsistency may be used in derived timeliness analysis.

## How to record a decision

Update `data/mappings/management_action_register.csv` rather than this generated report. Add the owner and due date first. A final action also requires decision rationale, completion evidence, reviewer and ISO review timestamp. ACT-006 and ACT-007 additionally require an `approval_status` of `approved`, `approved_with_conditions` or `rejected`.

After the meeting, regenerate and validate:

```bash
.venv/bin/python -m customer_harm.governance.cli
.venv/bin/python -m customer_harm.governance.handoff_cli
```
