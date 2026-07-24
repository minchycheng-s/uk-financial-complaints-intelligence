# Warning methodology validation

## Current result

The validation run passed all structural checks across 15 one-at-a-time scenarios and 5,751 firm-product observations. The baseline identifies 352 `priority_review` observations. Of all observations, 3,384 remain in the same band under every scenario, while 2,367 change under at least one scenario. Median band stability is 100%, but the least stable observations remain in their baseline band in only 10 of 15 scenarios.

## Most influential judgements

The peer-position threshold and priority boundary have the largest effect on workload:

- Reducing the high-peer threshold from the 90th to 85th percentile raises priority observations from 352 to 474.
- Increasing it to the 95th percentile lowers priority observations to 232.
- Reducing the priority boundary from six to five points raises priority observations to 446.
- Increasing it from six to eight points lowers priority observations to 181.

Other alternatives have smaller but still material effects. Raising the beyond-eight-weeks threshold from 10% to 20% lowers priority observations to 304. Increasing the minimum eligible rules from three to four lowers priority observations to 319 and increases `insufficient_data` from 1,618 to 2,533.

These results mean the prototype is suitable for structured review, but the prioritised workload is materially shaped by business choices. The baseline must not be presented as objectively correct.

## Case review

`warning_review_sample.csv` contains five current-period examples from each band. `warning_review_sample_drilldown.csv` provides all eight rule evaluations for every selected case. Record durable review outcomes in `data/mappings/warning_case_review_decisions.csv`, not in generated files.

Suggested outcomes are:

- `coherent_priority_case`: multiple indicators form a plausible investigation story.
- `useful_monitoring_case`: signal is valid but does not justify priority review.
- `likely_false_positive`: the rule is technically correct but misleading without missing context.
- `insufficient_context`: more firm, denominator or reporting-window evidence is required.
- `data_quality_concern`: source or derived values need investigation.

Reviewers should trace evidence back through features, processed facts and source workbook cells. A warning is explainable only if every triggered rule and source value can be reconstructed.

## Sign-off criteria

Before changing `warning_methodology_review.csv` from `pending_business_review`, a conduct-risk owner should confirm:

1. The priority workload is operationally manageable.
2. Reviewed priority cases are sufficiently coherent and not dominated by firm size or reporting-window effects.
3. The treatment of `insufficient_data` is acceptable.
4. Peer thresholds and minimum group size are appropriate.
5. Material-change thresholds and persistence bonus reflect business expectations.
6. Dashboard wording prevents warning bands from being interpreted as misconduct findings.

Any threshold change should create a new methodology version rather than silently rewriting v1.

## Completed sample-review findings

All 25 sampled cases were reviewed with Codex attribution. Outcomes were:

- 4 `coherent_priority_case`
- 7 `useful_monitoring_case`
- 4 `likely_false_positive`
- 4 `no_material_signal_confirmed`
- 1 `potential_false_negative`
- 5 `insufficient_context`

Four of five priority cases showed coherent evidence across multiple themes. The fifth was useful for monitoring but its high score was concentrated in context-rate rules. The likely false positives were percentage movements based on very small complaint volumes, including one to nine opened complaints. The potential false negative had opened complaints grow around 219%, but its peer position remained below the configured 90th-percentile requirement.

The methodology review status is therefore `revision_required`. Recommended changes are minimum denominator support for percentage rules, review of category-level point caps, and reconsideration of the volume-pressure peer gate. Insufficient-data suppression and rule-level traceability performed as intended and should be retained.
