# Executive summary

## Purpose

The UK Financial Complaints and Customer Harm Intelligence Platform helps customer-operations and conduct-risk stakeholders identify FCA firm-product-period observations that warrant investigation. It combines five years of published firm-level complaints data with transparent peer, deterioration, timeliness and volume-pressure rules.

The platform is an analytical prioritisation tool. A warning is not evidence of misconduct, causation or customer harm, and human investigation remains necessary before operational or regulatory action.

## Current release

The current FCA release covers ten half-year periods from 2021-H1 through 2025-H2. The verified pipeline produces:

- 75,231 source metric records with workbook, sheet and cell lineage;
- 5,751 firm-product-period feature observations;
- 60 product-period peer benchmark records;
- 51,759 rule-level v2 indicator records;
- 135 all-period priority-review observations, all with structured analytical reviews;
- five Tableau dashboards for executive monitoring, investigation, rule explanation and data quality.

For 2025-H2, the dashboard contains 293 distinct firms and 578 firm-product observations. It identifies 13 priority-review observations across 13 firms, 71 insufficient-data observations and one confirmed source anomaly.

## What management can use it for

The platform supports:

- comparison of complaint volume with published business-context rates;
- review of complaint growth, closure outcomes and uphold percentages;
- comparison of firms within the same product and reporting period;
- identification of persistent or unusually strong combinations of signals;
- prioritisation of cases for investigation through an evidence-backed queue;
- inspection of the exact rule, metric and source-cell evidence behind a warning;
- explicit separation of limited evidence from an apparent absence of current signals.

## Analytical status

The current methodology is `fca_complaint_early_warning_v2_candidate`. It passed structural, sensitivity and reviewed-case validation, and all 135 priority observations have been reviewed. It remains `analytical_candidate_pending_business_review`; it is not approved for operational decision-making.

The implemented states are:

| Analytical state | Management interpretation |
|---|---|
| `priority_review` | Strongest combined evidence; investigate first |
| `review` | Material signals requiring diagnostic review |
| `monitor` | Early or limited signal; continue monitoring |
| `no_current_signal` | No rule triggered with sufficient coverage |
| `insufficient_data` | Too few eligible rules to classify safely |

`insufficient_data` is deliberately separate from `no_current_signal`. Missing or unavailable evidence is not treated as zero and cannot support a low-risk conclusion.

## Material limitations

- The warning model still uses FCA firm-level complaints evidence only. BOE and
  selected ONS indicators are now available as separate reporting-period
  context, while the FOS workbook supports taxonomy mapping only; none of these
  external sources currently changes warning points.
- Published firms and peer populations may change between periods.
- Firm reporting windows may overlap or differ in duration.
- Some firm identities remain unresolved and retain stable name-based keys rather than an unverified FRN.
- Public aggregate data cannot reveal root cause or individual customer outcomes.
- Forecasting, redress exposure and economic-condition analysis are outside the current release.

## Release conclusion

The FCA module is complete as a reproducible portfolio and
analytical-demonstration release. It has automated tests, source
reconciliation, reviewed mappings, explicit quality gates, a full rebuild
audit and a packaged Tableau workbook. An authorised business reviewer was not
available, so formal approval is explicitly deferred rather than assumed.
Production use remains out of scope. See `docs/portfolio_release_status.md`.
