# Early-warning methodology v2 candidate

## Purpose and status

`fca_complaint_early_warning_v2_candidate` is a review candidate created from the completed 25-case assessment of v1. It remains an analytical prioritisation tool, not a prediction of misconduct or proof of customer harm. A business owner must review and approve it before operational use.

## Why v1 was revised

The case review found four likely false positives where upheld percentages were calculated from very small numbers of closed complaints. It also found one potential false negative where complaints more than tripled to 12,736 but the firm did not cross the 90th peer percentile. Several rules also measured the same underlying signal and could overstate the amount of independent evidence.

## Candidate changes

1. Upheld and closure-timeliness rules require at least 20 closed complaints. The threshold is a stability control: percentages based on fewer observations are too volatile for this warning score. These rows remain in the source and analysis tables; they are only prevented from triggering these percentage rules.
2. Related signals share point-family caps: context rate 4, complaint outcome 4, timeliness 3 and volume pressure 2. Both uncapped and capped values are retained in `family_score_evidence` and `point_cap_reduction`.
3. Priority review starts at 8 points rather than 6. This requires a stronger combination of evidence.
4. `OPENED_EXCEPTIONAL_GROWTH` adds 2 monitoring points where opened complaints at least double and the current count is at least 100. It does not label the result as harm; it makes rapid material growth visible for investigation.

The full executable definition is in `config/warning_methodology_v2.json`.

## Validation result

The build covered 5,751 firm-product-period observations and passed structural validation. After applying the reviewed Studio Retail identity correction, v1 contains 354 priority-review observations and v2 contains 135. Of the nine reviewed cases specifically targeted by the revisions:

- all four coherent priority cases remained `priority_review`;
- all four likely false positives moved to `no_current_signal`;
- the potential false negative moved from `no_current_signal` to `monitor`.

This is strong internal evidence that the revisions behave as intended on the reviewed sample, but it is not out-of-sample validation. The 25 reviewed cases were selected from the same data used to revise the rules, so further business review and future-period monitoring are required.

## Reproduce the candidate

```bash
.venv/bin/python -m customer_harm.analytics.warning_cli \
  --methodology config/warning_methodology_v2.json \
  --output-dir data/processed/warnings_v2

.venv/bin/python -m customer_harm.analytics.validation_cli \
  --methodology config/warning_methodology_v2.json \
  --output-dir data/processed/warnings_v2/validation

.venv/bin/python -m customer_harm.analytics.methodology_comparison_cli
```

Comparison outputs are under `data/processed/warnings_comparison`. The v1 configuration and outputs remain unchanged for auditability.

## Complete priority-case review

All 135 v2 priority observations have a structured analytical review in `data/mappings/warning_v2_priority_review_decisions.csv`. Four had already appeared in the original stratified sample, leaving 131 newly reviewed observations. Each record contains its independent signal families, persistence evidence, review flags, disposition, explanation, reviewer and review date.

The dispositions are:

- 52 `retain_priority_review`: stronger cases with at least three independent signal families or a score above the eight-point boundary;
- 74 `retain_priority_review_borderline`: exactly eight points from two distinct signal families, retained but ranked below stronger cases;
- 5 `retain_priority_review_with_statistical_caveat`: source values confirmed but based on 20–49 closed complaints;
- 3 `retain_priority_review_with_definition_caveat`: unusually large Black Horse context values confirmed in the workbooks and explained by the FCA workbook Notes;
- 1 `source_anomaly_requires_business_review`: UK Warranty source percentages total 118.47% across separate FCA sheets.

The nine source checks are recorded in `data/mappings/warning_v2_source_check_resolutions.csv`. Eight are resolved with explicit caveats. UK Warranty remains a source anomaly and must not be interpreted using the derived timeliness value until a business treatment is agreed. The Studio Retail identity is now explicitly mapped to FRN 311908 using authoritative evidence and propagated through the dependent tables. Reproduce the register with:

```bash
.venv/bin/python -m customer_harm.analytics.priority_review_cli
```
