# Complaint feature methodology

The feature layer reshapes valid product-level fact cells into one row per firm, FCA publication period, source reporting window and product group. Missing values are not imputed and Grand Total is excluded to prevent double counting.

## Base measures

Counts, percentages and context rates remain separate. Consumer-credit upheld counts and percentages are stored in different columns. Provision and intermediation context rates are also separate because their denominators describe different business activities.

Derived descriptive measures include complaints opened minus complaints closed and the sum of the published closed-within-three-days and closed-after-three-days-within-eight-weeks percentages. These measures describe reported data; they do not establish customer harm or regulatory breach.

## Trends

Previous values, absolute changes and percentage changes are calculated within firm and product after sorting by the actual source reporting-window end date. Percentage growth is left missing when the previous value is zero; infinity is never produced. Reporting windows can overlap or vary in duration, so trend comparisons should always retain `source_reporting_period`, `observation_start`, `observation_end` and `observation_days`.

## Peer benchmarks

Medians, quartiles and percentile ranks are calculated within FCA publication period and product group. A percentile is a relative position, not a risk score. Direction differs by measure: a high upheld rate may warrant attention, while a high timely-closure rate can be positive. Raw complaint-count percentiles are strongly influenced by firm size and should not be interpreted as conduct performance without context.

## Outputs

- `firm_product_period_features.csv` contains base measures, trends and peer percentile ranks.
- `product_period_benchmarks.csv` contains peer counts, medians and quartiles.
- `feature_validation.csv` and `feature_summary.json` document completeness and validation.

No warning thresholds or composite score are applied at this stage. Those require an explicit, reviewed business methodology.
