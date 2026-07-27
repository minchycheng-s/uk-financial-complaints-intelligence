# UK Financial Complaints and Customer Harm Intelligence Platform

An auditable analytics portfolio project using FCA firm-level complaints data to identify where firms, products or reporting periods may warrant management investigation. The current analytical release covers immutable-source profiling, reviewed extraction, conservative firm resolution, analysis-ready tables, descriptive features, a reviewed v2 warning candidate and Tableau-ready reporting. Its warning scores support prioritisation only; they are not findings of misconduct or customer harm.

## Current scope

The profiler discovers every `.xlsx`/`.xlsm` file recursively under `data/raw/fca/firm_level`, calculates its SHA-256 hash, inspects every sheet, detects likely headers, and records workbook structure, missingness, inferred types and cross-period schema differences. After the manual review gate is approved, the extractor converts reviewed sheet roles into long-form metrics with raw-value and cell-level lineage. Raw workbooks are opened with `openpyxl` and never saved.

Ten source workbooks are present, covering 2021-H1 through 2025-H2. Their current names use `firm-level-complaints-data-YYYY-hN.xlsx`, which differs from the preferred `fca_firm_level_complaints_YYYY_hN.xlsx` convention in the project brief. They have deliberately not been renamed because raw inputs are immutable.

## Repository structure

```text
config/                       Source and profiling configuration
data/
  raw/fca/firm_level/         Immutable local source workbooks
  interim/profiling/          Generated profiling CSV/JSON outputs
  interim/extracted/          Generated reviewed extraction outputs
  interim/resolved/           Conservative and manually reviewed firm resolution
  interim/external_context/   BOE/ONS/FOS source profiles and tidy FOS taxonomy
  metadata/                   Generated ingestion manifest
  processed/                  Analysis, feature, warning and reporting outputs
docs/                         Method, architecture and limitations
notebooks/01_workbook_profiling.ipynb
src/customer_harm/profiling/  Reusable profiling implementation and CLI
src/customer_harm/extraction/ Reviewed extraction, mappings and validation
src/customer_harm/matching/   Conservative firm resolution and review workflow
src/customer_harm/analytics/  Analysis tables, warnings and review workflows
src/customer_harm/reporting/  Validated dashboard source and presentation tables
tableau/                      Dashboard specifications, guide, manifest and preview
tests/unit/                   Discovery, period and header tests
tests/integration/            Synthetic end-to-end pipeline test
```

Firm identity resolution remains deliberately conservative because most metric sheets do not contain FRNs. Exact reviewed evidence is applied where available; unresolved names retain stable name-based keys rather than receiving unsafe automatic matches.

## Environment setup

Python 3.11 or later is the supported portfolio environment.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

Alternatively, install the runtime/test dependencies from `requirements.txt`.

## Run workbook profiling

From the repository root:

```bash
.venv/bin/profile-fca-workbooks
```

Equivalent module command:

```bash
.venv/bin/python -m customer_harm.profiling.cli \
  --input-dir data/raw/fca/firm_level \
  --output-dir data/interim/profiling \
  --metadata-dir data/metadata \
  --source-inventory docs/source_inventory.csv \
  --review-decisions data/mappings/profiling_review_decisions.csv \
  --review-report docs/profiling_review_report.md \
  --extraction-readiness docs/extraction_readiness.md \
  --header-scan-rows 40 \
  --log-level INFO
```

The command is reproducible and overwrites generated profiling outputs only. It returns exit code `2` for a missing/invalid input directory or unparseable reporting period.

## Run tests

```bash
.venv/bin/pytest
```

Tests create synthetic workbooks only in pytest temporary directories and never write under `data/raw`.

## Run reviewed extraction

First run profiling and confirm that `data/interim/profiling/profiling_review_gate.json` has `extraction_authorised: true`. Then run:

```bash
.venv/bin/python -m customer_harm.extraction.cli --log-level INFO
```

The extractor refuses to run if the profiling gate is not approved or the raw reporting periods differ from the approved inventory. Mapping and exception rules live under `data/mappings`; reviewed exceptions retain their originating review IDs.

Generated files under `data/interim/extracted` are:

- `firms.csv`: observed firm identities and source lineage; FRN remains blank when the source sheet does not provide it.
- `complaint_metrics.csv`: long-form firm/product metrics with measurement unit, basis, status, raw value and cell lineage.
- `firm_aliases.csv`: trading-name observations with missing-marker states.
- `joint_reporters.csv`: main and included firm names by return type.
- `product_taxonomy.csv`: Notes-derived detailed products and versioned source periods.
- `rejected_records.csv`: records that could not be safely mapped rather than silently discarded.
- `validation_issues.csv`: explicit errors and warnings found after extraction.
- `sheet_reconciliation.csv`: expected versus extracted long-form records for every metric sheet.
- `total_reconciliation.csv`: additive count totals compared with complete product components.
- `extraction_summary.json`: source hashes, row counts, value statuses and validation findings.

See `docs/extracted_data_model.md` for table grains and interpretation rules.

## Resolve firm identities

After extraction and reconciliation, build a conservative firm-name-to-FRN crosswalk:

```bash
.venv/bin/python -m customer_harm.matching.cli --log-level INFO
```

Outputs under `data/interim/resolved` include `firm_identity_crosswalk.csv`, `complaint_metrics_resolved.csv`, `unmatched_firms.csv`, `ambiguous_firms.csv` and `firm_resolution_summary.json`. Only exact normalised legal names with one unique reference FRN are assigned. Same-period evidence is high-confidence; unique evidence from another period is medium-confidence. No fuzzy match is automatically accepted. See `docs/firm_identity_resolution.md`.

Generate ranked suggestions for unresolved firms without applying them:

```bash
.venv/bin/python -m customer_harm.matching.suggestion_cli
```

This writes `firm_match_suggestions.csv` with three distinct candidate FRNs per unresolved observation and creates an empty `data/mappings/firm_match_review_decisions.csv` template. Similarity labels rank review candidates; they are not approvals or identity confidence.

After recording decisions, apply them to versioned reviewed outputs:

```bash
.venv/bin/python -m customer_harm.matching.review_cli
```

The application validates decision IDs, approval metadata and the one-approved-candidate-per-observation rule. It creates `firm_identity_crosswalk_reviewed.csv`, `complaint_metrics_resolved_reviewed.csv`, `firm_match_review_results.csv`, `unmatched_firms_after_review.csv` and `firm_match_review_summary.json` without overwriting pre-review outputs.

## Build analysis-ready tables

Build the processed fact and dimensions after reviewed identity resolution:

```bash
.venv/bin/python -m customer_harm.analytics.cli
```

Outputs under `data/processed` are `fact_firm_complaints.csv`, `dim_firm.csv`, `dim_reporting_period.csv`, `dim_product_group.csv`, `dim_metric.csv`, `analysis_table_validation.csv` and `analysis_table_summary.json`. The fact preserves every source metric cell, includes the source reporting window, retains unresolved firms under stable name-based keys, and attaches reviewed quality flags. See `docs/analysis_ready_data_model.md` for grain and safe aggregation rules.

## Build descriptive features

Build firm/product observations, trends and peer benchmarks without applying a risk score:

```bash
.venv/bin/python -m customer_harm.features.cli
```

Outputs under `data/processed/features` are `firm_product_period_features.csv`, `product_period_benchmarks.csv`, `feature_validation.csv` and `feature_summary.json`. Trends use actual source-window end dates, zero-denominator growth remains missing, and peer percentiles are descriptive rather than automatic warning classifications. See `docs/feature_methodology.md`.

## Build external economic and taxonomy context

Build reporting-period Bank Rate context, a deliberately selected set of ONS
price indicators and a tidy FOS product taxonomy:

```bash
.venv/bin/python -m customer_harm.external_context.cli
```

Generated BOE and ONS tables are written under
`data/processed/external_context`; source profiles and the tidy FOS taxonomy
are written under `data/interim/external_context`. The command creates
`data/mappings/fca_fos_product_mapping.csv` only when it does not already
exist. Every suggested mapping remains `pending_review` and no external
indicator changes the warning score. See
`docs/external_context_methodology.md`.

After the standard dashboard reporting build has completed, generate the two
relationship-safe Tableau context sources with:

```bash
.venv/bin/python -m customer_harm.external_context.reporting_cli
```

This writes `dashboard_economic_context.csv` at one row per reporting period
and `dashboard_product_period_context.csv` at one row per reporting
period/product. Relate them in Tableau by `reporting_period`; do not physically
join them to firm-level records.

## Build early-warning indicators

Build the versioned, explainable analytical prototype:

```bash
.venv/bin/python -m customer_harm.analytics.warning_cli
```

Rules and thresholds live in `config/warning_methodology.json`. Outputs under `data/processed/warnings` include rule-level evidence, firm/product scores, firm-period navigation summaries, a methodology snapshot and validation results. Missing coverage produces `insufficient_data`; it never produces an assumed low-risk result. The methodology remains `pending_business_review` and must not be treated as a misconduct classification. See `docs/warning_methodology.md`.

Validate threshold sensitivity and create a current-period review sample:

```bash
.venv/bin/python -m customer_harm.analytics.validation_cli
.venv/bin/python -m customer_harm.profiling.notebook notebooks/02_warning_methodology_validation.ipynb
```

Outputs under `data/processed/warnings/validation` include scenario workload, observation-level band transitions and stability, a 25-case stratified review sample and rule drill-down. Durable case decisions belong in `data/mappings/warning_case_review_decisions.csv`. See `docs/warning_methodology_validation.md`.

Validate and summarise completed case decisions with:

```bash
.venv/bin/python -m customer_harm.analytics.case_review_cli
```

This creates `warning_case_review_results.csv`, `warning_case_review_crosstab.csv` and `warning_case_review_summary.json`. The current v1 review outcome is `revision_required`, not approved for operational use.

## Evaluate the v2 warning candidate

The reviewed v2 candidate adds denominator support, correlated-signal point caps and an exceptional complaint-growth monitor without changing the raw or v1 outputs:

```bash
.venv/bin/python -m customer_harm.analytics.warning_cli --methodology config/warning_methodology_v2.json --output-dir data/processed/warnings_v2
.venv/bin/python -m customer_harm.analytics.validation_cli --methodology config/warning_methodology_v2.json --output-dir data/processed/warnings_v2/validation
.venv/bin/python -m customer_harm.analytics.methodology_comparison_cli
```

The version comparison is written to `data/processed/warnings_comparison`. The candidate corrected all nine reviewed cases targeted by the revision, but remains pending business review and future-period validation. See `docs/warning_methodology_v2.md`.

Review every v2 priority observation with:

```bash
.venv/bin/python -m customer_harm.analytics.priority_review_cli
```

This writes 135 observation-level decisions to `data/mappings/warning_v2_priority_review_decisions.csv` and a summary to `data/processed/warnings_v2/validation/priority_review_summary.json`. These are structured analytical reviews; they do not replace business-owner approval.

Source-check resolutions are stored separately in `data/mappings/warning_v2_source_check_resolutions.csv`. Five small-denominator cases and three unusually large context-rate cases are confirmed with caveats. UK Warranty remains a confirmed source anomaly. The reviewed Studio Retail Limited identity is stored in `data/mappings/firm_identity_overrides.csv` as FRN 311908 and is applied without weakening automatic matching rules.

## Build dashboard-ready reporting tables

After the v2 warning and priority-review steps, run:

```bash
.venv/bin/python -m customer_harm.reporting.cli
```

Outputs under `data/processed/reporting` provide separate, validated Tableau sources for firm-product trends, firm-period navigation, warning-rule explanation, peer benchmarks and source-cell drill-down. Keep these as logical related tables; flattening them would duplicate observations and produce incorrect totals. Dashboard layout, filters and safe aggregation rules are defined in `tableau/dashboard_requirements.md` and `tableau/calculated_fields.md`.

The management-facing interpretation of the current analytical release is in
[`docs/analytical_findings.md`](docs/analytical_findings.md). It documents the
latest-period findings, persistent cases, recommended actions and limitations
directly from the validated reporting tables; Tableau is not required to
reproduce those conclusions.

The current decision-focused analysis is in
[`docs/business_analysis.md`](docs/business_analysis.md). It answers six
business questions with explicit periods, denominators, source files and
caveats. Its machine-readable evidence register is
[`data/processed/analysis/business_question_evidence.csv`](data/processed/analysis/business_question_evidence.csv).

## Govern management actions and approvals

Phase 3 turns the findings into a controlled action register without implying
business approval:

```bash
.venv/bin/python -m customer_harm.governance.cli
```

The durable register is
`data/mappings/management_action_register.csv`; the command validates its
controlled statuses and required decision metadata, then writes
`docs/management_action_status.md` and a machine-readable summary under
`data/processed/governance`. See `docs/management_governance.md` for the
assignment, evidence, review and approval workflow.

Build the Phase 4 evidence pack for the six strongest persistent cases with:

```bash
.venv/bin/python -m customer_harm.governance.persistent_case_cli
```

This writes case, period and triggered-rule evidence under
`data/processed/governance/persistent_cases`, creates the durable
`data/mappings/persistent_case_review_decisions.csv` template only when it does
not already exist, and updates `docs/persistent_case_review_status.md`. The
review procedure and controlled conclusions are documented in
`docs/persistent_case_review_guide.md`. The cautious preliminary assessment of
all six cases is in `docs/persistent_case_preliminary_assessment.md`; it leaves
root cause and business approval unresolved where public data is insufficient.

Build the evidence queues for management actions ACT-002 to ACT-005 with:

```bash
.venv/bin/python -m customer_harm.governance.action_evidence_cli
```

This writes reproducible priority, rule-driver, Consumer Credit monitoring and
insufficient-evidence queues under
`data/processed/governance/action_evidence`. The accompanying assessments are
in `docs/latest_priority_queue_assessment.md`,
`docs/rule_driver_assessment.md`, `docs/consumer_credit_monitoring.md` and
`docs/insufficient_evidence_assessment.md`. Recommendations for the two
business decisions are in `docs/methodology_decision_brief.md` and
`docs/source_anomaly_decision_brief.md`; neither document grants approval.

Prepare the evidence-linked business-review agenda and conservative operational
release gate with:

```bash
.venv/bin/python -m customer_harm.governance.handoff_cli
```

This writes `docs/business_review_handoff.md` and
`data/processed/governance/operational_release_gate.json`. The gate remains
false until the required governance decisions have been explicitly recorded.

Build the Tableau delivery pack with:

```bash
.venv/bin/python -m customer_harm.reporting.tableau_cli
```

This creates five presentation tables under `data/processed/reporting/presentation`, a machine-readable `tableau/workbook_manifest.json` and a data-backed `tableau/dashboard_preview.html`. Tableau Desktop is not installed in the build environment, so a native workbook is deliberately not fabricated as unvalidated XML. Follow `tableau/assembly_guide.md` to assemble and acceptance-test the `.twbx` through Tableau’s supported interface.

## Reproduce and audit the release

Run the stages in dependency order:

```bash
.venv/bin/pytest
.venv/bin/python -m customer_harm.profiling.cli --log-level INFO
.venv/bin/python -m customer_harm.extraction.cli --log-level INFO
.venv/bin/python -m customer_harm.matching.cli --log-level INFO
.venv/bin/python -m customer_harm.matching.review_cli
.venv/bin/python -m customer_harm.analytics.cli
.venv/bin/python -m customer_harm.features.cli
.venv/bin/python -m customer_harm.analytics.warning_cli --methodology config/warning_methodology_v2.json --output-dir data/processed/warnings_v2
.venv/bin/python -m customer_harm.analytics.validation_cli --methodology config/warning_methodology_v2.json --output-dir data/processed/warnings_v2/validation
.venv/bin/python -m customer_harm.analytics.priority_review_cli
.venv/bin/python -m customer_harm.reporting.cli
.venv/bin/python -m customer_harm.reporting.tableau_cli
```

The latest verified run, acceptance totals, raw-file integrity result and remaining release cautions are recorded in `docs/reproducibility_audit.md`.

For portfolio use where no authorised business reviewer is available, follow
the permitted claims and deferred-approval boundary in
`docs/portfolio_release_status.md`. The project remains demonstrable and
reproducible, while the operational release gate correctly remains false.

## Generated outputs

Under `data/interim/profiling`:

- `workbook_inventory.csv`: source identity, period, size, SHA-256, extraction timestamp, sheet list, status, row counts and warnings.
- `sheet_inventory.csv`: Excel-declared and value-based dimensions, selected header score/confidence/margin, review flag, blank rows/columns within the value range, merged cells, formulas, duplicate/raw/extracted headers, and conservative candidate total/note rows.
- `column_profiles.csv`: position, raw/normalised name, pandas storage dtype, semantic type, Python value-type distribution, null/blank/marker/error counts, zeros, negatives, numeric parse success, numeric range, uniqueness, examples and Excel number formats.
- `cell_format_profiles.csv`: per-column distribution of Excel number formats across data cells below the detected header.
- `product_group_inventory.csv`: product-group headers, measurement-basis wording, totals and unexpected blank headers across metric/context sheets.
- `product_group_comparison.csv`: product-label and measurement-basis changes between consecutive periods.
- `product_taxonomy_inventory.csv`: Notes-derived product/service taxonomy with source-row lineage, raw blank groups, review-only inherited groups and footnote markers.
- `product_taxonomy_comparison.csv`: detailed products added, removed or reassigned, plus explicit periods where Notes is unavailable.
- `reporting_definitions.csv`: Notes headings, narrative definitions and footnotes with stable keys and SHA-256 text hashes.
- `reporting_definition_comparison.csv`: definition text changes and unavailable reference periods.
- `profiling_review_register.csv`: stable review items, evidence, severity, proposed action, human decision and extraction-blocking status.
- `profiling_review_gate.json`: authoritative `approved`, `rejected` or `awaiting_manual_review` gate summary.
- `profiling_review_report.md` and `extraction_readiness.md`: generated human-readable review and readiness reports.
- `header_detection_results.csv`: every scored early-row candidate, ranking, signals and selected flag.
- `schema_comparison.csv`: sheet additions/removals, header movement, columns added/removed, possible renames, order/type changes and number-format changes.
- `profiling_warnings.csv`: explicit informational, warning and error records.
- `profiling_summary.json`: coverage totals and the profiling review gate summary.

The same auditable workbook inventory is written to `data/metadata/ingestion_manifest.csv`.

Review findings in `notebooks/01_workbook_profiling.ipynb`. Core logic is not embedded in the notebook.

Execute and save bounded notebook previews without adding Jupyter dependencies:

```bash
.venv/bin/python -m customer_harm.profiling.notebook
```

## Header and schema methodology

The first row is not assumed to be the header. Early rows are ranked using non-empty cell count, FCA header terms observed in these workbooks, uniqueness, low numeric proportion and adjacent-row density. Firm-data sheets and Notes product-reference sheets use separate term profiles. Confidence also considers the winning candidate's anchor count and score margin over the runner-up. Ties and weak selections are explicitly flagged for manual review. Every candidate and score is exported.

`Notes` is retained because it contains explanatory publication context and, in six periods, a product-group-to-product/service reference table beginning on row 9. It is labelled `product_reference` rather than treated as an ordinary firm-level table. Blank product-group cells in that table encode hierarchy and are not filled during profiling.

Sheets are assigned structural roles before profiling: `metric_wide_table`, `consumer_credit_metric_table`, `context_rate_table`, `firm_alias_reference`, `joint_reporter_reference`, or `product_reference`. Each role uses header anchors observed in that kind of FCA table.

Observed sheet-name variations are mapped to canonical roles only for comparison. Possible column renames use a conservative string-similarity threshold and are labelled as suggestions. No rename or product mapping is applied to source data.

Possible column renames combine header-text similarity with supporting column-position and semantic-type evidence. `schema_comparison.csv` retains both original sheet/column names, positions, storage and semantic types, formats, confidence, human-readable evidence and a `review_status`. Suggestions never rename source data automatically.

Excel's declared range can be much larger than its meaningful value range because formatting may extend into empty rows. The profiler reads worksheet XML to record both ranges, bounds value processing at the last cell containing a value or formula, and emits `EXCESSIVE_FORMATTED_RANGE` when the difference is material. Empty-row counts therefore describe gaps within the meaningful range, not formatted rows below the dataset.

Potential total and note rows use conservative, sheet-aware rules. Totals require an exact label in a metric table's first populated cell; notes are considered only in Notes sheets. These remain review indicators and are never removed automatically.

Value profiling is also non-destructive. Physical nulls, blank and whitespace-only strings, candidate missing/suppression/not-applicable markers, Excel errors, zeros and negatives are reported separately. Semantic types describe business-relevant shapes (`identifier`, `integer_like`, `decimal_like`, `percentage`, `currency`, `date`, `text`, `mixed`, or `empty`) while the pandas storage dtype remains available for technical debugging. No marker is converted during profiling.

Notes product groups are inherited only in a derived review field; `raw_product_group` preserves the original blank cell. Parenthetical measurement bases such as `per 1,000 policies in force` and footnote markers such as `(a)` are stored separately. Narrative definitions are hashed after whitespace/case normalisation so wording changes can be identified without treating prose as analytical rows.

Profiling code cannot grant business approval. Generated review items are merged with `data/mappings/profiling_review_decisions.csv`. An approved blocking item requires `decision` (`approved` or `approved_with_conditions`), `reviewer`, and `reviewed_at`. Extraction remains unauthorised while any blocking item is pending or rejected.

Coverage validation compares the exact expected reporting-period set and rejects missing, unexpected or duplicate periods. If a workbook fails, its partial sheet/column records are rolled back, audit outputs record the failure, and the CLI exits non-zero.

## Review gate and limitations

Before extraction or cleaning starts, review:

- low-confidence header selections and candidate alternatives;
- sheet-role mappings and possible column renames;
- product labels and reporting-definition changes;
- potential totals, footers and note rows;
- percentage and currency format changes;
- the non-standard raw filenames.

Large complaint counts may reflect firm size. Profiling alone is not evidence of customer harm or misconduct, and aggregated FCA data cannot establish root cause or individual customer outcomes.
