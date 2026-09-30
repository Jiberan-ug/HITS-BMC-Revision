# Editor Comment 1: Timing Fact Pattern

**Document type:** factual fields only; not a drafted rebuttal.

- Historical measurement rule: one flat row per patient, ranked by diagnosis availability, count of nonmissing absolute Neut/Lymph/Mono/PLT, WBC timestamp availability, `qc_nonmissing_count`, then original row order. Not first/earliest CBC, not first admission, and not pre-event selection.
- Primary cohort: N=1,820; AMI=453; non-AMI CAD=1,367.
- Selected-row CBC timestamp availability: 1,820/1,820 (100%). Timestamp availability is not index-encounter linkage.
- CBC plus listed admission date: 130/1,820 (7.14%). Date-level comparison: 99/130 earlier, 19/130 same calendar date, 12/130 later. Index-stay relation is unverified.
- Direct encounter / unique stay-window / partial clinical timing: 0/1,820 / 0/1,820 / 0/1,820.
- Same-index-hospitalization CBC confirmed: 0. Interpretable linkage denominator=0; 1,820 status UNKNOWN, not NO.
- CBC before angiography: 0/0 interpretable CBC–angiography pairs; not estimable because no angiography/CAG timestamp was recovered.
- CBC before initial AMI diagnosis: 0/0 AMI patients with valid initial-diagnosis time; not estimable. Discharge diagnosis date/time was not substituted.
- Fibrinogen timestamp: 1,707/1,820 (93.79%); value: 1,705/1,820 (93.68%); paired Fbg/CBC timestamps: 1,707/1,820 (93.79%).
- Fibrinogen relative to CBC among 1,707 timestamp pairs: same calendar date 1,553/1,707 (90.98%); earlier calendar date 41/1,707 (2.40%); later calendar date 113/1,707 (6.62%). Exact timestamp ordering: earlier 727/1,707; equal 1/1,707; later 979/1,707.
- Fibrinogen same index hospitalization confirmed: 0; interpretable stay-linkage denominator=0; UNKNOWN among all 1,707 timed values.
- Fibrinogen before angiography: 0/0 interpretable pairs; not estimable.
- Timing unverified: 1,820/1,820 (100%).
- Missing source elements: explicit encounter-to-lab key, discharge date/time, CAG/angiography and PCI/procedure dates, and initial AMI diagnosis date/time.
- Interpretation constraint: temporal proximity and same-calendar-day timing are not evidence of a shared encounter.
