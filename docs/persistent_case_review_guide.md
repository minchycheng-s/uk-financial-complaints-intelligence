# Persistent-case investigation guide

## Why this review exists

The strongest early-warning evidence is persistence across periods, not one
isolated score. Phase 4 scopes the six strongest persistent firm-product cases
that remain in `priority_review` in 2025-H2.

The generated evidence makes the review faster and reproducible. It does not
decide the root cause or management response.

## Files to use

- `persistent_case_summary.csv`: case ranking and persistence history.
- `persistent_case_period_evidence.csv`: metrics, scores, bands and review
  information for every available period in each case.
- `persistent_case_rule_evidence.csv`: every triggered rule and its exact
  condition evidence.
- `persistent_case_review_decisions.csv`: durable human conclusions.
- `persistent_case_review_status.md`: concise progress view.
- `persistent_case_preliminary_assessment.md`: evidence-based explanations and
  questions prepared for a non-specialist reviewer.

Generated CSV evidence is under
`data/processed/governance/persistent_cases`. Human decisions are under
`data/mappings` and should be committed.

## Review each case step by step

1. Confirm that the firm and product identity are consistent across periods.
2. Plot or inspect opened complaints, upheld percentage, closure percentages
   and published context rates.
3. Identify when the case first became a priority and whether the same rules
   persisted.
4. Read `condition_evidence` for the triggered rules; do not infer the
   conditions from the score.
5. Check denominators, reporting windows, coverage status, review flags and
   source-check resolutions.
6. Classify the supported root cause. Use `not_determined` when the public data
   cannot support a conclusion.
7. Record a proportionate management decision and required follow-up.
8. Add a named owner, evidence reference, reviewer and ISO review date before
   setting `review_status` to `completed`.

## Controlled conclusions

Allowed root-cause categories are:

- `operational_process`
- `business_mix`
- `reporting_practice`
- `source_definition`
- `data_quality`
- `multiple_factors`
- `not_determined`

Allowed management decisions are:

- `continue_monitoring`
- `remediation_required`
- `methodology_treatment_required`
- `no_further_action`
- `escalate_for_business_review`

Use only conclusions supported by the evidence. A persistent signal is not
itself proof of misconduct, customer harm or a need for customer redress.

## Run the pack

```bash
.venv/bin/python -m customer_harm.governance.persistent_case_cli
```

The command never overwrites an existing decision register. It validates that
the register still matches the generated six-case scope and rejects incomplete
records marked as completed.
