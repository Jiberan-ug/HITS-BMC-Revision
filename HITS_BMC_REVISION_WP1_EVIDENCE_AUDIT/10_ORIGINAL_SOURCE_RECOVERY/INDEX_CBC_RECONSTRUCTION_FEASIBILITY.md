# Index CBC Reconstruction Feasibility

## Status

**NOT_FEASIBLE from the currently recovered source set.** This is a feasibility finding, not a claim that reconstruction is impossible if an encounter-level laboratory extract or original query is later recovered.

## Required chain and gaps

To identify the first CBC during an eligible index hospitalization, and determine whether it preceded angiography/intervention, the source must link patient, eligible index encounter, encounter admission/discharge, lab specimen/time, and angiography/procedure time. The recovered mother file has patient keys, a sparse admission-date field, discharge diagnosis text, and CBC test timestamps; it lacks an encounter/visit key, discharge date, CAG/PCI/procedure date, and a verified specimen/collection-time definition.

CBC timestamps are present in a wide export and can be traced to a source row for all 2,279 patient keys. That does not identify which CBC belongs to the 2020–2026 eligibility encounter. The 269 duplicated patient groups also do not contain two distinct current inpatient numbers or two distinct populated admission dates. The AMI phenotype is derived from discharge-diagnosis text, but the source cannot prove that the selected diagnosis belongs to the same angiography/index encounter as any candidate CBC.

## Determination

`INDEX_CBC_STATUS = NOT_FEASIBLE`; `PRE_ANGIOGRAPHY_CBC = NOT_ESTABLISHED`. Do not construct an analysis dataset or rerun a model in this WP. A future reconstruction would require an encounter-level extraction/query or source-system crosswalk linking eligible CAG encounter, diagnosis, laboratory specimen timestamp, and procedure timestamp. CBC date must not be used as a surrogate cohort-entry date.
