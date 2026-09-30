# CBC Measurement-Selection Rule: Final

## Executable Rule

The historical HITS selector chooses one row per `patient_sn` from the cleaned wide master. It sorts by the following priorities, in order:

1. Non-empty discharge diagnosis, descending.
2. Count of nonmissing required absolute Neut, Lymph, Mono, and PLT values, descending.
3. Availability of a parseable WBC `test_time`, descending.
4. Existing `qc_nonmissing_count`, descending.
5. Original source-row position, ascending, as the deterministic tie-breaker.

The first row after that stable sort is retained. `build_patient_frame` then reads CBC, fibrinogen, diagnosis, admission date, and other mapped values from that selected flat row. It does not select each lab independently from a longitudinal test table.

## What This Rule Does Not Mean

It is **not** a first-admission, first-CBC, earliest-CBC, most-recent-CBC, pre-AMI, pre-angiography, or pre-intervention rule. Timestamp availability affects selection, but chronology does not. The source row is not proven to be a unique hospitalization or laboratory specimen.

The upstream definition and field composition of `qc_nonmissing_count` were not recovered. Discharge-diagnosis availability explicitly affects the ranking, so the row choice is not outcome-blind with respect to diagnosis availability; the ranking does not directly use AMI class or model performance. Do not claim that the rule avoids all outcome-related selection.

## Timestamp Findings in the Frozen Cohort

- A WBC/CBC timestamp is present in 1,820/1,820 selected analysis rows.
- Neut, Lymph, Mono, PLT, MPV, RDW, and Hb timestamps also match the WBC timestamp within the selected flat row in 1,820/1,820 patients for each listed variable.
- This exact within-row timestamp agreement supports a shared timestamp representation in the flat export. It does not establish specimen identity, analyzer run identity, encounter identity, or index-hospitalization timing.
- The same historical row rule and cohort are used for the aggregate timing tables. No patient-level selected rows were exported.

Executable source: `scripts/06_hits_ami_predevelopment_v0_2.py`, SHA-256 recorded in `09_CODE/SOURCE_HASHES.csv`. Selection fields and code locations were rechecked locally in `select_one_row_per_patient` and `build_patient_frame`.
