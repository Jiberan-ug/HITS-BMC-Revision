# Target-hospitalization age lock

**Definition reserved, not implemented:** (source-confirmed target hospitalization/CAG episode date minus primary `birth_date`, falling back to `基线_birth_date`) / 365.2425; retain 18-120 years. A patient-specific date shift must be applied consistently to both dates or reversed by an approved method before subtraction.

Primary birth dates parse in 1,820/1,820 (AMI 453/453, non-AMI CAD 1,367/1,367). No source-confirmed target episode date is available. Consequently `AGE_AVAILABLE_N=NOT_ESTIMABLE`, `AGE_MISSING_N=NOT_ESTIMABLE`, and the requested Table 1 age summaries are `NOT_PROCESSED`. These are not claims that zero or 1,820 patients are truly missing age; the semantic anchor is unresolved.

The historical `admission_date`/WBC fallback age vector must not be used for submission-facing clinical estimates. Its published/frozen numerical values are retained for provenance only and marked `SUPERSEDED_BY_TARGET_HOSPITALIZATION_AGE` pending correction.
