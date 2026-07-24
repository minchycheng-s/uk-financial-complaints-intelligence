# Analysis-ready FCA data model

The processed layer is built from `complaint_metrics_resolved_reviewed.csv`. It preserves every extracted metric cell while adding stable keys, reviewed identity resolution and quality metadata.

## Fact grain

`fact_firm_complaints.csv` has one row per source metric cell. Its analytical grain is firm, workbook reporting period, source reporting window, canonical sheet, metric, product group and measurement basis. `fact_id` is a stable hash of source workbook, sheet, row and column. Both the fact ID and source-cell key are unique.

Use `is_analysis_ready_value = True` for numeric analysis. Missing and not-calculable rows remain in the fact for completeness analysis. Use `is_product_level = True` when aggregating product groups; otherwise `grand_total` would be counted alongside its components.

Counts, percentages and context rates are separate measurement units. Count metrics are additive where the metric dimension says `is_additive = True`. Percentages and context rates must never be summed. Context rates with different measurement bases must not be combined as if they were identical.

## Dimensions

- `dim_firm.csv` contains 460 stable firm identities after the reviewed Studio Retail/FRN 311908 correction. Resolved identities use `FRN:<frn>`. Unresolved identities use a deterministic `NAME:<hash>` key and remain in the data.
- `dim_reporting_period.csv` contains ten half-year workbook periods, calendar boundaries and the preceding period.
- `dim_product_group.csv` contains six analytical product groups plus `grand_total`, which is explicitly flagged.
- `dim_metric.csv` distinguishes metric, source table and measurement unit. This keeps consumer-credit upheld counts separate from upheld percentages.

## Quality metadata

The three reviewed percentages above the usual 0-to-1 range retain their exact source values and have `quality_flag = percentage_above_expected_range` and `quality_review_status = source_value_confirmed`. They are valid source observations, not corrected values.

`source_reporting_period` is preserved separately from `reporting_period`. This matters when a firm has multiple reporting windows within one FCA workbook period, as observed for Kensington Mortgage Company in 2023-H2.

## Rebuild

Run the upstream extraction and identity steps first, then:

```bash
.venv/bin/python -m customer_harm.analytics.cli
```

The build fails on row loss, duplicate source cells, duplicate fact IDs or invalid dimension keys. Results are summarised in `analysis_table_summary.json` and `analysis_table_validation.csv`.
