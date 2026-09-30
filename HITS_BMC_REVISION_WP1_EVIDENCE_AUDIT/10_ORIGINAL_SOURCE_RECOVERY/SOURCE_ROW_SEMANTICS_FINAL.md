# Source Row Semantics: Final

## Recovered structure

The primary source is a wide patient-linked EHR export with repeated rows for some patient keys. Its row grain cannot be promoted to hospitalization, encounter, procedure, or laboratory-panel grain from the available identifiers. The defensible classification is **wide patient-linked/merged EHR record; exact row semantics unknown**.

The recovered primary file has 2,548 rows, 431 columns, and 2,279 unique `patient_sn` values. The cleaned master has the same 2,548 rows and exactly the same set of 2,279 patient keys. Thus the patient-level source lineage is recovered, while encounter-level lineage is not.

## Identifiers and repeats

- 2,010 patients have one source row; 269 patients have two rows; none has three or more. The 269 extra rows are a row multiplicity, not a verified count of repeat hospitalizations.
- In all 269 two-row patient groups, both rows carry the same single `基线_inpatient_no_id` token. No pair has two distinct values for this field.
- The current `inpatient_no_id` is populated on only one row in each of the 269 groups; no pair contains two current inpatient numbers or two distinct current inpatient numbers.
- Admission date is present in one row for 17 groups and absent in both rows for 252 groups; no group has two populated, distinct admission dates.
- No explicit encounter/visit ID, discharge date, angiography date, PCI/procedure date, or procedure identifier was found among the 431 source columns. Five `vsn_admission_record` fields and one `vsn_discharge_record` field do not supply an encounter key/date that resolves the repeats.

## Determination

`SOURCE_ROW_GRAIN = WIDE_PATIENT_LINKED_MERGED_RECORD_UNRESOLVED`; `TRUE_REPEAT_HOSPITALIZATIONS = UNKNOWN`; `DISTINCT_SECOND_ADMISSIONS_EVIDENCED = 0`. The data do not establish whether the repeated rows are duplicate extraction, multiple source records from the same hospitalization, distinct procedures, or separate admissions. Do not call all 269 extra rows repeat hospitalizations, and do not use row multiplicity alone to infer the number of admissions.
