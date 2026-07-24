# Firm identity resolution

Metric worksheets generally identify firms by name but do not consistently provide FCA reference numbers (FRNs). Trading-name reference sheets provide legal firm names and FRNs from 2023-H1 onward. Resolution therefore remains a separate, auditable derivation after extraction.

## Matching rules

Names are Unicode-normalised, case-folded and reduced to single whitespace. Punctuation and company suffixes are preserved. An FRN is assigned only when exact normalised legal-name evidence points to one unique FRN.

- `exact_name_same_period` is high-confidence because the name and FRN occur in the same reporting period.
- `exact_name_global_unique` is medium-confidence because the unique FRN is supported only in another available period. This is useful for earlier data but must not be mistaken for same-period proof.
- `exact_name_multiple_frns` is ambiguous and receives no FRN.
- `no_exact_legal_name_reference` is unmatched and receives no FRN.

The source `frn` field is never overwritten. `resolved_frn`, status, method and confidence are separate derived fields. No fuzzy matching is applied automatically.

## Manual-review suggestions

`firm_match_suggestions.csv` contains three distinct candidate FRNs per unmatched period/name pair. Legal names and trading names are used as candidate evidence. Character and token similarities are ranking aids, not match confidence; even `high_similarity` can represent a different firm.

`firm_match_review_queue.csv` groups repeated names across reporting periods, reducing the initial workload from period/name observations to unique firm names. Tier A contains exact comparison-key variants and should be reviewed first; it is still not automatically approved. Tiers B and C require stronger identity evidence. Tier D should normally remain unmatched unless new authoritative evidence is found.

Reviewers should confirm legal identity and historical-period compatibility using authoritative FCA evidence. Record a decision in `data/mappings/firm_match_review_decisions.csv` only when evidence is sufficient. At most one candidate may ultimately be approved for an unmatched period/name pair. Uncertainty should remain unresolved. Generating suggestions never changes the identity crosswalk or resolved metric table.

Reviewed decisions are applied with `python -m customer_harm.matching.review_cli`. The command rejects unknown suggestion IDs, invalid decision values, missing approval metadata and multiple approved candidates for one observation. It writes versioned `*_reviewed` outputs and never overwrites the pre-review crosswalk or metric table. `unresolved` is a completed review outcome: it means the candidate was considered but the available evidence did not justify assigning its FRN.

## Outputs

`data/interim/resolved` contains the period/name crosswalk, an enriched metric table with unchanged row count, review queues for unmatched and ambiguous names, and a JSON summary. Unmatched names require reviewed reference evidence before mapping; similarity alone is insufficient.
