# Target date provenance

| Candidate | Audited source | Coverage in frozen N=1,820 | Episode interpretation | Decision |
| --- | --- | ---: | --- | --- |
| `admission_date` | `master_cohort_cleaned.csv` (SHA-256 `f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660`) | 130 parseable; 1,690 missing | No encounter key/source confirmation; observed years 2012-2025, with 80 before 2020 and 50 in 2020-2026 | Cannot anchor target age |
| Target CAG/procedure date | Audited original mother export and cleaned master | No independent field identified | No patient/encounter-linked event table supplied | Not available |
| Deidentified target episode date | No source file supplied | Not measurable | WP3.2 narrative assertion lacks a linked data file or reproducible allocation code | Not available |
| Legacy WBC/CBC timestamp | Cleaned master | Historically used for 1,690 fallback ages | Explicitly disallowed as target clinical timing anchor | Excluded |

The original mother export (`冠心病+造影手术+20-26（减少附属）(1).csv`, SHA-256 `1725a9e4c9b963d2e4737188ed1b8915454792cdbb3d8e2034a7243bedddd239`) has only 146/2,548 nonempty `admission_date` entries and no independently linked CAG/procedure date in the WP1R-B source inventory. The cleaned master has 2,548 rows and 436 columns; the same historical selector yields 2,279 unique patients and the frozen N=1,820 cohort. Neither source establishes that a parsed admission date belongs to the selected target hospitalization.

The requested priority A/B/C hierarchy cannot be applied because no candidate is episode-confirmed. There is no valid fallback hierarchy and no year minimum/maximum for a *confirmed* target date. The 2012-2025 range describes only the unverified `admission_date` candidate, not the study-period range.

The user confirmed on 2026-09-30 that no individual target-date source is currently available. This is a source-access/lineage HOLD, not a statistical missing-value imputation problem. See `AGE_TARGET_HOSPITALIZATION_QC.csv` for aggregate denominators and `05_QA/audit_wp3_3_sources.py` for reproducible checks. No patient record was copied into this package.
