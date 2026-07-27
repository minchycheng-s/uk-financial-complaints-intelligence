# Tableau Desktop assembly guide

## What has been built

The repository contains validated reporting sources, five dashboard-specific presentation tables, a workbook manifest and a browser preview. A native `.twb` or `.twbx` is not generated because Tableau Desktop and its SDK are unavailable in the build environment. Creating unvalidated Tableau XML would be less reliable than assembling the workbook through Tableau’s supported interface.

Open `tableau/dashboard_preview.html` in a browser to see the intended executive layout. `tableau/workbook_manifest.json` is the machine-readable dashboard contract.

## 1. Refresh the delivery pack

```bash
.venv/bin/python -m customer_harm.reporting.cli
.venv/bin/python -m customer_harm.reporting.tableau_cli
```

Both commands must finish successfully. Confirm `data/processed/reporting/dashboard_validation.csv` and `data/processed/reporting/presentation/tableau_pack_validation.csv` contain no error rows.

## 2. Create the workbook

1. Open Tableau Desktop and create a workbook named `UK Financial Complaints and Customer Harm Intelligence`.
2. Connect to `data/processed/reporting/dashboard_firm_product_period.csv` as the primary logical table.
3. Add the remaining reporting CSVs as separate logical tables using the relationships in `dashboard_requirements.md`.
4. Do not create a physical join across rule detail or source metric detail.
5. Save the workbook under `tableau/uk_financial_complaints_intelligence.twbx`.

Use field names rather than Tableau’s automatic row-number fields. Confirm dates are dates, booleans are booleans, counts/scores are whole numbers, and percentages are decimals formatted as percentages.

## 3. Executive Overview

Use the presentation tables for fast, unambiguous KPI construction:

- `executive_kpis.csv`: five KPI tiles and methodology subtitle.
- `executive_period_trend.csv`: stacked columns by reporting period for priority, review and monitor.
- `executive_product_snapshot.csv`: horizontal bars or highlight table by product.

Place the mandatory analytical notice immediately below the dashboard title. Use the latest period by default.

## 4. Priority Review Queue

Connect `priority_review_queue.csv`. Create a text table containing firm, FRN, product, period, score and review disposition. Sort by `review_queue_sort_order` ascending and warning score descending. Use the calculated display fields in `calculated_fields.md`.

Show the full review comment and source-check resolution in the tooltip. Apply a distinct outline or icon to the source anomaly; do not use a colour that implies a regulatory conclusion.

## 5. Firm and Product Explorer

Use `dashboard_firm_product_period.csv` with `dashboard_peer_benchmarks.csv` related by reporting period and product group.

- Put reporting period on columns.
- Use separate sheets for counts, percentages and context rates so units are never combined.
- Add warning score as its own line or compact band strip.
- Put source reporting period, coverage and identity status in tooltips.
- Add firm and product selectors as required single/multiple-value filters.

## 6. Rule Explanation

Use `dashboard_warning_rule_detail.csv`. Filter to one firm-product observation before displaying rules. Show rule label, status, evidence, points, persistence and eligibility reason. A rule marked ineligible must display “Not assessable,” not “Passed.”

## 7. Data Quality and Coverage

Use `data_quality_summary.csv` for headline counts and `dashboard_source_metric_detail.csv` for lineage. Display source workbook, sheet, row, column, raw value, value status and quality-review fields.

## 8. Actions and filters

- Executive product selection filters the firm/product explorer.
- Executive firm selection opens the priority queue.
- Priority-queue selection opens rule explanation.
- Rule explanation can navigate to source metric detail using firm, period, source window and product.
- Apply global filters listed in `dashboard_requirements.md`.

## 9. Acceptance test before publishing

- Latest period is 2025-H2.
- Latest view contains 293 firms, 578 observations, 13 priority observations and 13 priority firms.
- All-period priority queue contains 135 observations.
- Data-quality view contains one source anomaly.
- Insufficient data is displayed separately from no current signal.
- The methodology notice appears on every dashboard.
- No percentage, context rate, rule row or product warning score is summed.
- Filters do not change KPI totals through duplicated physical joins.
- Workbook title and tooltips use investigation/prioritisation language only.

After these checks, record the Tableau reviewer, review date and approval status before publishing.

## 10. Economic context dashboard

Run:

```bash
.venv/bin/python -m customer_harm.external_context.cli
.venv/bin/python -m customer_harm.external_context.reporting_cli
```

Add `dashboard_economic_context.csv` and
`dashboard_product_period_context.csv` as separate logical tables. Relate
`reporting_period = reporting_period`; do not create a physical join to the
firm-product table.

Recommended sheets:

1. Bank Rate trend using `end_bank_rate`.
2. ONS context trend using one selected `*_period_end` measure at a time.
3. Product complaint volume using `complaints_opened_total`.
4. Product outcome medians using the fields ending `_median`.
5. Warning workload using priority, review, monitor and insufficient-data
   observation counts.

Use product group as a filter only on the product-period table. Economic
values should remain unchanged when the selected product changes. Place the
external-context interpretation notice directly below the dashboard title.
