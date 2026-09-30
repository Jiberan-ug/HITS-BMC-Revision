# WP3.2 Final QA

**Gate:** `WP3_2_PASS_SUBMISSION_READY`

## Status

- `SOURCE_DATE_LINEAGE`: `RESOLVED_BY_AUTHOR_SOURCE_CONFIRMATION`; author/source-owner confirmation only, not machine, database-query, or independent verification.
- `CBC_VALUES`: `TARGET_HOSPITALIZATION_ASSOCIATED`.
- `EXACT_CBC_TIMING`: `NOT_UNIFORMLY_RECONSTRUCTABLE`.
- `LEGACY_WBC_TIMESTAMP`: `NOT_USED_AS_CLINICAL_TIMING_ANCHOR` or temporal-allocation field.
- `TEMPORAL_DATE_AXIS`: `2020_2026_HOSPITALIZATION_ANGIOGRAPHY_DATES_DEIDENTIFIED`.
- `TEMPORAL_SPLIT_CALENDAR_ANCHOR`: `NOT_AVAILABLE_IN_FROZEN_ANALYSIS_RECORD`; the author/source owner confirmed the earlier draft's 2015 split/date ranges were stale. No replacement calendar cutoff or group assignment was inferred.
- `TEMPORAL_ANALYSIS`: `TEMPORAL_SENSITIVITY_NOT_VALIDATION`.
- `STATISTICAL_REANALYSIS`: `NONE`.
- `FIGURE1_STYLE`: `ORIGINAL_STYLE_PRESERVED`; WP3.1 and WP3.2 Figure 1 TIFF SHA-256 values match.
- `MANUSCRIPT_CHANGE_STRATEGY`: `MINIMAL_TARGETED_MINOR_REVISION`.

## Verification

- Numerical crosscheck: PASS against frozen WP2 canonical outputs; no result values were recalculated.
- Comment coverage: PASS, 22/22 Editor/Reviewer comments remain `CLOSED` or `CLOSED_WITH_EXPLICIT_LIMITATION`.
- Internal term scan: PASS; obsolete unresolved source-date HOLD wording and the 2009-2026/1,802/1,820 anomaly framing are absent from submission-facing materials. Timing phrases that appear are explicitly negated or quoted reviewer text. Temporal validation is consistently denied rather than claimed.
- Temporal split reporting: PASS WITH EXPLICIT LIMITATION; the stale 2015 cutpoint was removed on author/source-owner confirmation. The frozen analysis record does not retain a verified calendar cutpoint, so the manuscript and response state this limitation while preserving the frozen group counts and estimates. No calendar value was inferred and no analysis was rerun.
- Document rendering: PASS; clean manuscript 28 pages, marked manuscript 28 pages, response 7 pages, supplementary methods 7 pages. Final clean and response PDFs match the rendered page counts.
- Figure 4: PASS; only label wording changed. All 9 aggregate source rows match WP3.1 in every non-label field. The supplied R script regenerated Figure 4; TIFF export is 600 dpi. No geometry redesign.
- Supplementary tables: PASS; temporal labels and explanatory note updated with Artifact Tool. Numeric cell values and formulas were identical before/after export/import.
- No patient-level raw data are included in this submission package.

No portal submission or PR merge was performed. The response to Editor Comment 5 explicitly notes that the exact calendar cutpoint is unavailable in the retained analysis record. PR #1 remains open for the requested final external audit.
