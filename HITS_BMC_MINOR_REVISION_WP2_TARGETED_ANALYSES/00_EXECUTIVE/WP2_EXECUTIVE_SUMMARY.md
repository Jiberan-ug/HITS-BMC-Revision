# WP2 Executive Summary

## Decision

`WP2_PASS_READY_FOR_MANUSCRIPT_REVISION`. This is an analysis-repair package for retrospective single-center AMI phenotype discrimination among CAD patients. It is not future-event prediction, temporal transportability, clinical diagnosis, triage, or external validation.

## Cohort and canonical models

- Primary cohort: N=1820; AMI=453 (24.9%); non-AMI CAD=1367.
- Fibrinogen complete-case cohort: N=1705; AMI=426; non-AMI=1279.
- Age gate: `AGE_1820_CANONICAL_LOCKED`. Canonical model vector has 1820/1820 ages; the submitted Table 1 1818 count is not reproduced and remains a separate reporting discrepancy for WP3.
- Core-7: AUC=0.725350, 95% CI 0.697229–0.752611, Brier=0.162803, calibration intercept=-0.025793, slope=0.973876.
- PIV: AUC=0.708051, 95% CI 0.677757–0.735254.
- Core−PIV: ΔAUC=0.017300, 95% CI 0.003446–0.030794; N=1820, paired on identical patients/folds.
- Enhanced, historical full-cohort canonical imputation branch: AUC=0.735135, 95% CI 0.710044–0.762760, N=1820. This exact existing fold-local median pipeline is reproduced only for freeze reconciliation.
- Enhanced complete case: AUC=0.736739, 95% CI 0.709817–0.766010, N=1705. Enhanced−Core paired complete-case ΔAUC=0.009678, 95% CI 0.002300–0.016932.

## Clinical increment and DCA

Full-cohort OOF results not requiring fibrinogen:
- Clinical only: N=1820, AUC=0.554525, 95% CI 0.524452–0.585820, Brier=0.185730.
- Clinical + PIV: N=1820, AUC=0.713057, 95% CI 0.684882–0.740119, Brier=0.166039.
- Clinical + Core-7: N=1820, AUC=0.729270, 95% CI 0.702412–0.757533, Brier=0.162285.

The full-cohort Clinical + Enhanced result (AUC=0.739413) reproduces the historical fold-local fibrinogen-imputation branch for freeze reconciliation only. No new fibrinogen imputation is used for reviewer-facing Enhanced comparisons. Those comparisons use the shared complete-case cohort:
- Clinical only: N=1705, AUC=0.545733, 95% CI 0.514742–0.574058, Brier=0.186609.
- Clinical + PIV: N=1705, AUC=0.717332, 95% CI 0.689350–0.744927, Brier=0.165521.
- Clinical + Core-7: N=1705, AUC=0.730297, 95% CI 0.700715–0.755403, Brier=0.162300.
- Clinical + Enhanced: N=1705, AUC=0.740699, 95% CI 0.712219–0.770013, Brier=0.161187.

Paired complete-case comparisons:
- Fibrinogen-complete cohort Clinical_Plus_PIV minus Clinical: ΔAUC=0.171598, 95% CI 0.134116–0.207963.
- Fibrinogen-complete cohort Clinical_Plus_Core minus Clinical: ΔAUC=0.184563, 95% CI 0.147726–0.225633.
- Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical: ΔAUC=0.194966, 95% CI 0.156701–0.230987.
- Fibrinogen-complete cohort Clinical_Plus_Core minus Clinical_Plus_PIV: ΔAUC=0.012965, 95% CI 0.000391–0.025074.
- Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical_Plus_PIV: ΔAUC=0.023368, 95% CI 0.010638–0.038660.
- Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical_Plus_Core: ΔAUC=0.010403, 95% CI 0.002962–0.017287.

The reviewer-facing DCA uses the fibrinogen-complete sample N=1705, with all four clinical models, treat-all, and treat-none on identical patients. It is exploratory and is not evidence of clinical utility.

## Other required analyses

- Canonical result reconciliation: 57 MATCH, 0 ROUNDING_ONLY, 0 MINOR_NUMERIC_DIFFERENCE, 0 MATERIAL_MISMATCH.
- Traditional indices: NLR, PLR, MLR, SII, SIRI, PIV, and HRR; PIV remains the prespecified comparator.
- Core-7: Spearman matrix and frozen 300-development-bootstrap stability summary provided; no variable removed.
- Calibration and ROC source data use regenerated 5×10 OOF predictions. The legacy 20-repeat figure branch is superseded in this review package.
- Figure 5: 9/9 displayed AUCs have a 95% CI in the frozen source; no new temporal models were fit.
- Date-axis numbers are preserved and relabeled for WP3 as `EXPLORATORY DEIDENTIFIED DATE-AXIS SENSITIVITY ANALYSIS`; they do not establish temporal validation or transportability.
- Troponin pooled comparator: not performed; unified assay, ULN, and timing are invalid/incomplete.
- Patient-level OOF files: saved locally with restrictive permissions; absent from repository and public ZIP.

## Scope and risks

- The two-person Table 1 age discrepancy is not resolved at the individual-record cause level; WP3 must rebuild that descriptive row from the locked age vector.
- The frozen CBC-to-index-angiography encounter link remains unverified, so no admission-first, pre-diagnosis, pre-angiography, or treatment-naive claim is supported.
- Discharge-diagnosis phenotypes are not independently adjudicated; the high-specificity subset is a strict text-rule sensitivity only.
- Bootstrap intervals resample fixed patient-level mean OOF predictions and do not include full model-development uncertainty.

Manuscript rewriting, response-letter drafting, and PR merge were not performed.
