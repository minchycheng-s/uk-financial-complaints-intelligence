# Tableau calculated fields

Most business logic is computed in Python so Tableau remains a presentation layer. The following fields are safe display calculations.

## Priority band label

```text
CASE [priority_band]
WHEN "priority_review" THEN "Priority review"
WHEN "review" THEN "Review"
WHEN "monitor" THEN "Monitor"
WHEN "no_current_signal" THEN "No current signal"
WHEN "insufficient_data" THEN "Insufficient data"
END
```

## Review queue order

```text
CASE [review_disposition]
WHEN "source_anomaly_requires_business_review" THEN 1
WHEN "retain_priority_review" THEN 2
WHEN "retain_priority_review_with_statistical_caveat" THEN 3
WHEN "retain_priority_review_with_definition_caveat" THEN 4
WHEN "retain_priority_review_borderline" THEN 5
ELSE 6
END
```

## Warning score display

```text
IF [priority_band] = "insufficient_data" THEN "Insufficient data"
ELSE STR(INT([warning_score])) + " points"
END
```

## Rule status label

```text
CASE [rule_status]
WHEN "triggered_persistent" THEN "Triggered and persistent"
WHEN "triggered" THEN "Triggered"
WHEN "ineligible" THEN "Not assessable"
ELSE "Eligible, not triggered"
END
```

## Latest-period priority firm

Use this only with `dashboard_firm_period`, which has one row per firm and period:

```text
[is_latest_reporting_period] AND [has_priority_review_product]
```

## Percentage display

Underlying percentages are stored as proportions. Apply Tableau percentage formatting rather than multiplying the values. Values confirmed outside the usual range must remain unchanged and display their quality caveat.

## Prohibited calculations

- Do not calculate a new warning score in Tableau.
- Do not convert `insufficient_data` to zero.
- Do not sum percentages, context rates, warning-rule rows or product warning scores.
- Do not infer harm, misconduct or regulatory breach from a band.
