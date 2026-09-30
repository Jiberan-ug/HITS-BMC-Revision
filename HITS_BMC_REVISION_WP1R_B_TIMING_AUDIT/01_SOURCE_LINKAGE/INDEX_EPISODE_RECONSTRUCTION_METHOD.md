# Index Episode Reconstruction and Source Search

## Frozen Cohort Reconstruction

The audit loaded the historical `select_one_row_per_patient` and `build_patient_frame` function bodies from the V0.2 analysis script's AST. It compiled only those functions and their constants. The analysis `main()` function was not called. The same historical discharge-diagnosis phenotype rule and core-CBC inclusion rule were applied; no phenotype was newly defined. The resulting cohort-size guard was exact: 1,820 total, 453 AMI, 1,367 non-AMI CAD.

No patient-level selection or timing table was written. The only outputs are cohort/group aggregates, schema-level source metadata, and source hashes.

## Evidence Hierarchy Applied

- **Direct encounter linkage:** not established. No explicit encounter/visit/admission key ties the selected lab row to the eligible CAG episode.
- **Unique stay-window linkage:** not established. A complete, unique admission-and-discharge window and linked CAG/AMI episode are unavailable.
- **Partial clinical timing linkage:** not established. No linked angiography, intervention, or initial AMI diagnosis time supports event ordering.
- **Unverified:** applies to all 1,820 analysis patients for index-episode timing. UNKNOWN was retained; it was not converted to NO.

The lab timestamp itself is available, and CBC/fibrinogen timestamps can be compared with one another. That is laboratory-time arithmetic, not evidence that a test belongs to the eligible index hospitalization.

## Source-Field Review

The original mother export has 2,548 rows and 431 columns, with 2,279 unique patient identifiers. It contains patient-level keys, `admission_date` in a sparse subset, discharge-diagnosis text, CBC timestamps, fibrinogen timestamps, and limited troponin timestamps. Its identified structure lacks discharge date/time, CAG/angiography date/time, PCI/procedure date/time, and an initial AMI diagnosis timestamp. Two inpatient-number/token columns are present, but they are not linked specifically to each lab row or the index angiography encounter. Row grain remains patient-linked/wide and not proven to represent a hospitalization.

The Scheme C ZIP has 11 members: cleaned master; MACE-positive, MACE-negative, and positive-extended tables; a recommended-model draft; field dictionary; README; patient crosswalk; file-relationship table; duplicate audit; and missingness summary. The ZIP contains no hospitalization-level procedure or laboratory event table. Its patient crosswalk supports dataset membership only, not CBC-to-encounter linkage.

The deidentified lineage master is derived from the same source master. Its dates are shifted by patient and preserve within-patient intervals; they are not independent clinical date evidence. Its `visit_id_hash_list` is generated from `inpatient_no_id` and baseline inpatient-number fields, then aggregated per patient. It is not an event-specific `visit_id` attached to each laboratory specimen. It therefore does not upgrade the linkage level or provide an independent source.

The previously generated Information Score encounter/CBC audits contain 1,658 records, all marked `INDEX_ENCOUNTER_NOT_RECOVERABLE`. They are derived patient-level timing audits, not independent HIS/LIS/procedure exports, and they are not the frozen HITS N=1,820 cohort. Their date arithmetic was not transferred as patient-level evidence or used to label HITS cases.

The local filename/schema review also surfaced CAG/PCI artifacts in unrelated project directories. They were excluded because their cohort/source provenance does not establish identity overlap with the HITS source. No protected identifiers were uploaded or copied into this package.

## Search Scope and Result

Searched relevant local HITS/Article-5 directories, source-raw and data-raw/EHR-extracted folders, Downloads, the TwoPapers Scheme C bundle and metadata, the deidentified cohort-lineage package, and historical Information Score source-recovery/timing outputs. WP1R-A had found three of the four named original files; its named adverse-negative source export remained absent and would not itself supply an index CAG date. No extraction query, raw angiography/procedure register, discharge register, or independent encounter-level lab export linking the HITS analysis patients to index dates was located.

`TIMING_SOURCE_INVENTORY.csv` contains filenames, hashes, file dimensions where applicable, role, and linkage decision. `ALTERNATIVE_LINKAGE_SOURCE_AUDIT.csv` gives the alternate timing-audit coverage. No source paths containing the local username or patient identifiers are published.

## Timing Denominator Rules

- Clinical timing availability is counted only when episode linkage is defensible. For all 1,820 patients, that denominator is zero.
- For raw lab/admission field availability, the denominator is the phenotype-group cohort size.
- CBC-versus-admission comparisons use calendar dates only because `admission_date` is not a validated exact event timestamp. Same date is not treated as hour-level ordering or same-stay evidence.
- Fibrinogen-versus-CBC counts report calendar-day relation and exact recorded timestamp order separately.
- No missing or unlinked timing value is treated as a negative clinical fact.
