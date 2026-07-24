# Reproducibility and release audit

Audit date: 24 July 2026

## Outcome

The complete derived-data pipeline was rebuilt successfully from the ten FCA workbooks covering 2021-H1 through 2025-H2. All automated tests passed, all pipeline validation gates passed, the independently checked reporting totals matched the Tableau acceptance criteria, and the SHA-256 hashes of every raw workbook were unchanged.

This verifies the analytical build. It does not approve the warning methodology for operational or conduct decisions.

## Verification performed

The following sequence was run from the repository root:

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

Results:

- Tests: 85 passed, including governance evidence and release-gate controls.
- Profiling: 10 workbooks and 116 sheets.
- Extraction and reviewed identity resolution: 75,231 metric rows preserved.
- Analysis tables: 75,231 fact rows; 31,703 analysis-ready values.
- Features: 5,751 firm-product-period rows and 60 product-period benchmark rows.
- V2 warnings: 51,759 rule-indicator rows across 5,751 observations.
- Priority review: all 135 priority observations have structured analytical decisions.
- Reporting validation: zero issues.

## Raw-source integrity

SHA-256 hashes were calculated for all ten workbooks immediately before the rebuild and again after the rebuild. The two hash lists were identical. The pipeline therefore made no change to the raw Excel inputs.

The implementation opens raw workbooks for reading and writes generated outputs only under `data/interim`, `data/metadata`, `data/processed`, `docs` and `tableau`.

## Tableau acceptance totals

The following totals were independently calculated from the rebuilt reporting tables:

| Check | Verified value |
|---|---:|
| Latest reporting period | 2025-H2 |
| Distinct firms in latest period | 293 |
| Firm-product observations in latest period | 578 |
| Priority observations in latest period | 13 |
| Priority firms in latest period | 13 |
| Insufficient-data observations in latest period | 71 |
| Priority-review queue across all periods | 135 |
| Confirmed source anomalies | 1 |
| Definition caveats | 3 |
| Statistical caveats | 5 |
| Insufficient-data observations across all periods | 1,332 |
| Unresolved firm-identity observations | 163 |
| Reporting validation issues | 0 |

These values match the Tableau workbook acceptance checks used during manual assembly.

## Remaining cautions

1. The v2 methodology remains pending business-owner approval. Scores are analytical prioritisation signals, not findings of harm or misconduct.
2. Firm resolution intentionally leaves 104 distinct period-firm pairs unmatched after review. Their observations remain usable through stable name-based keys but must not be presented as FRN-confirmed identities.
3. The confirmed UK Warranty Limited source anomaly is retained exactly as published. The affected derived timeliness measure requires documented business treatment.
4. The optional Tableau rule-selection action did not behave as intended during assembly and was explicitly deferred. The rule sheets and evidence remain visible; the issue does not alter source data or calculated results.
5. The packaged Tableau workbook should be opened, refreshed and saved once more after a full data rebuild so its embedded extracts are explicitly synchronized with the newly generated CSV files.
6. Git metadata is now available and the project has been pushed to a remote
   repository. The current release-hardening changes must still be committed
   and pushed before a clean-working-tree release check can pass.
7. No authorised business reviewer is available in the project environment.
   This does not prevent portfolio demonstration, but formal approval remains
   deferred and the operational release gate remains false.

## Release interpretation

The project is ready for reproducible analytical demonstration and portfolio
presentation. Its release classification and permitted claims are documented
in `docs/portfolio_release_status.md`. Production or regulatory use remains
conditional on business approval of the methodology, treatment of documented
caveats and normal operational controls.
