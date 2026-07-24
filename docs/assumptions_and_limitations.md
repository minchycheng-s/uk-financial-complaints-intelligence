# Assumptions and limitations

- Filename periods are treated as the reporting period and validated against `YYYY-H1/H2`.
- Sheet-title variants are grouped heuristically for comparison; mappings require review.
- Header detection is explainable but heuristic and its ranked candidates must be reviewed.
- Possible column renames use text similarity and are suggestions only.
- Aggregated FCA data cannot establish misconduct, causation or individual customer outcomes.
- Early-warning rules and weights are an analytical prototype pending business-owner review; bands prioritise investigation and are not risk probabilities or regulatory conclusions.
- Peer percentiles depend on the firms published in each period and product group. FCA publication thresholds and changes in the reporting population can change relative positions.
- Firm reporting windows may overlap and vary in length, so consecutive observations are not always identical calendar periods.
