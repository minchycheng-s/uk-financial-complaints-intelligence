# Architecture

## Current logical flow

```text
Immutable FCA workbooks
        |
        v
Python workbook profiling
  - discovery and SHA-256
  - sheet roles and header candidates
  - schema, value and format profiles
  - taxonomy and definition comparison
        |
        v
Reviewed profiling gate
  - durable decisions under data/mappings
  - extraction blocked until approved
        |
        v
Canonical extraction
  - firms, aliases and joint reporters
  - product taxonomy
  - long-form complaint metrics
  - source workbook/sheet/cell lineage
  - reconciliation and validation
        |
        v
Firm identity resolution
  - conservative exact matching
  - ranked suggestions for review only
  - approved decisions and stable unresolved keys
        |
        v
Analysis-ready model
  - fact_firm_complaints
  - firm, period, product and metric dimensions
        |
        v
Descriptive feature layer
  - firm-product-period measures and changes
  - product-period peer counts and percentiles
        |
        v
V2 warning candidate
  - versioned rule configuration
  - eligibility and small-denominator controls
  - correlated-family point caps
  - persistence and priority bands
  - sensitivity and case-review outputs
        |
        v
Reporting layer
  - firm/product trend table
  - firm/period navigation table
  - peer benchmarks
  - warning-rule detail
  - source-metric detail
        |
        v
Tableau
  - Executive Overview
  - Priority Review Queue
  - Firm and Product Explorer
  - Warning Rule Explanation
  - Data Quality and Coverage
```

## Repository layers

| Layer | Main location | Responsibility |
|---|---|---|
| Configuration | `config/` | Source settings, product mappings and versioned methodology |
| Immutable inputs | `data/raw/` | Local source files; excluded from Git |
| Durable review decisions | `data/mappings/` | Human-reviewed mappings, exceptions and case decisions |
| Profiling | `src/customer_harm/profiling/` | Workbook structure, header, schema, values and review gate |
| Extraction | `src/customer_harm/extraction/` | Canonical records, lineage and reconciliation |
| Matching | `src/customer_harm/matching/` | Conservative firm resolution and review application |
| Analysis | `src/customer_harm/analytics/` | Fact/dimensions, warnings, validation and review |
| Features | `src/customer_harm/features/` | Trends and peer benchmarks |
| Reporting | `src/customer_harm/reporting/` | Tableau-safe logical and presentation tables |
| Generated data | `data/interim/`, `data/processed/` | Reproducible derived outputs; excluded from Git except final Tableau package |
| Tests | `tests/` | Unit and synthetic end-to-end validation |
| Presentation | `tableau/` | Dashboard definitions, calculated fields, guide and preview |

## Design decisions

### Raw data is immutable

Raw workbooks are opened for reading and never saved. Generated data is written outside `data/raw`. The release audit compares before-and-after SHA-256 hashes.

### Review gates are data, not informal notes

Profiling, matching, source-check and warning-case decisions are stored in version-controlled mapping files. Automated matching never accepts a fuzzy suggestion without an explicit decision.

### Granularity is preserved

The core fact grain is one extracted metric cell. Firm-product-period features are derived later. Tableau uses logical relationships rather than one flattened physical join because the reporting tables have different grains.

### Missing evidence is not zero

Missing, suppressed, invalid and unavailable values retain explicit states. A warning observation becomes `insufficient_data` when too few rules are eligible; it does not become `no_current_signal`.

### Business logic remains outside Tableau

Python computes features, peer percentiles, rule evidence, scores, review fields and presentation tables. Tableau is the interactive presentation layer and uses only documented safe aggregations.

### Warnings remain explainable

Every warning retains its rule ID, conditions, points, eligibility, persistence, signal family, peer count and source evidence. The methodology is versioned in configuration and remains pending business approval.

## Validation and reproducibility

The release is protected by:

- unit and integration tests;
- profiling and extraction review gates;
- row-count and additive reconciliation;
- fact and feature validation;
- warning structural and sensitivity validation;
- reviewed priority cases and source anomalies;
- reporting and Tableau-pack validation;
- a documented full rebuild and raw-file integrity audit.

See `docs/reproducibility_audit.md` for the verified release totals.

## Future target architecture

The original business case also proposes external sources, Google Cloud Storage, BigQuery and advanced SQL. Those components are not part of the current implementation.

A future extension may use:

```text
FCA + FOS + Bank of England + ONS
        |
        v
Versioned ingestion and reviewed cross-source mappings
        |
        v
Google Cloud Storage immutable landing zone
        |
        v
BigQuery staging -> dimensions/facts -> analytical views
        |
        v
Scheduled Python/SQL validation and feature builds
        |
        v
Tableau curated-source connection
```

Cloud migration should follow—not precede—stable analytical definitions, external-source licensing review and business approval of the methodology.
