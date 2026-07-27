# Dashboard requirements

## Status and purpose

The dashboard uses the reviewed v2 analytical candidate to prioritise investigation. It must always display: “Analytical prioritisation only; not evidence of misconduct or customer harm. Pending business approval.” The dashboard must not describe a firm as harmful, unsafe, non-compliant or high risk.

## Data sources and relationships

Use CSVs under `data/processed/reporting` as separate logical tables. Relate them using the stated keys; do not physically join all tables into one flat extract.

| Logical table | Relationship key | Purpose |
|---|---|---|
| `dashboard_firm_product_period` | firm, period, source window, product | Primary warning and trend analysis |
| `dashboard_firm_period` | firm and period | Executive firm counts and navigation |
| `dashboard_warning_rule_detail` | firm, period, source window, product | Rule explanation and eligibility |
| `dashboard_peer_benchmarks` | period and product | Median and quartile reference lines |
| `dashboard_source_metric_detail` | source-cell `fact_id` | Raw-value and lineage drill-down |
| `dashboard_economic_context` | reporting period | One BOE/ONS context row per half-year; never sum these values across firms |
| `dashboard_product_period_context` | period and product | Product-level complaint totals, firm medians, warning workload and trends |

Do not sum complaint counts from the rule-detail table: every firm-product observation has nine rule rows. Count metrics are additive only in the source metric table where `is_analysis_ready_value = True`, `is_product_level = True`, and the selected metric is additive. Never sum percentages or context rates.

## Required dashboards

### 1. Executive overview

- Latest-period KPI tiles: distinct firms, firms with priority products, priority product observations, open source anomalies and insufficient-data observations.
- Trend of priority, review and monitor observations by reporting period.
- Product-group distribution of current priority observations.
- Notice showing methodology ID, candidate status and latest reporting period.
- Clicking a firm navigates to the priority queue or firm explorer.

### 2. Priority review queue

- One row per priority firm-product-period observation.
- Display firm, FRN, product, period, score, independent signal-family count, triggered rules, persistence, review disposition and caveat flags.
- Default sort: source anomaly first, then strong retained cases, statistical/definition caveats, and borderline cases; within each group sort score descending.
- Clearly distinguish `source_anomaly_requires_business_review` from ordinary analytical review.

### 3. Firm and product explorer

- Firm-product trend for opened/closed complaints, upheld percentage, closure timeliness and context rates.
- Warning score and band shown on the same period axis without combining measurement units.
- Product-period peer median and interquartile range as optional reference lines.
- Preserve the actual `source_reporting_period` in tooltips because it can differ from the FCA workbook period.

### 4. Rule explanation

- Show each rule’s eligibility, trigger status, persistence, points, peer count and condition evidence.
- Explain capped versus uncapped score using `family_score_evidence` and `point_cap_reduction`.
- Ineligible rules must display their eligibility reason and must not appear as reassuring non-triggers.

### 5. Data quality and coverage

- Counts by coverage status and identity-match status.
- Source anomalies and review caveats with source-cell evidence.
- Missingness for core metrics by period/product.
- Link drill-down fields to source workbook, sheet, row and column; raw files remain read-only.

### 6. Economic and complaint context

- Relate `dashboard_economic_context` to
  `dashboard_product_period_context` using `reporting_period`.
- Show Bank Rate and selected ONS series in separate charts because they use
  different concepts even where the unit is percentage points.
- Show product complaint totals or firm medians beside—not mathematically
  combined with—the economic indicators.
- Display: “Economic context supports interpretation only; it does not
  establish causation and does not change the warning score.”
- Do not display a correlation as causal evidence. Ten half-year observations
  are insufficient for a reliable causal model.

## Global filters

Reporting period, product group, firm/FRN, priority band, review disposition, coverage status, identity status, triggered rule and persistent trigger.

## Refresh acceptance criteria

- Reporting validation status is `passed`.
- Exactly 5,751 firm-product observations and 51,759 v2 rule observations for the current ten-workbook release.
- Every priority observation has an analytical review disposition.
- Exactly one currently open source anomaly is visible.
- No dashboard extract changes files under `data/raw`.
