# Insufficient-evidence assessment

## Outcome

All 71 latest `insufficient_data` observations have been categorised using
rule-eligibility evidence:

| Product group | Cases | Zero eligible rules | One or two eligible rules |
|---|---:|---:|---:|
| Banking and Credit Cards | 10 | 10 | 0 |
| Consumer Credit | 9 | 0 | 9 |
| Decumulation and Pensions | 10 | 7 | 3 |
| Home Finance | 17 | 14 | 3 |
| Insurance and Pure Protection | 13 | 8 | 5 |
| Investments | 12 | 9 | 3 |

Forty-eight observations have no eligible rules. Twenty-three have only one or
two eligible rules, which is below the evidence needed for classification.
Missing required features account for nearly all ineligible rule rows; three
rows also fail the minimum peer-group condition.

## Treatment

- Do not merge these records with `no_current_signal`.
- Attempt to restore or source missing features where the source supports it.
- Where peer groups are too small, retain the limitation and do not classify.
- Consumer Credit requires a product-specific method rather than fabricated
  timeliness or context values.
- Home Finance is the first remediation priority because it has 17 affected
  observations, 14 with zero eligible rules.

The case-level queue is
`data/processed/governance/action_evidence/insufficient_evidence_queue.csv`.
