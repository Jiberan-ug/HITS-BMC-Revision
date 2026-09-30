# Reviewer response skeleton
Not a response letter. Verbatim letter needs recovery; summaries below come from user WP1 instructions.

## E1: CBC/fibrinogen selection and timing
Response: [NOT DRAFTED IN WP1]
Evidence: 01_TIMING/CBC_INDEX_MEASUREMENT_RULE_AUDIT.md
Action: Recover index encounter and laboratory ETL; no pre-angiography claim
Manuscript change: [WP3 ONLY] Methods
Status: AUDITED / AWAITING AUTHORIZATION

## E2: AMI label provenance and clinical adjudication
Response: [NOT DRAFTED IN WP1]
Evidence: 02_PHENOTYPE/AMI_LABEL_PROVENANCE_AUDIT.md
Action: Report text-derived phenotype; do not invent adjudication
Manuscript change: [WP3 ONLY] Methods/limitations
Status: AUDITED / AWAITING AUTHORIZATION

## E3: Reconcile2548 to2279
Response: [NOT DRAFTED IN WP1]
Evidence: 03_COHORT_FLOW/MOST_COMPLETE_RECORD_SELECTION_RULE.md
Action: Report269 surplus rows, not269 proven repeat admissions
Manuscript change: [WP3 ONLY] Flow/Methods
Status: AUDITED / AWAITING AUTHORIZATION

## E4: Nested validation, aggregation and bootstrap
Response: [NOT DRAFTED IN WP1]
Evidence: 04_VALIDATION/VALIDATION_PIPELINE_AUDIT.md
Action: Report5x10/inner5 and fixed averaged-prediction bootstrap
Manuscript change: [WP3 ONLY] Statistics
Status: AUDITED / AWAITING AUTHORIZATION

## E5: Temporal validation design
Response: [NOT DRAFTED IN WP1]
Evidence: 04_VALIDATION/TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md
Action: Verify date lineage before temporal claim; retain frozen estimates
Manuscript change: [WP3 ONLY] Methods/limitations
Status: AUDITED / AWAITING AUTHORIZATION

## E6: High-specificity phenotype flow
Response: [NOT DRAFTED IN WP1]
Evidence: 02_PHENOTYPE/HIGH_SPECIFICITY_AMI_COHORT_AUDIT.md
Action: Explain453 to178 to138; later R flowchart only after approval
Manuscript change: [WP3 ONLY] Supplement
Status: AUDITED / AWAITING AUTHORIZATION

## E7: Fibrinogen missingness and same-sample comparison
Response: [NOT DRAFTED IN WP1]
Evidence: 05_MISSINGNESS/FIBRINOGEN_FAIR_COMPARISON_AUDIT.md
Action: Report by-outcome availability and paired CC comparison
Manuscript change: [WP3 ONLY] Results/Supplement
Status: AUDITED / AWAITING AUTHORIZATION

## E8: Clinical missingness and full incremental performance
Response: [NOT DRAFTED IN WP1]
Evidence: 05_MISSINGNESS/AGE_DEFINITION_DISCREPANCY.md
Action: Recover corrected age vector before clinical-model reuse
Manuscript change: [WP3 ONLY] Methods/Results
Status: AUDITED / AWAITING AUTHORIZATION

## E9: Calibration provenance and Figure5 intervals
Response: [NOT DRAFTED IN WP1]
Evidence: 04_VALIDATION/CALIBRATION_PREDICTION_PROVENANCE.md
Action: Recover canonical predictions; reconcile legacy figure branch; no rerun now
Manuscript change: [WP3 ONLY] Figures/Table2
Status: AUDITED / AWAITING AUTHORIZATION

## E10: Conclusions and clinical positioning
Response: [NOT DRAFTED IN WP1]
Evidence: 08_REVISION_PLANNING/CONCLUSION_CLAIM_AUDIT.md
Action: Acknowledge limited internal increment and temporal uncertainty
Manuscript change: [WP3 ONLY] Discussion/Conclusions
Status: AUDITED / AWAITING AUTHORIZATION

## E11: Human research guidelines statement
Response: [NOT DRAFTED IN WP1]
Evidence: 07_ETHICS/HUMAN_RESEARCH_GUIDELINES_REQUIREMENT.md
Action: Verify documents; insert text only in WP3
Manuscript change: [WP3 ONLY] Declarations
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M1: Validation rigor and temporal generalizability
Response: [NOT DRAFTED IN WP1]
Evidence: 04_VALIDATION/TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md
Action: Separate code verification from date-source validity
Manuscript change: [WP3 ONLY] Statistics/limitations
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M2: Core predictor collinearity
Response: [NOT DRAFTED IN WP1]
Evidence: 06_COMPARATORS/COLLINEARITY_EXISTING_EVIDENCE_AUDIT.md
Action: WP2 descriptive Spearman only; do not reselect
Manuscript change: [WP3 ONLY] Supplement
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M3: Clinical covariate missingness handling
Response: [NOT DRAFTED IN WP1]
Evidence: 05_MISSINGNESS/AGE_DEFINITION_DISCREPANCY.md
Action: Resolve1818 versus1820; document fold-local imputation
Manuscript change: [WP3 ONLY] Methods/Table1
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M4: All traditional index benchmarks
Response: [NOT DRAFTED IN WP1]
Evidence: 06_COMPARATORS/TRADITIONAL_INDEX_PERFORMANCE_INVENTORY.csv
Action: Report all7 existing AUC/CI; PIV remains primary
Manuscript change: [WP3 ONLY] Supplement
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M5: Repeat records and prior cardiovascular history
Response: [NOT DRAFTED IN WP1]
Evidence: 03_COHORT_FLOW/MOST_COMPLETE_RECORD_SELECTION_RULE.md
Action: Recover encounter/history semantics; row counts already reconcile
Manuscript change: [WP3 ONLY] Methods/Table1/flow
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M6: Fairness of PIV comparison
Response: [NOT DRAFTED IN WP1]
Evidence: 06_COMPARATORS/PIV_COMPARATOR_METHOD_AUDIT.md
Action: Explain internal log-logistic vs temporal ordinal comparison
Manuscript change: [WP3 ONLY] Statistics
Status: AUDITED / AWAITING AUTHORIZATION

## R1-M7: Troponin comparison
Response: [NOT DRAFTED IN WP1]
Evidence: 06_COMPARATORS/TROPONIN_FEASIBILITY_AUDIT.md
Action: Do not pool incomparable assays; request assay/ULN/time only if retrievable
Manuscript change: [WP3 ONLY] Limitations
Status: AUDITED / AWAITING AUTHORIZATION

## R1-m1: Consecutive screening
Response: [NOT DRAFTED IN WP1]
Evidence: 03_COHORT_FLOW/CONSECUTIVE_SCREENING_AND_SELECTION_BIAS_AUDIT.md
Action: Retrieve screening/extraction register; do not assert consecutive
Manuscript change: [WP3 ONLY] Setting
Status: AUDITED / AWAITING AUTHORIZATION

## R1-m2: CBC timing clarification
Response: [NOT DRAFTED IN WP1]
Evidence: 01_TIMING/CBC_INDEX_MEASUREMENT_RULE_AUDIT.md
Action: State completeness-ranked row, not first/pre-event sample
Manuscript change: [WP3 ONLY] Methods
Status: AUDITED / AWAITING AUTHORIZATION

## R1-m3: Informed consent in retrospective cohort
Response: [NOT DRAFTED IN WP1]
Evidence: 07_ETHICS/ETHICS_CONSENT_HARD_GATE.md
Action: Documentary author confirmation; no inferred waiver
Manuscript change: [WP3 ONLY] Declarations
Status: AUDITED / AWAITING AUTHORIZATION

## R2-1: DCA for clinical incremental models
Response: [NOT DRAFTED IN WP1]
Evidence: 06_COMPARATORS/DCA_FEASIBILITY_AUDIT.md
Action: Canonical OOF recovery required before any authorized DCA
Manuscript change: [WP3 ONLY] Supplement/limitations
Status: AUDITED / AWAITING AUTHORIZATION
