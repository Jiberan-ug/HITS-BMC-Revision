# CBC Date Semantics Audit

## Finding

The raw primary mother file contains laboratory `test_time` fields, but its recovered structure does not establish whether a timestamp is the index-admission CBC, an older historical test, the earliest-ever test, or another record selected/merged into the wide export. The correct status is **UNKNOWN**. Dates before 2019 are compatible with historical laboratory records for patients later selected under a 2020–2026 angiography eligibility rule, but this interpretation is not demonstrated by the available source structure.

## Evidence

- The primary mother file has 2,548 rows and 431 columns. It includes admission date and CBC test timestamps, but no discharge date, CAG date, PCI date, procedure date, encounter ID, or visit ID field was identified in the recovered column names.
- WBC test time is populated in 2,268 source rows; 2,249 of those timestamps are before 2019. Fibrinogen test time is populated in 2,128 rows; 2,109 are before 2019.
- Among the 146 rows with both a parseable WBC test time and admission date, the median WBC-minus-admission difference is -1,771.48 days; 111 precede and 35 follow the listed admission date, and 21 fall on the same calendar day. Fibrinogen/admission comparison is available for 140 rows: median -1,632.65 days, 105 precede, 35 follow, and 20 share a calendar day.
- These arithmetic comparisons are not same-encounter matches. The export does not expose the encounter relationship needed to interpret them clinically.
- The HITS analysis master’s mapped CBC timestamps match a source row for all 2,279 patients; this establishes patient-level timestamp lineage, not index-encounter semantics.

## Determination

`CBC_DATE_SEMANTICS = UNKNOWN`; `INDEX_ENCOUNTER_CBC = NOT_ESTABLISHED`. Do not use CBC year as recruitment period, do not label these measurements admission-first or pre-angiography, and do not treat the pre-2019 values as evidence that cohort eligibility began before 2020. The source owner confirmed that eligibility was based on 2020–2026 coronary angiography, but no recovered query or date field machine-verifies this rule.

Temporal-validation code execution and the validity of its calendar-time interpretation are separate. Until the model-input date is linked to an eligible index encounter and the date-shift lineage is verified, the frozen temporal analysis is **not credible as temporal transportability evidence**. Its already-frozen numerical outputs are not recalculated or overwritten in WP1R.
