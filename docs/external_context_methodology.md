# External context integration methodology

## Purpose

This phase adds Bank of England (BOE), Office for National Statistics (ONS)
and Financial Ombudsman Service (FOS) reference data without changing the FCA
warning score. The external tables provide explanatory context and a reviewed
taxonomy route; they are not evidence that an economic condition caused a
complaint or that misconduct occurred.

## Source roles

| Source | Current role | Analytical grain |
|---|---|---|
| BOE Bank Rate history | Interest-rate environment | reporting half-year |
| ONS `mm23.csv` | Selected inflation and price context | indicator × month and indicator × reporting half-year |
| FOS product list | Old/new product taxonomy | taxonomy version × sector × product group × product type |

The current FOS workbook contains taxonomy, not firm complaint or uphold
results. Cross-source outcome comparison therefore remains out of scope until
an appropriate FOS outcomes dataset is acquired and profiled.

## Selected ONS indicators

The source contains thousands of columns. `config/external_context.json`
deliberately selects six series:

- CPI annual rate;
- CPIH annual rate;
- housing-services annual rate;
- insurance annual rate;
- financial-services annual rate;
- RPI mortgage-interest-payment annual rate.

Values remain in source percentage points. They are not converted to decimal
fractions. Monthly values are retained and half-year summaries contain the
mean, period-end value, minimum, maximum, within-period change and observed
month count.

## BOE treatment

For every FCA reporting half-year, Bank Rate is evaluated as an effective-date
series. The output records the rate at the period start and end, the minimum
and maximum rate encountered, the change in percentage points and the number
of rate decisions inside the period.

## FOS mapping governance

The tidy taxonomy is generated under `data/interim/external_context`.
`data/mappings/fca_fos_product_mapping.csv` is created only if it does not
already exist, protecting future manual decisions. Keyword-based candidates
are suggestions only:

- every row begins as `pending_review`;
- `approved_fca_product_group` remains blank;
- suggestions are not consumed by the FCA analytical or warning pipelines.

## Safe decision use

Economic context can help distinguish a market-wide pressure period from
firm-specific deterioration. It must not:

- remove an FCA warning automatically;
- be interpreted as causal evidence;
- be summed across firms;
- be added to warning points before validation and business approval.

The appropriate first analytical use is a reporting-period relationship:

```text
dim_reporting_period
    ├── FCA firm-product-period observations
    ├── BOE half-year context
    └── ONS indicator-half-year context
```

## Outputs

```text
data/interim/external_context/
  external_source_profiles.csv
  fos_product_taxonomy.csv

data/processed/external_context/
  boe_half_year_context.csv
  ons_monthly_context.csv
  ons_half_year_context.csv
  external_context_validation.csv
  external_context_summary.json

data/mappings/
  fca_fos_product_mapping.csv

data/processed/reporting/
  dashboard_economic_context.csv
  dashboard_product_period_context.csv
  dashboard_external_context_validation.csv
  dashboard_external_context_summary.json
```

Run with:

```bash
.venv/bin/python -m customer_harm.external_context.cli
.venv/bin/python -m customer_harm.external_context.reporting_cli
```

The reporting tables remain separate logical tables. Economic context has one
row per reporting period. Product context has one row per reporting period and
product group, using sums only for complaint counts and medians for
percentages and context rates.
