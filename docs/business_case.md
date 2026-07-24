# Business case and current delivery scope

## Business need

Complaint volume alone cannot show where customer-outcome risk may be emerging. Large firms naturally generate more complaints, while a smaller operation may have fewer complaints but a high context rate, uphold percentage or deterioration relative to comparable firms.

Management therefore needs an analytical framework that:

- creates a consistent view across firms, products and reporting periods;
- distinguishes raw volume from published business-context measures;
- compares firms with relevant product-period peers;
- identifies unusual or persistent changes transparently;
- prioritises investigation without replacing human judgement;
- preserves the data-quality and source evidence behind every result.

The primary question for the current release is:

> Which FCA firm-product-period observations show the strongest combination of complaint-volume, context-rate, complaint-outcome and timeliness signals, and which should be investigated first?

## Stakeholders and supported decisions

The main users are customer operations, complaints operations, product management, conduct risk and senior management. The platform supports decisions about:

- where diagnostic or root-cause investigation should begin;
- which firms and products require closer monitoring;
- whether complaint-handling outcomes are deteriorating;
- whether apparently high complaint volume remains unusual after peer comparison;
- which results are too weak, incomplete or caveated for a reliable classification;
- which source anomalies require business treatment before a derived measure is used.

It does not determine misconduct, recommend individual compensation or replace compliance judgement.

## Delivered FCA release

The implemented release includes:

- ten FCA firm-level complaint workbooks from 2021-H1 to 2025-H2;
- immutable-source discovery, hashing and structural profiling;
- reviewed header, sheet, taxonomy, missing-value and exception mappings;
- canonical long-form extraction with source-cell lineage;
- conservative firm resolution with explicit manual decisions;
- firm, reporting-period, product and metric dimensions;
- firm-product-period trends and product-period peer benchmarks;
- transparent, versioned v2 warning rules with family caps and persistence controls;
- sensitivity validation and structured review of all priority observations;
- reporting tables and five interactive Tableau dashboards;
- automated tests, reconciliation checks and a reproducibility audit.

The main analytical unit is:

> Firm × product group × reporting period

## Relationship to the original business scope

The original business case describes a broader multi-source platform. The current delivery is the FCA early-warning module.

| Original area | Current status |
|---|---|
| FCA complaints | Delivered |
| Five years of trend history | Delivered |
| Firm and product standardisation | Delivered with unresolved identities retained safely |
| Complaint volume and growth | Delivered |
| Published context-rate normalisation | Delivered where source denominators exist |
| Closure and uphold outcomes | Delivered |
| Peer benchmarking | Delivered |
| Transparent anomaly detection | Delivered |
| Explainable prioritisation | Delivered; pending business approval |
| Tableau dashboards | Delivered |
| Financial Ombudsman Service integration | Future phase |
| Bank of England and ONS integration | Future phase |
| Redress and financial-exposure scenarios | Future phase |
| Forecasting | Future phase |
| Google Cloud Storage and BigQuery | Future phase |
| Advanced SQL analytical layer | Future phase |

## Business and analytical terminology

The original business case proposed four business classifications. The implementation adds a fifth state so inadequate evidence is never mistaken for low risk.

| Original business term | Implemented state | Meaning |
|---|---|---|
| High priority | `priority_review` | Strongest combined evidence; prioritise investigation |
| Medium priority | `review` | Material negative signals; perform diagnostic review |
| Watchlist | `monitor` | Early or limited evidence; continue monitoring |
| Low priority | `no_current_signal` | No current rule signal and enough eligible evidence to classify |
| Not separately defined | `insufficient_data` | Insufficient eligible evidence; no risk conclusion |

This is a semantic mapping for communication, not a claim that the score measures the probability or severity of customer harm.

## Success criteria assessment

| Criterion | FCA release assessment |
|---|---|
| Clean and reproducible multi-source dataset | Partial: reproducible FCA multi-workbook dataset; external sources not integrated |
| Standardise firms and products | Delivered |
| Identify decision-relevant trends | Analytical views delivered; final findings report remains a separate phase |
| Distinguish volume from normalised risk | Delivered where context measures are published |
| Compare firms with peers | Delivered |
| Detect unusual changes transparently | Delivered |
| Explainable prioritisation | Delivered; pending business approval |
| Estimate financial exposure | Not delivered |
| Clear Tableau dashboard | Delivered |
| Practical recommendations | Review dispositions delivered; management findings report remains a separate phase |

## Current governance position

The FCA release is suitable for analytical demonstration and portfolio presentation. Operational use requires:

1. business-owner approval of the v2 rules, thresholds and bands;
2. documented treatment of the confirmed source anomaly and definition caveats;
3. continued monitoring against future reporting periods;
4. proportionate investigation before any customer-harm or conduct conclusion.
