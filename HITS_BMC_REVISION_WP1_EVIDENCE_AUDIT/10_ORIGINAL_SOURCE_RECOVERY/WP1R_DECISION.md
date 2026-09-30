# WP1R-A Final Decision

Date: 2026-09-29. Scope: recover and audit the four named source files, report source/encounter/date lineage, and update the author-confirmed ethics declaration. No manuscript was edited, no patient-level source data were copied into this repository, and no model or statistical analysis was rerun.

## Direct Answers

1. **Four original files found:** three of four unique named file types. The primary CSV, adverse-positive CSV, and adverse workbook were found. The adverse-negative CSV (`...20-26-不良（减少附属）.csv`) was not found. Duplicate local copies of the other files had matching hashes.
2. **Primary mother file:** found and hash-verified. SHA-256 `1725a9e4c9b963d2e4737188ed1b8915454792cdbb3d8e2034a7243bedddd239`.
3. **2,548 / 2,279 anchor:** reproduced exactly; the cleaned master has 2,548 rows and the exact same 2,279-patient key set as the primary mother file.
4. **True source-row meaning:** wide patient-linked/merged EHR export; exact row grain unresolved. It is not proven to be one row per hospitalization, encounter, procedure, or lab panel.
5. **2020–2026 selection basis:** author-confirmed as patients undergoing coronary angiography in the Coronary Heart Disease Unit I database at the First Affiliated Hospital of Xinjiang Medical University. No extraction query or corresponding date field was recovered. `STUDY_PERIOD_SOURCE = AUTHOR_CONFIRMED_BUT_NOT_MACHINE_VERIFIED`.
6. **CAG eligibility:** author-confirmed, but not machine-verifiable from the recovered file. No CAG/PCI/procedure date or encounter identifier was found.
7. **CBC dates before 2019:** timestamps are lab `test_time`; their relationship to index encounter is unknown. They are compatible with historical tests in a wide EHR export, but the source does not prove that they are historical rather than index-encounter values or a different merged/selected record.
8. **CBC and discharge diagnosis same encounter:** not established. Both are present at patient-linked level, without an encounter key joining either to an eligible index CAG stay.
9. **True repeat admissions among 269 surplus records:** unknown. All 269 repeated-patient pairs share one baseline admission token, none has two distinct current inpatient numbers, and no pair has two distinct populated admission dates. Therefore zero distinct second admissions are evidenced; this is not proof that none occurred.
10. **Same-hospitalization index CBC:** `NOT_FEASIBLE` from the recovered files because encounter, lab-specimen, and CAG/procedure linkage is absent.
11. **Primary source-lineage:** partially recoverable. Patient set is exact; exact same-patient source-row matches were found for diagnosis in 2,265/2,279, admission date 2,279/2,279, core CBC 2,276/2,279, CBC timestamps 2,279/2,279, fibrinogen value/time 2,276/2,279, and all mapped fields jointly 2,259/2,279. These checks match any source row for a patient, not necessarily the specific row selected by the HITS analysis.
12. **Temporal analysis:** the frozen temporal code/output remains an existing implementation record, but is not credible as temporal transportability evidence until modeled dates are linked to index encounters and the date-shift lineage is verified. No frozen estimate was recalculated or overwritten.
13. **Ethics:** `ETHICS_CONSENT_GATE = PASS` based on the author's explicit confirmation of approval K202602-10 and an Ethics Committee-approved waiver of informed consent. The approval documents were not independently inspected and are not included in the public repository. The manuscript statement “All participants provided informed consent” conflicts with the author confirmation and must be corrected in a later manuscript stage.

## Final Gate

**`WP1R_SOURCE_RECOVERY_PARTIAL_PASS_INDEX_CBC_RECONSTRUCTION_REQUIRED`**

The original primary mother file and patient-level lineage were recovered, but the missing fourth file, unverified eligibility query, unresolved repeated-row grain, and absent encounter/CBC/procedure linkage prevent a full source-recovery pass or index-CBC reconstruction. Stop here. This gate does not authorize WP2, model reruns, or manuscript edits.

## Machine-Readable Evidence

See the adjacent source inventory, source-to-analysis crosswalk, repeated-patient token audit, date-field inventory, date relationships, and aggregate metrics. They contain no patient-level identifiers or row-level records. Source originals remain local and are not committed.
