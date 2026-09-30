# WP3.3 executive summary

**Gate: `WP3_3_HOLD_TARGET_DATE_NOT_RECONSTRUCTABLE`. Do not submit the WP3.2 package.**

The frozen master and historical cohort selector reproduce 1,820 patients (453 definite AMI; 1,367 definite non-AMI CAD). Primary birth dates parse for all 1,820. A source-confirmed, patient-linked target hospitalization or coronary-angiography date has **not** been supplied or found in the audited source ecosystem. The user confirmed on 2026-09-30 that the requested individual target-date dataset is not currently available.

The flat master has 130/1,820 parseable `admission_date` entries, but no encounter-level proof that they belong to the target episode; 80 are dated before 2020, inconsistent with treating the field wholesale as a confirmed 2020-2026 target-episode anchor. The remaining 1,690 lack that date. The legacy CBC/WBC timestamp cannot be used as the age fallback. Therefore target-anchored age availability, Table 1 age, and corrected clinical-model metrics are **not estimable**, not zero-valued results.

An independent frozen-source discrepancy also blocks submission: the V0.5 temporal script whose SHA-256 matches the archived run manifest explicitly assigns groups using `cbc_datetime` and a 2015-01-01 cutpoint, whereas the WP3.2 source-lineage note and current submission language say the groups used a 2020-2026 target hospitalization/CAG date axis and did not use the legacy CBC timestamp. The historical group counts may remain recorded, but their claimed clinical calendar interpretation is not source-verified. No temporal analysis was rerun here.

No model, DCA, calibration, figure, manuscript, or response was changed. Old age-dependent clinical results are marked **SUPERSEDED_BY_TARGET_HOSPITALIZATION_AGE** for submission use, pending a valid reanalysis; this does not assert that replacement results exist. Core-7, PIV, Enhanced hematologic and other frozen numerical files remain byte-unchanged, but numerical freeze is not a substitute for a valid source interpretation.

To lift the HOLD, obtain a locally controlled patient/encounter-linked target admission or CAG source with field dictionary, provenance, date-shift semantics, and a documented join key to the frozen master. Reconcile the original temporal-group allocation to executable source evidence separately. Then rerun only the age-dependent clinical analyses specified in WP3.3 and perform a new submission audit. No patient-level source or output belongs in this public repository.
