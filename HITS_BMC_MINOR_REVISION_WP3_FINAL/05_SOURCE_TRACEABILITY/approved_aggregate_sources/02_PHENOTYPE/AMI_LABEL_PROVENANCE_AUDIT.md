# AMI phenotype provenance
Direct source: discharge_diagnosis in master_cohort_cleaned.csv. Code: `scripts/06_hits_ami_predevelopment_v0_2.py` lines 201-332 and 356-390.
Explicit acute/subacute MI language defines A; old/prior MI alone can enter broad non-AMI CAD B; unresolved MI without adequate context or uncertain terms remains C. CAD/angina/revascularization markers support B. Troponin, CK-MB, ECG, ICD adjudication, angiography findings, PCI records and physician review are NOT inputs to this classification code.

Independent clinical review: NOT_EVIDENCED in recovered materials. Do not infer one from the word definite. Ancillary troponin fields exist but do not constitute a formal Universal Definition adjudication. Three-way text mapping is a computable phenotype, not a gold standard.

High-specificity code: `scripts/12_hits_v0_5_shift_robust_validation.py` high_specificity_flag, lines 370-379. Requires A plus MI term, acute/ST marker, no subacute or uncertain wording, and subtype/explicit acute phrase/wall-specific phrase. It does not use troponin, ECG or procedure evidence. It uses discharge text, information finalized after presentation/diagnosis; it is not a pre-diagnostic feature set.

Control caveat: strict-control regex also includes PCI/CABG/revascularization terms. High-specificity controls inherit that rule, excluding old-MI/ACS markers. Do not describe all strict controls as angiography-confirmed pure angina without source evidence.

Parser limitation: fallback acute phrase handling and negation span merit clinical chart review; WP1 neither changes the parser nor assigns unresolved patients a negative label.
