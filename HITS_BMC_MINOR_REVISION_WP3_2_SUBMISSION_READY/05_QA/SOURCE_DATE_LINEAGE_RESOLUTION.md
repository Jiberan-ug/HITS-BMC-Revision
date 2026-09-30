# Source-Date Lineage Resolution

**Status:** `SOURCE_DATE_LINEAGE_RESOLVED_BY_AUTHOR_SOURCE_CONFIRMATION`

This resolution records author/source-owner confirmation supplied for WP3.2. It is not machine verification, database-query verification, or independent verification.

## Confirmed provenance

- The source cohort comprises patients who underwent coronary angiography from 2020-01-01 through 2026-01-01.
- Hematologic measurements used in Core-7, PIV, and Enhanced analyses were obtained in association with the target hospitalization.
- Historical CBC timestamp fields in the flat research export reflect legacy registration/export inconsistencies. They are not valid anchors for the analyzed measurements' true clinical sampling times.
- The temporal sensitivity analysis used the 2020-2026 hospitalization/coronary-angiography date axis after institutional patient-specific deidentification/date shifting within +/-182 days.
- The anomalous legacy `WBC_test_time` fields were not used to allocate patients to temporal groups.

## Residual limitation

The exact within-hospital CBC sampling time relative to admission, coronary angiography, and AMI diagnosis cannot be reconstructed uniformly. The manuscript therefore describes the measurements as target-hospitalization-associated and does not claim that they were uniformly admission-first, pre-angiography, pre-diagnostic, or pre-treatment.

## Temporal split reporting limitation

`TEMPORAL_SPLIT_CALENDAR_ANCHOR_STATUS=NOT_AVAILABLE_IN_FROZEN_ANALYSIS_RECORD`. The author/source owner confirmed that the 1 January 2015 split and the 2014-2015 date ranges in the earlier draft are stale and must not be used. The WP2 frozen temporal facts preserve the development, buffer, and later group counts and performance estimates but do not preserve a source-verified calendar cutpoint. The submission therefore reports the confirmed 2020-2026 hospitalization/coronary-angiography date source, the patient-specific +/-182-day shift, the six-month buffer, group roles/counts, and the frozen estimates, while explicitly stating that the exact calendar cutpoint is unavailable. No replacement date or new group assignment has been inferred, and no temporal model has been rerun. Historical WP1 audit artifacts remain unchanged and available for context; they are not used to restore the stale 2015 cutpoint to the submission.

## Audit boundary

WP3.2 applies a document and submission-package patch only. No model, cross-validation, bootstrap, ROC, calibration, DCA, or sensitivity analysis was rerun. The WP3.1 historical audit artifacts remain unchanged in the repository; this note resolves the submission-facing interpretation using the new author/source confirmation and does not erase prior audit history.
