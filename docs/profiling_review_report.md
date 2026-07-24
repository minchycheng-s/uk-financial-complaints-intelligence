# Workbook profiling review report

Review status: **approved**

Extraction authorised: **True**

This report is generated from profiling evidence. Only decisions recorded in `data/mappings/profiling_review_decisions.csv` count as human approval.

## Review items

| ID | Category | Scope | Severity | Blocks extraction | Status | Recommended action |
|---|---|---|---|---:|---|---|
| REV-A384BF1B33 | source_coverage | all periods | info | False | approved | Retain hashes and exact-period validation. |
| REV-E86CDF0785 | source_naming | 2021-H1 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-7FEC48E030 | header_selection | 2021-H1 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-8B2996CFDD | source_naming | 2021-H2 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-A490218956 | header_selection | 2021-H2 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-C3A87947AA | source_naming | 2022-H1 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-CE02A4F68C | header_selection | 2022-H1 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-A51F5C5CEF | source_naming | 2022-H2 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-65844D44C3 | header_selection | 2022-H2 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-E0FB2DF0B3 | source_naming | 2023-H1 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-0BB8894C13 | formatted_range | 2023-H1 / Closed within 3 days | low | False | approved | Accept value-based bounds while retaining the source-range warning. |
| REV-CC418B08B4 | header_selection | 2023-H1 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-140CBA92AC | source_naming | 2023-H2 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-F1ED3817F3 | mixed_column | 2023-H2 / Context (Intermediation) | high | True | approved | Determine the meaning of the text value and unnamed column before extraction. |
| REV-7D1451CAB0 | source_naming | 2024-H1 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-6853FA8892 | header_selection | 2024-H1 / Notes | low | False | approved | Confirm row 9 as the Notes taxonomy header. |
| REV-59BFF984E7 | source_naming | 2024-H2 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-6526CD6DA2 | source_naming | 2025-H1 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-DE070F74FA | missing_markers | 2025-H1 / Trading Names | medium | True | approved | Confirm the marker meaning and document its future missing-value category. |
| REV-DD5E937D6A | source_naming | 2025-H2 | low | False | approved | Keep immutable raw names and use manifest source IDs. |
| REV-D7590B79E4 | excel_errors | 2025-H2 / Percentage within 3 days | high | True | approved | Inspect the affected error cells and define whether they are invalid, unavailable or derivable. |
| REV-189F967382 | excel_errors | 2025-H2 / Percentage upheld | high | True | approved | Inspect the affected error cells and define whether they are invalid, unavailable or derivable. |
| REV-EE0C638468 | schema_changes | possible_column_renamed | high | True | approved | Review evidence and approve canonical mappings or period-specific exceptions. |
| REV-EB30419D16 | schema_changes | semantic_type_changed | high | True | approved | Review evidence and approve canonical mappings or period-specific exceptions. |
| REV-23981CDAE7 | schema_changes | sheet_added | medium | True | approved | Review evidence and approve canonical mappings or period-specific exceptions. |
| REV-F65BAA3049 | schema_changes | sheet_removed | high | True | approved | Review evidence and approve canonical mappings or period-specific exceptions. |
| REV-4D13ADA54B | product_definitions | context sheets | high | True | approved | Confirm whether omitted per-1,000 wording changes meaning or presentation only. |
| REV-2D18373974 | product_definitions | insurance product group | high | True | approved | Approve or reject an explicit reviewed mapping; preserve both raw labels. |
| REV-3AF425FDE7 | reference_availability | Notes taxonomy | medium | False | approved | Use the latest prior taxonomy only if explicitly approved and versioned. |
| REV-D0F4A14413 | reporting_definitions | Notes narrative | medium | False | approved | Review publication dates and stale period wording; record source text verbatim. |

## Gate rule

Profiling remains `awaiting_manual_review` until every blocking item has an `approved` or `approved_with_conditions` decision with reviewer metadata.
