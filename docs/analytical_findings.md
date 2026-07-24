# Analytical findings and management actions

## Purpose and scope

This report answers the current release question:

> Which FCA firm-product-period observations show the strongest combination of complaint-volume, context-rate, complaint-outcome and timeliness signals, and which should be investigated first?

It uses the processed FCA firm-level complaints release covering 2021-H1 to
2025-H2. The main analytical unit is a firm, product group and reporting
period. Findings were calculated from the validated reporting tables, with
2025-H2 treated as the latest period.

The warning methodology is an analytical prioritisation tool. A signal is not
evidence of customer harm or misconduct, and a score is not an estimate of
financial exposure. Management investigation and business approval remain
necessary.

## Executive conclusion

The latest period contains 578 firm-product observations. Of these:

- 13 (2.2%) are in `priority_review`;
- 113 (19.6%) are in `review`;
- 45 (7.8%) are in `monitor`;
- 336 (58.1%) have no current signal; and
- 71 (12.3%) have insufficient eligible evidence.

The immediate investigation queue is small enough to manage, but it is not
uniformly distributed. Seven of the 13 priority observations are in Insurance
and Pure Protection, and three are in Decumulation and Pensions. Several cases
also recur across multiple reporting periods. Management should begin with
these persistent cases, then examine the dominant timeliness and complaint-
outcome signals, while treating incomplete Consumer Credit evidence and all
`insufficient_data` results as data limitations rather than low-risk outcomes.

## Finding 1: a small group of cases persists across reporting periods

The strongest evidence is not a single high score. It is the repeated
classification of the same firm-product combination over time.

| Firm-product combination | Priority periods | Priority range | Latest status | Latest score |
|---|---:|---|---|---:|
| SCOTTISH WIDOWS LIMITED — Investments | 10 | 2021-H1 to 2025-H2 | Priority review | 8 |
| British Gas Services Limited — Insurance and Pure Protection | 9 | 2021-H2 to 2025-H2 | Priority review | 8 |
| ManyPets Ltd — Insurance and Pure Protection | 6 | 2022-H2 to 2025-H2 | Priority review | 8 |
| OVO HOME SERVICES LTD — Insurance and Pure Protection | 5 | 2021-H2 to 2025-H2 | Priority review | 8 |
| Elderbridge Limited — Home Finance | 4 | 2024-H1 to 2025-H2 | Priority review | 8 |
| Scottish Equitable Plc — Investments | 3 | 2024-H2 to 2025-H2 | Priority review | 11 |

SCOTTISH WIDOWS LIMITED in Investments is the clearest persistent case: it
appears in the priority queue in all ten periods and has at least one
persistent rule in nine of them. British Gas Services Limited is a priority
case in nine periods, all with persistent-rule evidence.

**Management action:** open a longitudinal root-cause review for the six cases
above. Review the underlying metrics and rule evidence across periods, not
only the latest score. Record whether the pattern reflects operational
complaint handling, business mix, reporting practice or another supported
cause. The result should be a documented decision, not an automatic adverse
finding.

## Finding 2: the latest priority workload is concentrated in insurance and pensions

The 13 latest priority observations are distributed as follows:

| Product group | Total observations | Priority | Priority rate | Review | Review rate |
|---|---:|---:|---:|---:|---:|
| Insurance and Pure Protection | 163 | 7 | 4.3% | 40 | 24.5% |
| Decumulation and Pensions | 63 | 3 | 4.8% | 15 | 23.8% |
| Investments | 70 | 2 | 2.9% | 19 | 27.1% |
| Home Finance | 65 | 1 | 1.5% | 10 | 15.4% |
| Banking and Credit Cards | 66 | 0 | 0.0% | 14 | 21.2% |
| Consumer Credit | 151 | 0 | 0.0% | 15 | 9.9% |

Insurance and Pure Protection has the largest priority count. Decumulation
and Pensions has the highest priority rate, although its population is much
smaller. Investments has no fewer concerns: it has the highest review rate
and includes two latest priority cases.

**Management action:** allocate the first investigation capacity to Insurance
and Pure Protection and Decumulation and Pensions, then to the persistent
Investments cases. Maintain diagnostic review of the wider `review` population
rather than interpreting the absence of a priority case in Banking or
Consumer Credit as evidence of good outcomes.

## Finding 3: timeliness and upheld outcomes dominate the latest rule evidence

Latest-period triggered-rule counts are:

| Rule | Triggered observations | Persistent triggers |
|---|---:|---:|
| At least 10% closed beyond eight weeks, upper peer quartile and at least 20 closed complaints | 63 | 33 |
| Upheld percentage in highest peer decile with at least 20 closed complaints | 39 | 28 |
| Provision context rate in highest peer decile | 33 | 24 |
| Upheld percentage increased by at least five percentage points | 27 | 2 |
| Opened complaints at least doubled and current volume is at least 100 | 26 | 5 |

The rule counts overlap: one observation can trigger several rules. They
therefore describe the composition of the evidence, not a count of distinct
firms at risk. Nevertheless, the high number of persistent timeliness,
upheld-percentage and provision-context triggers shows that the current
workload is not driven by complaint volume alone.

**Management action:** structure case reviews around three questions:

1. Why are complaints remaining open beyond eight weeks?
2. Why is the uphold percentage high relative to relevant product-period
   peers?
3. Does a high published context rate reflect operational performance,
   business mix, the source denominator or a definition issue?

Do not compare provision and intermediation context rates as if they were the
same measure; their denominators and business meanings differ.

## Finding 4: Consumer Credit shows volume pressure but incomplete analytical coverage

For Consumer Credit in 2025-H2:

- the median firm-level change in opened complaints is +18.2% across 142
  comparable observations;
- 26 observations are in `monitor`, the highest monitor count of any product;
- 142 of 151 observations have partial coverage and nine have limited
  coverage; none has broad coverage; and
- closure-timeliness and published context-rate measures are unavailable in
  the current analytical table.

This combination explains why volume pressure can be visible without creating
a priority classification based on several independent signal families. The
absence of a Consumer Credit priority case is therefore not a low-risk
conclusion.

**Management action:** create a Consumer Credit monitoring workstream focused
on sustained volume growth and repeat exceptional-growth cases. Keep the
result separate from the multi-signal priority queue until comparable
timeliness and context evidence is available or the business explicitly
approves a product-specific methodology.

## Finding 5: insufficient evidence remains a material part of the workload

There are 71 latest-period `insufficient_data` observations, equal to 12.3% of
the latest population.

| Product group | Insufficient observations | Share of product observations |
|---|---:|---:|
| Home Finance | 17 | 26.2% |
| Investments | 12 | 17.1% |
| Decumulation and Pensions | 10 | 15.9% |
| Banking and Credit Cards | 10 | 15.2% |
| Insurance and Pure Protection | 13 | 8.0% |
| Consumer Credit | 9 | 6.0% |

Home Finance has the highest proportion of insufficient results. These cases
do not have enough eligible rule evidence for classification; they must not be
combined with `no_current_signal`.

**Management action:** assign ownership for the 71 cases and classify the
reason for insufficient evidence: source absence, unsuitable denominator,
minimum-volume requirement, missing prior-period comparison or another rule-
eligibility condition. Prioritise Home Finance because more than one quarter
of its latest observations are affected.

## Recommended management sequence

1. Review the six persistent cases in Finding 1 using their full period
   history and source evidence.
2. Complete the remaining latest priority queue, beginning with Insurance and
   Pure Protection and Decumulation and Pensions.
3. Investigate timeliness, uphold and context-rate drivers using the
   rule-level evidence rather than the final score alone.
4. Establish a separate Consumer Credit volume-monitoring process.
5. Resolve or formally accept the 71 insufficient-evidence cases.
6. Obtain business-owner approval for the warning methodology before any
   operational deployment.

## Interpretation limits

- Reporting populations and source windows can differ by period. Aggregate
  count changes must not be interpreted as like-for-like market growth without
  checking population and period comparability.
- FCA context measures use published denominators. `per 1,000` rates and exact
  counts are not interchangeable.
- Percentages above 100% found in source workbooks are preserved. A confirmed
  historical source inconsistency remains documented and requires business
  treatment before using a derived timeliness measure.
- Peer percentiles are descriptive comparisons within a product and reporting
  period. They do not estimate causal harm.
- Unresolved firm identities retain stable name-based keys and must not be
  silently assigned an FRN.
- Scores support workload ordering. They do not measure probability, severity,
  redress or financial exposure.

## Reproducible evidence

The findings use:

- `data/processed/reporting/dashboard_firm_product_period.csv` for observation
  bands, scores, coverage, trends and reviewed dispositions;
- `data/processed/reporting/dashboard_warning_rule_detail.csv` for triggered
  and persistent rule counts; and
- the definitions and limitations in `docs/warning_methodology.md`,
  `docs/warning_methodology_v2.md` and `docs/business_case.md`.

The report was prepared from generated outputs rather than manually copied
Tableau values. Tableau remains a presentation layer and can be updated
separately.
