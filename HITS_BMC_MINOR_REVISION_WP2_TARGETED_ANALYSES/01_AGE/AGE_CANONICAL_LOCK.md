# Canonical Age Definition Lock

**Status:** `AGE_1820_CANONICAL_LOCKED`

The frozen V0.3.1 clinical models build their patient frame through the hash-verified V0.2 cohort script. The canonical derivation is: primary `birth_date`, then `基线_birth_date` only as fallback; reference date is `admission_date`, with `lab_blood_routine_examination_WBC_test_time` as fallback; age is elapsed days divided by 365.2425; values outside the inclusive 18–120 year range are set missing. The input is the previously audited master cohort (SHA-256 `f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660`), and the executed V0.2 script SHA-256 is `089924ec5a58d09c3e96bdedd2a9316690eebd3f70377a058760a90b267ad91a`.

The canonical primary cohort contains 1820 patients: 453 AMI and 1367 non-AMI CAD. Age is available for 1820/1820 (453 AMI; 1367 non-AMI). The recovered V0.3.1 script uses this vector in the 4-variable clinical baseline and clinical-incremental models; those models retain all eligible patients and use the canonical fold-local median preprocessing for missing clinical predictors.

The submitted Table 1 reports 1,818/1,820 (AMI 452/453; non-AMI 1,366/1,367). No executable correction reproducing that two-person difference was recovered. The reported line is therefore retained only as a separate, unverified reporting branch; it is not the canonical clinical-model age vector. Its exact two records and cause remain unresolved. WP3 should rebuild the Table 1 age row from the locked vector and report the correction. This WP2 task does not edit the manuscript.

Reference-date use is not equivalent to a validated index-admission time anchor. CBC-date fallback counts and the unresolved encounter-linkage limitation are reported in `AGE_CANONICAL_QC.csv` and remain subject to the locked timing claim boundary.
