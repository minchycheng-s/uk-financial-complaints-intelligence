# Confirmed source anomaly decision brief

## Case

UK Warranty Limited, Insurance and Pure Protection, 2022-H1 has source values
of 88.35% closed within three days and 30.12% closed after three days but
within eight weeks. Together they equal 118.47%.

The extraction has been checked against the source workbook and is correct.
The inconsistency is in the published source values.

## Analyst recommendation

- Preserve both raw published values and their lineage.
- Do not replace either value with zero or silently cap it.
- Exclude the derived combined timeliness measure for this
  firm-product-period from scoring or comparative interpretation.
- Display a source-anomaly warning wherever the affected evidence is shown.
- Require an explicit business decision before any alternative treatment.

## Decision status

`pending_business_review`. The recommended treatment prevents a known
inconsistency from becoming a misleading derived measure while retaining the
original evidence.
