# WP3.3 final QA

| Check | Status | Evidence |
| --- | --- | --- |
| Frozen cohort selector | PASS | 2,548 raw rows, 2,279 selected patients, 1,820 primary patients, 453 AMI |
| Master source hash | PASS | `f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660` |
| Target age source | HOLD | No source-confirmed patient-linked index date |
| Old WBC/CBC age fallback excluded | PASS | No new age computed; historical metrics explicitly superseded for submission use |
| Temporal source description | HOLD | Archived V0.5 code uses 2015/CBC, conflicting with WP3.2 date-axis statement |
| Four clinical models / DCA | NOT_PROCESSED | Prohibited without valid target age |
| Table 1 / manuscript / response patch | NOT_PROCESSED | Analysis gate not passed |
| Core/PIV/Enhanced hematologic results | UNCHANGED | No frozen model script or output edited; validity not newly assessed |
| Patient-level content in WP3.3 package | PASS | Aggregate CSVs, metadata, and script only; no row-level data |
| Submission readiness | FAIL | WP3.2 submission-ready claim superseded by WP3.3 HOLD |

The aggregate audit can be rerun locally with Python containing pandas, numpy, matplotlib, and scikit-learn:

```text
python3 -B 05_QA/audit_wp3_3_sources.py \
  --master /local/private/master_cohort_cleaned.csv \
  --selector /local/HITS/scripts/06_hits_ami_predevelopment_v0_2.py \
  --temporal-script /local/HITS/scripts/12_hits_v0_5_shift_robust_validation.py \
  --output /local/public/HITS_BMC_MINOR_REVISION_WP3_3_AGE_CORRECTION
```

The script writes only aggregate counts and fingerprints. It does not export IDs, patient dates, ages, predictions, or row-level classifications.
