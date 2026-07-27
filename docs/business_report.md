# UK Financial Complaints Intelligence: Plain-English Business Report

## Purpose of this report

This project helps answer one practical business question:

> When review time is limited, which firm-and-product cases should an analyst investigate first, and what evidence supports that decision?

The system does not decide that a firm has harmed customers or behaved improperly. It organises a large and difficult dataset, identifies unusual patterns, and gives a reviewer enough evidence to decide where further investigation is most useful.

This report explains the project without assuming financial-services knowledge. It uses the current generated reporting tables, covering data through **2025-H2**, as its source of truth.

## Executive summary

The latest period contains:

- **293 firms**
- **578 firm-product observations**
- **13 highest-priority observations**
- **113 additional observations marked for review**
- **45 observations to monitor**
- **71 observations with insufficient data**
- **336 observations with no current warning signal**

An observation is one firm, one product group and one reporting period. It is not an individual complaint or customer.

The main business message is not that 126 observations are “bad.” It is that **126 observations, or 21.8% of the latest set, contain enough warning evidence to justify review**, with 13 placed at the front of the queue.

Insurance and pure protection has the largest number of highest-priority observations: **7 out of 163** observations in that product group. However, decumulation and pensions has a slightly higher proportion: **3 out of 63**. This illustrates an important analytical distinction:

- Counts tell us where the greatest review workload sits.
- Rates tell us where signals are most concentrated relative to the size of the group.

The most common rule signal is an unusually high proportion of complaints closed after eight weeks. This rule triggered **63 times** in the latest period. High upheld percentages relative to peers triggered 39 times, and high provision-context rates relative to peers triggered 33 times. Rules can overlap, so these figures must not be added together as if they represented separate firms.

Total complaints opened rose sharply to **5,457,584**, up 56.1% from the preceding period. Almost all of this change comes from Consumer Credit. Its reported total increased from 1,756,172 to 3,805,146. Excluding Consumer Credit, complaints opened across the other product groups actually fell by approximately 5.0%.

That finding should prompt a comparability and data-definition check before a business conclusion. A sudden increase can reflect real customer pressure, but it can also reflect changes in reporting coverage, firm populations, classifications or source definitions. The project therefore treats it as a question to investigate, not proof of worsening harm.

## 1. What business problem are we solving?

A complaints team may receive information about hundreds of firms and several product groups every six months. It cannot investigate every number with equal effort.

The real problem is therefore prioritisation:

1. Which observations show the strongest combination of warning signs?
2. Which observations have repeated warning signs over time?
3. Which observations are unusual compared with similar firms?
4. Which numbers can be traced back to their original workbook cells?
5. Which observations do not contain enough information for a fair conclusion?

Without a structured process, people may focus only on the largest firms, the biggest raw complaint totals, or a dramatic percentage seen in isolation. That can lead to poor decisions. A large firm may naturally receive more complaints because it serves more customers, while a smaller firm may show a more unusual complaint rate or worsening handling outcome.

This project combines those different perspectives and creates a review queue. It helps an analyst spend time where it is likely to produce the most useful follow-up.

## 2. Why should a business care?

Complaint data is an early indication that customers may be experiencing problems. It can reveal:

- growing operational pressure;
- slower complaint handling;
- a high proportion of complaints where the firm agreed with the customer;
- unusual complaint volumes relative to business activity;
- repeated deterioration across reporting periods; or
- incomplete data that makes confident assessment impossible.

The value of the project is not merely producing charts. It creates a controlled path from raw source files to a business decision:

> raw evidence → checked data → comparable measures → warning signals → prioritised review

This matters because decisions made from poor-quality, misunderstood or non-comparable data can waste review time and unfairly characterise firms.

## 3. What the data sources mean

### Financial Conduct Authority data

The FCA data describes complaints reported by firms. It includes complaint volumes, closure timing, upheld percentages and complaint figures placed in the context of business volumes.

In plain English, this is the main dataset used to ask:

- How many complaints were reported?
- Is the number changing?
- How quickly were complaints closed?
- How often did the firm agree with the complainant?
- Is the complaint level unusual when compared with the scale of business?

### Bank of England data

Bank Rate is included as economic background. Changes in interest rates can affect borrowing costs and household finances, which may influence the environment in which complaints arise.

It is not used to increase or decrease a firm's warning score. A similar movement in Bank Rate and complaints does not prove that one caused the other.

### Office for National Statistics data

CPI and CPIH inflation are also included as background. Inflation can create financial pressure for households and businesses.

Again, the figures support interpretation only. They do not prove why a particular firm received complaints.

### Financial Ombudsman Service data

The project currently contains a mapping between FCA product groups and FOS categories. It does not yet contain a complete, validated set of FOS outcomes for direct comparison.

FOS information could later provide a useful independent view of complaints escalated beyond firms. Until that integration is completed, this project should not claim that FCA warning scores agree or disagree with Ombudsman outcomes.

## 4. What the pipeline does

The project performs the following work:

1. **Discovers source workbooks** and records their sheets.
2. **Profiles the files** to understand headers, dimensions, data types, missing values and structural differences.
3. **Handles different sheet purposes**, including main data, notes and joint-reporter information.
4. **Extracts values without altering the raw workbooks.**
5. **Preserves source lineage**, including workbook, sheet, row, column and cell references.
6. **Standardises firms and product groups** while retaining original values.
7. **Reconciles totals** so extracted data can be checked against the source.
8. **Builds analysis-ready tables** at firm-product-period level.
9. **Creates comparison features**, such as change from the previous period and position relative to peers.
10. **Applies transparent warning rules** and creates review queues.
11. **Presents the results in Tableau**, including executive, firm, rule and data-quality views.

The key strength is traceability. When a warning appears, an analyst can inspect the underlying rule and return to the source evidence instead of treating a score as a mysterious result.

## 5. Current findings

### 5.1 Size and status of the latest portfolio

The 578 observations in 2025-H2 are classified as follows:

| Status | Observations | Share | Plain-English meaning |
|---|---:|---:|---|
| Highest priority | 13 | 2.2% | Review these first |
| Review | 113 | 19.6% | Warning evidence justifies investigation |
| Monitor | 45 | 7.8% | Some evidence exists, but it is weaker |
| Insufficient data | 71 | 12.3% | A reliable warning classification cannot be made |
| No current signal | 336 | 58.1% | No configured rule currently triggers |

“No current signal” does not mean “no customer risk.” It only means the available data did not trigger the current rules.

“Insufficient data” is especially important. It must remain separate from low risk because missing evidence is not reassuring evidence.

### 5.2 Where the review workload sits

| Product group | All observations | Highest priority | Highest-priority rate |
|---|---:|---:|---:|
| Insurance and pure protection | 163 | 7 | 4.3% |
| Consumer Credit | 151 | 0 | 0.0% |
| Investments | 70 | 2 | 2.9% |
| Banking and credit cards | 66 | 0 | 0.0% |
| Home finance | 65 | 1 | 1.5% |
| Decumulation and pensions | 63 | 3 | 4.8% |

Insurance contains the largest number of highest-priority cases, so it creates the greatest immediate workload. Pensions has the highest concentration, although the difference is small and the numbers are limited.

This does not demonstrate that either sector is generally worse. It identifies where the current rules have concentrated review cases.

### 5.3 The warning patterns that appear most often

The most frequent latest-period rule triggers are:

| Rule theme | Triggers | Plain-English interpretation |
|---|---:|---|
| High share closed after eight weeks | 63 | Complaint handling appears slow relative to the rule threshold and peers |
| High upheld percentage compared with peers | 39 | The firm agreed with customers unusually often compared with similar observations |
| High provision-context rate compared with peers | 33 | Complaints were high relative to the relevant provision business measure |
| Upheld percentage deteriorated | 27 | The upheld percentage increased materially from the preceding period |
| Exceptional growth in complaints opened | 26 | Complaint volume at least doubled and was large enough to be meaningful |

These are screening rules, not findings. One observation can trigger several rules, and some rules may be more informative than others depending on data coverage and product definitions.

### 5.4 Highest-priority examples

The highest scores in the latest queue include:

- **Embark Services Ltd — Decumulation and pensions — score 13**
- **Scottish Equitable Plc — Investments — score 11**
- **Coutts & Company — Decumulation and pensions — score 9**

These should be described as the first cases for analytical review, not as the “worst firms.” The score measures the combination of configured signals; it does not measure the number of harmed customers, financial loss or regulatory severity.

The full queue also records caveats. For example, some observations are retained because they have strong signals but require caution due to limited samples, borderline evidence or source issues.

### 5.5 Complaint-volume change needs investigation

Latest total complaints opened:

- 2025-H1: **3,496,394**
- 2025-H2: **5,457,584**
- Change: **+1,961,190**, or **+56.1%**

Consumer Credit accounts for the change:

- 2025-H1: **1,756,172**
- 2025-H2: **3,805,146**
- Change: **+2,048,974**, or **+116.7%**

Across all other product groups combined:

- 2025-H1: **1,740,222**
- 2025-H2: **1,652,438**
- Change: **−87,784**, or approximately **−5.0%**

The safest conclusion is:

> The overall increase is concentrated in Consumer Credit and should be checked for population, coverage, classification and reporting-definition changes before it is interpreted as a real deterioration in customer outcomes.

This is a stronger analytical answer than simply saying “complaints increased by 56%.”

### 5.6 Economic background

In 2025-H2:

- Bank Rate moved from approximately **4.25% to 3.75%**.
- CPI inflation was approximately **3.4%** at the period end.
- CPIH inflation was approximately **3.6%** at the period end.

These indicators describe the environment in which consumers and firms operated. They may help form questions, such as whether financial pressure or changing borrowing conditions affected particular product groups. They do not establish a causal explanation for the observed complaint patterns.

## 6. Recommended business actions

### Action 1: Check the Consumer Credit increase before interpreting it

Confirm:

- whether the same population of firms is represented in both periods;
- whether product definitions changed;
- whether any source sheets or reporting practices changed;
- whether one or a few large firms explain most of the increase; and
- whether external aggregate publications show the same movement.

Only after those checks should the business decide whether the increase reflects genuine complaint pressure.

### Action 2: Review the 13 highest-priority observations first

For each case:

1. Inspect the triggered rules.
2. Check whether the signal persisted from the previous period.
3. Read any review caveats.
4. Verify the underlying source cells.
5. Compare the firm with suitable peers.
6. Record whether the case should be escalated, monitored or closed.

### Action 3: Treat insurance as the largest workload, not automatically the greatest risk

Insurance contains seven highest-priority observations and 55 observations with any current warning signal. This makes it an efficient area for thematic review.

However, review should still be conducted at firm-product level. The number of signals partly reflects the size of the product group.

### Action 4: Keep insufficient-data cases visible

The 71 insufficient-data observations need a separate data-improvement or follow-up process. They should never be combined with “no current signal.”

The business should record which measures are missing and whether the absence is expected, caused by reporting rules or caused by a data-quality problem.

### Action 5: Use source evidence before communicating a conclusion

Every material conclusion should answer:

- Which reporting period does it cover?
- Is it a count, percentage or rate?
- What is the comparison basis?
- Is the source value complete and valid?
- Can the figure be traced to the original workbook?
- Does the conclusion describe an observation, or does it incorrectly imply causation?

### Action 6: Add FOS validation as a later enhancement

Once suitable FOS outcome data is obtained and mapped, compare the warning queue with independently escalated complaint outcomes. This could test whether the rules identify cases that later show poor outcomes.

Until then, FOS should be described as planned external validation, not completed evidence.

## 7. What the project cannot tell us

The project cannot currently prove:

- that a firm caused customer harm;
- how severe any individual customer outcome was;
- the amount of financial loss or redress;
- why a complaint trend changed;
- that an economic indicator caused complaints;
- that a firm with no current signal is low risk;
- that a high score represents a regulatory breach; or
- that one product group is inherently worse than another.

These limitations are not weaknesses to hide. Stating them clearly is part of professional analysis.

## 8. The most important business concerns

If only five concerns are remembered, they should be these:

1. **Comparability:** Are we comparing the same firms, definitions and reporting coverage across periods?
2. **Data sufficiency:** Is there enough valid information to make a fair classification?
3. **Concentration:** Is a total movement broad-based, or driven by one product group or a few large firms?
4. **Evidence:** Can every important signal be traced back to its source?
5. **Interpretation:** Are we describing an unusual pattern, or accidentally claiming that we have proved customer harm or causation?

These concerns are more useful for business decision-making than memorising financial terminology.

## 9. How to explain the project in an interview

### One-minute version

> I built an end-to-end complaints intelligence project using FCA firm-level workbooks. The business problem was that a review team cannot investigate every firm and product equally, so I created a transparent process to identify where review should start. I profiled changing Excel structures, extracted and reconciled the data, resolved firms, created period and peer comparisons, and applied explainable warning rules. The latest data covers 293 firms and 578 firm-product observations. Thirteen observations are in the highest-priority queue, but I am careful not to call them harmful firms—the result is prioritisation evidence, not proof. I also found that a 56% increase in total complaints was entirely driven by Consumer Credit, which means the correct next step is to check comparability and reporting coverage before claiming deterioration. Tableau dashboards let a reviewer move from the portfolio view to the underlying rule and source cell.

### What this demonstrates

The project shows the ability to:

- translate an unclear business brief into analytical questions;
- inspect and understand unfamiliar source data;
- build a reusable Python data pipeline;
- handle changing Excel structures;
- test and reconcile transformations;
- design analysis-ready tables;
- distinguish counts, rates and percentages;
- compare observations over time and against peers;
- create transparent decision rules;
- communicate limitations and avoid overclaiming;
- build interactive Tableau dashboards; and
- explain findings to non-technical decision-makers.

## 10. Plain-English glossary

**Complaint opened**

A complaint received or recorded during the period.

**Complaint closed**

A complaint for which the firm completed its handling process.

**Upheld complaint**

A complaint where the firm agreed wholly or partly with the customer.

**Closed within three days**

The share of complaints resolved very quickly.

**Closed after three days but within eight weeks**

The share resolved after the quick-resolution window but before the usual eight-week deadline.

**Closed after eight weeks**

A derived indicator for complaints not closed within the two published timing categories. It requires care where source percentages are inconsistent.

**Complaints in context**

A complaint figure divided by a measure of business activity, such as accounts, policies, sales or transactions. It helps compare firms of different sizes.

**Peer comparison**

Comparing an observation with other firms in the same product group and reporting period.

**Persistent signal**

A warning condition that also appeared in the previous period.

**Coverage status**

An indication of how much valid evidence was available for the warning assessment.

**Source anomaly**

A value that was extracted correctly but appears internally unusual or inconsistent in the original source.

**Priority score**

A transparent sum of configured warning evidence used to order review work. It is not a measure of proven harm.

## Data-version note

This report uses the current generated files under `data/processed/reporting` as the numerical source of truth. Earlier narrative documents may contain figures from previous pipeline runs. This is a normal reporting-control issue: when generated data is refreshed, written summaries must also be refreshed before release.
