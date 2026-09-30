# WP3.1 QA status

**Gate: WP3_1_HOLD_SOURCE_DATE_LINEAGE**

The user-confirmed original manuscript was used as the template, and the supplied Editor and Reviewer letters were recovered verbatim. The source-date audit identifies a material unresolved discrepancy: the manuscript states an angiography study period of 1 January 2020 to 1 January 2026, while the selected CBC timestamps span 2009-2026 and 1,802/1,820 are before 2019. The documented +/-182-day shift cannot explain that difference, and the analytic-input-to-shift-output linkage has not been verified. The date-axis analysis is therefore described as exploratory, not temporal validation; this unresolved lineage issue prevents a submission-ready PASS.

The revised manuscript preserves the original section sequence, paragraph order, tables, declarations order, and reference list. The Introduction is unchanged. Table 1 age values were rebuilt from the current source vector. The clinical comparison uses N=1,705; Clinical+Core-7 versus Clinical+PIV is reported as ΔAUC 0.0130 (95% CI 0.0004-0.0251). No statistical models were rerun.

All five main figures and four supplementary figures are generated in R from the included source-data CSVs. Each figure has a reproducible R script; shared helpers are included, and scripts resolve inputs relative to the package. Vector PDFs and 600-dpi TIFF/PNG files are included. All nine figure exports were visually reviewed against the recovered original figure set where applicable. The clean and marked manuscripts (29 pages each) and point-by-point response (7 pages) were rendered and visually checked.

No patient-level data, direct identifiers, or patient-level predictions are included. No statistical models were rerun. This package is for author/editorial review and is not submission authorization.
