# CBC index measurement rule
Status: TIMING_RECONSTRUCTION = NOT_FEASIBLE for a validated index admission, angiography, or first diagnosis using recovered materials alone.

Direct code: `scripts/06_hits_ami_predevelopment_v0_2.py` lines 335-390, archived in `09_CODE/source_excerpts/cohort_selection.txt`.
One flat master row is selected per patient. Lexicographic ranking: nonblank discharge diagnosis (descending); raw nonmissing count of absolute Neut/Lymph/Mono/PLT (descending); parsable WBC timestamp present (descending); pre-existing qc_nonmissing_count (descending); source-row position (ascending). Patient key is the grouping key. No chronological minimum/maximum or pre-event check is applied. CBC/fibrinogen are read from that selected row, not selected independently from a longitudinal laboratory table. The upstream test-selection ETL is not recovered.

All seven CBC timestamps match WBC time in 1820/1820 selected analysis rows. This supports within-row CBC timestamp consistency, not admission-first sampling, specimen identity or pre-AMI/pre-angiography status. Timestamp label is test_time; collection-versus-report-time semantics remain unverified.

Admission dates are present in 130/1820. Arithmetic CBC-minus-admission median is -1754.205 days (IQR -3055.304 to -30.604), 99 before/31 after, 19 same calendar day. Before/after timestamps and same-calendar-day counts overlap by definition. These implausibly long gaps forbid an interpretation as validated within-index-hospitalization timing. No dedicated angiography/PCI/initial-AMI/discharge-diagnosis timestamp recovered in master headers/dictionary. Admission/discharge vsn tokens exist but are not dates. No imaging/treatment source export or selection ETL recovered in the inspected project/archive.

Fibrinogen timestamps: 1707; numeric fibrinogen: 1705. Fbg-CBC same calendar day: 1553/1707 (90.978%). Median difference is about 0.000440 days. Laboratory proximity does not repair encounter linkage. See descriptive timing CSVs; do not delete negative-time cases or rebuild the cohort in WP1.

Honest reporting rule for future WP3: a laboratory panel carried by the selected completeness-ranked patient record. Do not call it admission-first or pre-angiography. Exact recruitment period and hospital encounter require author/source verification.
