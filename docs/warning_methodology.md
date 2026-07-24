# Early-warning methodology

## Purpose and status

`fca_complaint_early_warning_v1` is an explainable analytical prototype for prioritising investigation. It is not a prediction of misconduct, a regulatory judgement or evidence of customer harm. The completed sample review concluded `revision_required` in `data/mappings/warning_methodology_review.csv`; v1 is not approved for operational use.

The methodology evaluates eight rules for each firm, product, FCA publication period and actual source reporting window. Every rule produces eligibility, evidence, trigger, points and persistence fields. Missing data never becomes a reassuring zero-risk signal.

## Eligibility

A rule is eligible only when all required features exist and its publication-period/product peer group contains at least 20 observations. A product observation needs at least three eligible rules to receive a priority band; otherwise it is `insufficient_data`, even if one available signal triggers.

Closure percentages that imply a negative or greater-than-100% derived beyond-eight-weeks value are excluded from that rule rather than interpreted as good or poor performance.

## Rules

- Provision context rate in the highest peer decile: 3 points.
- Intermediation context rate in the highest peer decile: 3 points.
- Upheld percentage in the highest peer decile: 3 points.
- At least 10% closed beyond eight weeks and in the adverse upper peer quartile: 3 points.
- Upheld percentage increased by at least five percentage points and is at or above the 75th peer percentile: 2 points.
- Provision context rate increased at least 25% and is at or above the 75th peer percentile: 2 points.
- Intermediation context rate increased at least 25% and is at or above the 75th peer percentile: 2 points.
- Opened complaints increased at least 25% and are in the highest peer decile: 1 point.

The lower volume-pressure weight reflects that raw complaint counts are highly affected by firm size. Context rates receive greater weight because they relate complaints to business undertaken, although their denominators still differ between provision and intermediation.

The relative thresholds focus attention on unusual peer position. Five percentage points and 25% changes are prototype materiality thresholds chosen to avoid signalling small fluctuations; they require business-owner review. The 10% beyond-eight-weeks threshold is also a prototype prioritisation threshold, not a statement that lower values are acceptable or that higher values prove a breach.

## Persistence and bands

A rule is persistent when it triggers in the current and immediately preceding observation for the same firm and product, ordered by actual source-window end date. Persistence adds one point per persistent rule, capped at two points.

- 0: `no_current_signal`
- 1–2: `monitor`
- 3–5: `review`
- 6 or more: `priority_review`
- fewer than three eligible rules: `insufficient_data`

Scores prioritise workload; they are not probabilities and should not be compared with credit or conduct-risk ratings.

## Outputs

- `warning_indicators.csv`: one observation and rule, including evidence and eligibility reason.
- `firm_product_warning_summary.csv`: scores and bands at the scoring grain.
- `firm_period_warning_summary.csv`: navigation summary across products; maximum product score is retained rather than summing incomparable product scores.
- `warning_methodology_snapshot.json`: exact versioned rule configuration used for the run.
- `warning_validation.csv` and `warning_summary.json`: run-level validation and coverage.

Analysts should begin with the summary, then inspect the underlying triggered rules and source metrics. A firm appearing in `priority_review` means only that the configured indicators warrant investigation.
