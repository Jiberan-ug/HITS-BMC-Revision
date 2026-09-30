# AMI Diagnosis-to-Encounter Linkage: Final

The analysis AMI phenotype is sourced from `discharge_diagnosis` text. The primary mother file includes discharge-diagnosis text and admission-date fields, and the diagnosis value for 2,265 of 2,279 unique patients exactly matches a value on at least one source row. This supports source lineage for most patient-level diagnosis values.

It does **not** establish that the selected diagnosis belongs to the same hospitalization as the 2020–2026 coronary angiography eligibility encounter or to the CBC timestamp used in the model. The mother file lacks an explicit encounter/visit identifier, discharge date, angiography date, PCI/procedure date, and a recovered extraction query that could bind these fields. Its row grain remains unresolved.

`AMI_DIAGNOSIS_SOURCE_LINEAGE = PARTIALLY_RECOVERED`; `DIAGNOSIS_TO_INDEX_ENCOUNTER_LINKAGE = UNKNOWN / NOT_ESTABLISHED`. Do not describe the phenotype as encounter-adjudicated or use it to assert a same-admission or prospective baseline sequence. No AMI labels or model inputs were rebuilt in WP1R.
