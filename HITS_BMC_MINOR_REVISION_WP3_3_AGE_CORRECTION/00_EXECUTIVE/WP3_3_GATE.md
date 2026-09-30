# WP3.3 gate

`WP3_3_HOLD_TARGET_DATE_NOT_RECONSTRUCTABLE`

## Basis

1. No source-confirmed target hospitalization/CAG date is linked to the 1,820-person analysis cohort.
2. The only parsed `admission_date` covers 130 people and has an unverified encounter meaning; 80 of those dates precede 2020.
3. The prohibited legacy CBC/WBC timestamp supplied the historical age fallback for 1,690 people.
4. The frozen V0.5 temporal code contradicts the WP3.2 submission-facing source-date lineage statement.

## Consequence

Do not infer a target-anchored age, copy forward the old age-dependent clinical metrics, patch the manuscript, or upload the WP3.2 files to BMC. This package documents the gate only. It neither changes nor validates the frozen hematologic estimates.

## Release requirements

Patient/encounter-level source and clinical-field owner sign-off for the 2020-2026 index date; join/coverage and shifted-date consistency audit; corrected age and prespecified four-model reanalysis on frozen folds; separate executable temporal-lineage reconciliation; document/figure QA; final author review. PR #1 must remain open and unmerged until these are resolved.
