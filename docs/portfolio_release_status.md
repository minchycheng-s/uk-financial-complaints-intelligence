# Portfolio and research release status

## Release classification

This repository is ready for an **analytical demonstration and portfolio
release**. It is not an operational conduct, regulatory or customer-remediation
system.

The absence of an available business reviewer does not prevent the project
from being demonstrated, assessed or reproduced. It does prevent the warning
methodology and confirmed source-anomaly treatment from being represented as
formally approved.

## What may be presented

- the complete data-engineering and analytical workflow;
- source lineage, profiling, validation and reconciliation controls;
- descriptive findings and transparent warning rules;
- the Tableau dashboards and investigation workflow;
- preliminary analytical case assessments;
- governance controls that prevent unapproved operational use.

## Required presentation wording

Use:

> Analytical portfolio demonstration. Warning scores prioritise investigation
> and are not findings of misconduct or customer harm. Formal business
> approval was outside the available project environment.

Do not claim that the methodology is production approved, regulator endorsed,
predictive of harm or suitable for automated decisions.

## Deferred items

| Item | Status | Reason |
|---|---|---|
| Business methodology approval | Deferred | No authorised business reviewer available |
| Source-anomaly business treatment | Deferred | Requires accountable business decision |
| Internal root-cause confirmation | Deferred | Public FCA data contains no internal operational evidence |
| Production deployment | Out of scope | Approval, security, service ownership and monitoring are absent |

## Portfolio release checklist

- [x] Raw workbooks preserved unchanged.
- [x] Pipeline outputs reconciled and validated.
- [x] Automated tests pass.
- [x] Analytical limitations documented.
- [x] Priority and insufficient-evidence workloads reviewed.
- [x] Dashboard workbook assembled.
- [x] Source code placed under Git version control.
- [x] Operational approval gate remains false.
- [ ] Commit and push the current release-hardening changes.
- [ ] Add a release tag if a stable portfolio version is desired.

## If a reviewer becomes available later

Use `docs/business_review_handoff.md`, record decisions in
`data/mappings/management_action_register.csv`, then regenerate the governance
status and operational release gate. No analytical work needs to be discarded
or repeated merely because formal review was deferred.
