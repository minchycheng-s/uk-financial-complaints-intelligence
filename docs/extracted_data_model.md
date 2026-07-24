# Extracted FCA data model

The extraction layer converts wide, period-specific FCA worksheets into auditable long tables. Raw workbooks remain immutable.

## `firms.csv`

Grain: one observed firm identity per reporting period and source sheet.

Key fields include reporting period, firm name, optional FRN, raw firm group, joint-reporting flag and source lineage. FRN is not present on every FCA sheet and is never inferred from firm name without a separately reviewed matching process.

## `complaint_metrics.csv`

Grain: one firm, reporting period, canonical sheet, metric and product group.

`metric_value` is accompanied by `measurement_unit`, `measurement_basis`, `value_status`, `value_reason` and the original cell value. Counts, percentages and context rates are never combined. Source workbook, sheet, row, column and raw header provide cell-level lineage.

## `joint_reporters.csv`

Grain: one main reporting firm and included firm name per reporting period and return type. The source does not consistently provide FRNs on these sheets, so names are preserved without unsafe identifier inference.

## `firm_aliases.csv`

Grain: one firm and other-trading-name observation per period. A literal `null` is a missing marker, not a trading name and not evidence of no aliases.

## `product_taxonomy.csv`

Grain: one detailed product mapped to its inherited product group and source Notes period. Missing Notes sheets are recorded as unavailable evidence; taxonomies are not silently carried forward.

## `rejected_records.csv`

Contains cells or rows that cannot be safely canonicalised. Rejection is visible and auditable rather than silent data loss.

## `sheet_reconciliation.csv`

Grain: one extracted metric worksheet per reporting period. It compares eligible source rows multiplied by mapped metric columns with the number of long-form records produced. A match proves structural completeness, including records whose source values are blank.

## `total_reconciliation.csv`

Grain: one firm-level additive count total where a `Grand Total` is available. Complete component sets are summed and compared exactly with the reported total. Results are `matched`, `mismatch` or `not_comparable`. A record is not comparable when any component is missing or the reported total is unavailable. Percentages and context rates are excluded because they cannot safely be summed or averaged without their denominators.
