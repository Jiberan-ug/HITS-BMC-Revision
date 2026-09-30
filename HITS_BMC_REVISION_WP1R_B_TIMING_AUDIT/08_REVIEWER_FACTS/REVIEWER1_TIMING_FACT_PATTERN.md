# Reviewer 1: Timing Fact Pattern

**Document type:** factual fields only; not a drafted rebuttal.

- **Admission timing:** `admission_date` paired with selected CBC timestamp in 130/1,820 (7.14%). Date-level relation only: 99 before, 19 same calendar date, 12 after. The field is sparse and not validated as the index CAG admission; exact hour ordering is not claimed.
- **Symptom onset:** `NOT AVAILABLE`. No onset date/time was identified. It is not inferred from admission date.
- **Initial AMI diagnosis timing:** `NOT AVAILABLE`. Phenotype remains the frozen discharge-diagnosis text rule. Discharge date is unavailable and is not treated as diagnosis time.
- **Angiography/CAG timing:** `NOT AVAILABLE` in the recovered HITS source. No angiography date/time field or episode-linked angiography list was recovered.
- **Treatment / PCI / major intervention timing:** `NOT AVAILABLE` in the recovered HITS source. No procedure date/time field was recovered.
- **Troponin timing fields in the frozen HITS cohort:** cTnT timestamp 90/1,820; cTnI 173/1,820; hs-cTnT 402/1,820; CK-MB 1/1,820. No dedicated hs-cTnI field was recovered. Assay-specific initial-diagnosis linkage, serial rise/fall, platform/generation, and validated reference-limit context are unavailable; duplicate-named columns are not counted as additional assays. Troponin is not used to redefine the phenotype or establish the initial AMI time.
- **Index CBC rule:** completeness-ranked selected flat row: non-empty discharge diagnosis, number of available absolute Neut/Lymph/Mono/PLT values, WBC timestamp availability, `qc_nonmissing_count`, then source-row order. Not a first/earliest or proven pre-event CBC.
- **Index-episode status:** direct=0; unique stay-window=0; partial clinical timing=0; unverified=1,820. Same-index-hospitalization CBC is unconfirmed for all patients; UNKNOWN is not recoded as NO.
- **Study period:** 2020–2026 author-confirmed; machine verification not recovered.
