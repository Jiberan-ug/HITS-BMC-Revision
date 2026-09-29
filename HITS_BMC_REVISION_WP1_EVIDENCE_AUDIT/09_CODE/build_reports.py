"""Assemble read-only WP1 evidence inventories; never fit models or draw figures."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

ROOT = Path(os.environ['HITS_PROJECT_ROOT'])
OUT = Path(__file__).resolve().parents[1]
V31 = 'HITS_V0.3.1_verified_completion_20260825'
V05 = 'HITS_V0.5_shift_robust_validation'
V51 = 'HITS_V0.5.1_final_QA_lock'
FREEZE = 'HITS_V0.5.2_PUBLICATION_FREEZE'
BMC = 'RECOVERED_FROM_DOWNLOADS_20260831/03_SUBMISSION_PACKS/HITS_BMC_Cardiovascular_Disorders_Submission_Pack_v1.0/04_SOURCE_TRACEABILITY/Figure_Source_Data_and_R_Scripts'
CODE02 = 'scripts/06_hits_ami_predevelopment_v0_2.py'
CODE31 = V31+'/scripts/01_run_hits_v0_3_1_verified_completion.py'
CODE05 = 'scripts/12_hits_v0_5_shift_robust_validation.py'
GATE = 'WP1_HOLD_DUE_TO_SOURCE_DATA_GAP'
manifest=[]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def remember(rel):
    p=ROOT/rel
    manifest.append(dict(source=rel,sha256=digest(p),bytes=p.stat().st_size))
    return p


def csv(rel,data):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    (data if isinstance(data,pd.DataFrame) else pd.DataFrame(data)).to_csv(p,index=False,lineterminator='\n')


def md(rel,text):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text.strip()+'\n',encoding='utf-8')


def read(rel):
    return pd.read_csv(remember(rel))


def evidence(rel,alias):
    d=read(rel)
    forbidden={'patient_sn','research_patient_id','diagnosis_text','name','inpatient_no_id'}
    assert not forbidden.intersection(d.columns)
    csv('09_CODE/evidence/'+alias,d)
    return d


def main():
    m=json.loads((OUT/'09_CODE/descriptive_metrics.json').read_text())
    reg=evidence(FREEZE+'/04_CANONICAL_RESULT_REGISTRY.csv','CANONICAL_RESULT_REGISTRY.csv')
    perf=evidence(V31+'/05_nested_cv_robustness.csv','V031_performance.csv')
    trad=evidence(V31+'/06_traditional_marker_comparison.csv','V031_traditional.csv')
    clinical=evidence(V31+'/08_clinical_incremental_models.csv','V031_clinical.csv')
    delta=evidence(V31+'/07_paired_delta_auc_bootstrap.csv','V031_paired_deltas.csv')
    cc=evidence(V31+'/10_fibrinogen_complete_case_sensitivity.csv','V031_fibrinogen_CC.csv')
    evidence(V31+'/16_variable_stability.csv','V031_stability.csv')
    evidence(V31+'/01_candidate_missingness.csv','V031_historical_missingness.csv')
    legacy=evidence('HITS_V0.3_score_development/05_nested_cv_robustness_performance.csv','LEGACY_NOT_CANONICAL_performance.csv')
    evidence(V51+'/08_asymmetric_bound_sensitivity.csv','V051_asymmetric_sensitivity.csv')
    evidence(V51+'/06_clinical_enhanced_vs_PIV.csv','V051_temporal_clinical_delta.csv')
    # Preserve inspectable code with original line numbers, but redact personal home paths.
    for rel,alias in [(CODE02,'cohort_selection'),(CODE31,'canonical_internal'),(CODE05,'temporal'),
                      ('scripts/03_create_reviewer_rescue_package.R','date_shift'),
                      ('scripts/build_hits_manuscript_v1.R','legacy_figure_builder'),
                      (BMC+'/plot_hits_clinical_figures.R','submitted_figure45')]:
        p=remember(rel)
        text=p.read_text().replace(str(Path.home()),'$HOME')
        md('09_CODE/source_excerpts/'+alias+'.txt',f'Source: {rel}\nOriginal SHA256: {digest(p)}\nREAD ONLY; NOT EXECUTABLE. Home path redacted; trailing whitespace normalized.\n\n'+'\n'.join(f'{i:04d}: {line}'.rstrip() for i,line in enumerate(text.splitlines(),1)))
    figs=read(BMC+'/Figure3_source_data.csv')
    csv('09_CODE/evidence/submitted_calibration_points.csv',figs)
    lineage=[]
    for rel in ['HITS_MANUSCRIPT_V1.0/03_FIGURES/Figure4_source_data.csv','HITS_MANUSCRIPT_V1.1_PRE_SUBMISSION_QA/03_FIGURES/Figure4_source_data.csv','HITS_MANUSCRIPT_V1.2.1_FINAL_HOTFIX/01_MANUSCRIPT/figures/Figure4_source_data.csv']:
        p=ROOT/rel
        if p.exists():
            x=read(rel)
            lineage.append(dict(source=rel,submitted_calibration_equal=x.equals(figs),submitted_source=BMC+'/Figure3_source_data.csv'))
    csv('04_VALIDATION/FIGURE_SOURCE_LINEAGE_CHECK.csv',lineage)
    doc=Path(os.environ.get('HITS_CURRENT_DOCX',str(Path.home()/'Downloads/HITS_BMC_Manuscript_v1.2_EthicsNumber.docx')))
    with zipfile.ZipFile(doc) as z:
        xml=ET.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    pars=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in xml.findall('.//w:p',ns)]
    manuscript_text='\n'.join(pars)
    manifest.append(dict(source='LOCAL_DOWNLOADS/'+doc.name,sha256=digest(doc),bytes=doc.stat().st_size))
    assert '1818' in manuscript_text and '2020' in manuscript_text
    # Only short scientific/declaration excerpts, never authorship/address/contact blocks.
    selections=[(9,'abstract_methods'),(20,'setting_date_claim'),(34,'validation_methods'),(127,'age_denominators'),(185,'calibration_caption'),(239,'sensitivity_caption'),(246,'limitations'),(257,'consent_claim')]
    csv('09_CODE/evidence/MANUSCRIPT_TARGETED_EXCERPTS.csv',[dict(paragraph_zero_based=i,topic=tag,text=pars[i],source=doc.name,canonical_submitted_status='NOT_PORTAL_VERIFIED') for i,tag in selections])

    trad['formula']=trad.model.map(dict(NLR='Neut/Lymph',PLR='PLT/Lymph',MLR='Mono/Lymph',SII='PLT*Neut/Lymph',SIRI='Neut*Mono/Lymph',PIV='PLT*Neut*Mono/Lymph',HRR='Hb/RDW'))
    trad['transformation']='log1p(max(x,0)), training-fold z standardization'
    trad['validation_framework']='5-fold x 10 repeated outer CV; unpenalized univariable logistic fitted on training fold; no hyperparameter tuning required'
    trad['direct_Core_comparison']='YES_IN_PRIMARY; see paired delta output'
    trad['source']=V31+'/06_traditional_marker_comparison.csv'
    csv('06_COMPARATORS/TRADITIONAL_INDEX_PERFORMANCE_INVENTORY.csv',trad)
    cirows=[]
    for _,row in clinical.iterrows():
        d=row.to_dict();d.update(record_type='performance',status='EXISTING_NUMBERS_AGE_PROVENANCE_UNRESOLVED',source=V31+'/08_clinical_incremental_models.csv')
        cirows.append(d)
    for _,row in delta[delta.comparison.str.contains('Clinical')].iterrows():
        d=row.to_dict();d.update(record_type='paired_comparison',status='EXISTING',source=V31+'/07_paired_delta_auc_bootstrap.csv');cirows.append(d)
    for cohort in ['primary','strict']:
        for model in ['Clinical+PIV','Clinical+Core','Clinical+Enhanced']:
            cirows.append(dict(record_type='requested_gap',analysis=cohort,comparison=model+' minus Clinical',status='WP2_NEW_ANALYSIS_REQUIRED_FOR_PAIRED_CI',source='Not present in audited canonical paired output'))
        cirows.append(dict(record_type='requested_gap',analysis=cohort,comparison='Clinical+Enhanced minus Clinical+PIV',status='WP2_NEW_ANALYSIS_REQUIRED_FOR_INTERNAL_PAIRED_CI',source='Temporal N520 comparison exists separately and is NOT interchangeable'))
    csv('06_COMPARATORS/CLINICAL_INCREMENTAL_PERFORMANCE_EXISTING_RESULTS.csv',cirows)
    ids=['V05_PRIMARY_GUARDBAND','V05_HIGH_SPECIFICITY','V05_CONSERVATIVE_365D','V052_ASYMMETRIC_BOUND']
    fg=reg[reg.analysis_id.isin(ids)].copy()
    fg['CI_available']=fg.CI_lower.notna() & fg.CI_upper.notna()
    fg['why_omitted_from_figure']=fg.CI_available.map({True:'Not omitted in recovered plotting code',False:'No per-model AUC CI in registry or V051 asymmetric output; paired delta CI is a different estimand'})
    fg['can_add_without_rerun']=fg.CI_available.map({True:'YES_EXISTING',False:'NO_FIXED_PREDICTIONS_REBOOTSTRAP_NEEDS_WP2_AUTHORIZATION_AND_RECOVERY'})
    fg['status']=fg.CI_available.map({True:'EXISTING_EVIDENCE_NO_RERUN',False:'WP2_NEW_ANALYSIS_REQUIRED'})
    fg['CI_source']=FREEZE+'/04_CANONICAL_RESULT_REGISTRY.csv'
    csv('04_VALIDATION/FIGURE5_CI_AVAILABILITY.csv',fg)

    md('01_TIMING/CBC_INDEX_MEASUREMENT_RULE_AUDIT.md',f'''
# CBC index measurement rule
Status: TIMING_RECONSTRUCTION = NOT_FEASIBLE for a validated index admission, angiography, or first diagnosis using recovered materials alone.

Direct code: `{CODE02}` lines 335-390, archived in `09_CODE/source_excerpts/cohort_selection.txt`.
One flat master row is selected per patient. Lexicographic ranking: nonblank discharge diagnosis (descending); raw nonmissing count of absolute Neut/Lymph/Mono/PLT (descending); parsable WBC timestamp present (descending); pre-existing qc_nonmissing_count (descending); source-row position (ascending). Patient key is the grouping key. No chronological minimum/maximum or pre-event check is applied. CBC/fibrinogen are read from that selected row, not selected independently from a longitudinal laboratory table. The upstream test-selection ETL is not recovered.

All seven CBC timestamps match WBC time in 1820/1820 selected analysis rows. This supports within-row CBC timestamp consistency, not admission-first sampling, specimen identity or pre-AMI/pre-angiography status. Timestamp label is test_time; collection-versus-report-time semantics remain unverified.

Admission dates are present in 130/1820. Arithmetic CBC-minus-admission median is -1754.205 days (IQR -3055.304 to -30.604), 99 before/31 after, 19 same calendar day. Before/after timestamps and same-calendar-day counts overlap by definition. These implausibly long gaps forbid an interpretation as validated within-index-hospitalization timing. No dedicated angiography/PCI/initial-AMI/discharge-diagnosis timestamp recovered in master headers/dictionary. Admission/discharge vsn tokens exist but are not dates. No imaging/treatment source export or selection ETL recovered in the inspected project/archive.

Fibrinogen timestamps: 1707; numeric fibrinogen: 1705. Fbg-CBC same calendar day: 1553/1707 (90.978%). Median difference is about 0.000440 days. Laboratory proximity does not repair encounter linkage. See descriptive timing CSVs; do not delete negative-time cases or rebuild the cohort in WP1.

Honest reporting rule for future WP3: a laboratory panel carried by the selected completeness-ranked patient record. Do not call it admission-first or pre-angiography. Exact recruitment period and hospital encounter require author/source verification.
''')
    md('02_PHENOTYPE/AMI_LABEL_PROVENANCE_AUDIT.md',f'''
# AMI phenotype provenance
Direct source: discharge_diagnosis in master_cohort_cleaned.csv. Code: `{CODE02}` lines 201-332 and 356-390.
Explicit acute/subacute MI language defines A; old/prior MI alone can enter broad non-AMI CAD B; unresolved MI without adequate context or uncertain terms remains C. CAD/angina/revascularization markers support B. Troponin, CK-MB, ECG, ICD adjudication, angiography findings, PCI records and physician review are NOT inputs to this classification code.

Independent clinical review: NOT_EVIDENCED in recovered materials. Do not infer one from the word definite. Ancillary troponin fields exist but do not constitute a formal Universal Definition adjudication. Three-way text mapping is a computable phenotype, not a gold standard.

High-specificity code: `{CODE05}` high_specificity_flag, lines 370-379. Requires A plus MI term, acute/ST marker, no subacute or uncertain wording, and subtype/explicit acute phrase/wall-specific phrase. It does not use troponin, ECG or procedure evidence. It uses discharge text, information finalized after presentation/diagnosis; it is not a pre-diagnostic feature set.

Control caveat: strict-control regex also includes PCI/CABG/revascularization terms. High-specificity controls inherit that rule, excluding old-MI/ACS markers. Do not describe all strict controls as angiography-confirmed pure angina without source evidence.

Parser limitation: fallback acute phrase handling and negation span merit clinical chart review; WP1 neither changes the parser nor assigns unresolved patients a negative label.
''')
    md('02_PHENOTYPE/HIGH_SPECIFICITY_AMI_COHORT_AUDIT.md','''
# High-specificity cohort flow
Frozen primary AMI 453 = early 196 + buffer 79 + late 178. The decrease to 138 is NOT 315 phenotype misclassifications: 275 are outside the late validation set; within the late set 40 do not meet the stricter diagnosis-text rule. Late non-AMI controls decrease from 370 to 288 under the strict-control rule (82 excluded). Final late cohort 138+288=426.

Earlier high-specificity development cohort: 162 AMI + 634 strict controls = 796. Buffer high-specificity counts: 62 + 142 = 204 (not used in fitting/validation). See source CSV for all primary and high-specificity counts; these are descriptive rule reconstructions, not new model results.

The same discharge-diagnosis text supplies both phenotype definitions. Post-presentation/diagnosis information: YES (discharge text). Troponin/ECG/procedure requirements for positive high-specificity definition: NO. Treatment/revascularization wording can qualify a non-AMI strict control. No independent adjudication is evidenced. Date-lineage problems described in the temporal report apply equally here.
''')
    md('03_COHORT_FLOW/MOST_COMPLETE_RECORD_SELECTION_RULE.md',f'''
# Selection rule and reconciled rows
`{CODE02}` select_one_row_per_patient is the authoritative executable selector inspected. Exact lexicographic fields: `_has_diagnosis`, `_core_required_count` (Neut absolute, Lymph absolute, Mono absolute, PLT), `_has_cbc_time`, `qc_nonmissing_count`, `_source_row`; descending except final ascending source row. No chronology rule beyond timestamp availability.

Raw 2548 rows; unique patient keys 2279. 2010 patients have one row; 269 have two; no patient has >=3. Exactly 269 surplus rows are excluded by grouping. Zero completely identical rows. No other pre-selection exclusion, no missing patient key. Therefore FLOW_COUNTS_RECONCILE = YES at ROW level; 2548 distinct hospital encounters is NOT established.

For all 269 multiple-row patients, at most one row has a nonmissing diagnosis and at most one has CBC time. Seventeen have one distinct nonmissing admission date; 252 have none; none has two distinct admission dates. Neither main nor baseline admission token has multiple distinct nonmissing values within those groups. This pattern is compatible with partially populated linked/export rows; upstream extraction logic is needed to explain its origin. Repeated hospitalization count = UNKNOWN, not 269 and not proven zero.

After selection: A456 + B1372 + C340 + out-of-scope111 =2279. CBC requirement removes 3 A and 5 B; final 453+1367=1820. Post-selection exclusions:340+111+8=459. Missing diagnosis is included in C; do not count twice.

Outcome-informed selection risk: diagnosis availability explicitly affects ranking, so selection is not outcome-blind in availability. No AMI status or prediction performance appears in the rank key. No two competing nonempty diagnoses are observed among the 269 pairs. The component definition of pre-existing qc_nonmissing_count is NOT recovered; do not assert it uses only predictors or excludes diagnosis/procedure/outcome fields. Further HIS/ETL review required; no reselection in WP1.
''')
    md('03_COHORT_FLOW/CONSECUTIVE_SCREENING_AND_SELECTION_BIAS_AUDIT.md',f'''
# Recruitment and date-lineage hard gap
CONSECUTIVE = NOT_ESTABLISHED. No complete eligible angiography screening register, query/SQL inclusion criteria, extraction date/filters or exclusion ledger recovered. The analysis is a diagnosis-and-CBC-availability subset of a master export. It cannot be called a consecutive angiography cohort on this evidence alone.

The current downloaded manuscript states 2020-01-01 to 2026-01-01 and patient-level randomized institutional shifts within +/-182 days. In the actual frozen source, selected CBC years span {m['cbc_year_min']}-{m['cbc_year_max']}, with {m['primary_cbc_before_2019_n']}/1820 before 2019. Thus small bounded shifts cannot explain the discrepancy if CBC is intended to represent the stated index period. Historical tests outside that period are another possibility, but that would also undermine index-measurement interpretation and needs evidence.

The recovered date-shift R script reads an input master and writes a DISTINCT structure-preserved deidentified master. V05 instead reads the input master whose SHA256 is f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660. Its proof checks script text and an audit table, not actual linkage of the modeled rows/dates to that shifted output. Therefore institutional date transformation and application to the modeling input are NOT_VERIFIED. This is not evidence that the source dates are necessarily true calendar dates either.

Required: institutional export provenance, actual recruitment/index rule, dated screening denominator, deidentification specification and linkage of the exact hashed model input to it. Do not change dates, shift point, study period or frozen estimates to make them agree. WP1_HOLD_DUE_TO_SOURCE_DATA_GAP.
''')
    md('04_VALIDATION/VALIDATION_PIPELINE_AUDIT.md',f'''
# Canonical validation pipeline
Source `{CODE31}`: FoldPreprocessor lines156-216, make_tuned_pipeline219-246, repeated_splits397-406, run_nested_oof409 onward, patient_mean_predictions501-506, main1327 onward.

Outer: stratified 5-fold repeated10, seed20260825. Each patient receives10 out-of-training-fold predictions per model; total18200 before averaging in the primary cohort. Final reported metrics use ONE arithmetic mean probability per patient, not all repeated rows as independent cases and not mean repeat AUC. Repeat-wise median and quantiles are separate columns.

Inner: stratified5-fold; GridSearchCV on an sklearn Pipeline with training-local preprocessing. Elastic-net logistic SAGA; l1_ratio in0.25,0.5,0.75; C in0.1,1,10 (inverse regularization strength; not numerical glmnet lambda). Inner validation selects ROC AUC and refits on the outer training set. Core, Enhanced and clinical combination models use this path. Single-marker comparators have no tuned hyperparameters and use unpenalized logistic regression.

Preprocessing: missing medians fitted on the training split; Enhanced and Clinical allow imputation; CBC-only Core is complete. log1p(max(x,0)) for Neut/Lymph/Mono/PLT/Fbg and all seven ratios, specified in advance. MPV/RDW/Hb and clinical variables are standardized without that log transform. Mean/SD are training-fitted (ddof0); zero SD replaced by1. No winsorization. Deterministic variable construction and cohort selection occur before splitting; no evidence of leakage from fitted medians/scales/tuning in this canonical code. This does not eliminate selection bias or phenotype/timing validity concerns.

Identical outer partitions: code-supported YES for Core, Enhanced, PIV and all four clinical models on the same ordered1820 rows with the same target and outer seed. They are generated in separate analysis branches but deterministic same ordering/seed. Fbg complete-case models share their own1705-row folds. Inner seeds are model-label-specific; do not claim identical inner tuning partitions. Saved tuning records support10 repeats. Exact patient-fold artifacts were not persisted, so partition identity is code-based, not an independent stored-prediction audit.

Critical provenance boundary: `HITS_V0.3_score_development` is a DIFFERENT20-repeat legacy run. Its existing patient predictions must not be substituted for the verified10-repeat canonical run. No model has been rerun in WP1.
''')
    md('04_VALIDATION/BOOTSTRAP_CI_METHOD_AUDIT.md',f'''
# Bootstrap uncertainty
Source `{CODE31}` bootstrap_auc_ci527-538, paired_delta577-615; archived numbered source.

Metric and delta confidence intervals:1000 resamples of PATIENT rows from FIXED patient-averaged repeated OOF probabilities. Ordinary bootstrap with replacement; paired comparisons merge patient key and outcome1:1 and resample common rows together. Percentile2.5/97.5 intervals; single-class samples skipped and valid count saved. Model refit NO; fold regeneration NO; prediction regeneration NO. These intervals reflect resampling of the fixed evaluated patient-prediction pairs and do not incorporate full model-building or shared-training-dependence uncertainty. They must not be described as1000 complete nested pipeline repeats.

A SEPARATE300-replicate full-development bootstrap re-fits/tunes models for optimism/stability. It is not the1000-resample metric CI and not an external validation. Temporal fixed-validation paired bootstrap uses2000 resamples in V05/V051. Keep all three procedures distinct.
''')
    md('04_VALIDATION/TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md',f'''
# Temporal implementation versus provenance
Implementation verified from `{CODE05}` assign_guard_groups, fit_and_predict, execute_guardband and main. Type A: early training -> later fixed validation. Models are refitted/tuned on early data, not the full1820. Later cohort is prediction-only in the primary comparison. A separate3-repeat CV reference occurs ONLY inside development; later-subset repeated CV is not the primary temporal analysis.

Variable: parsed WBC test_time (called shifted_CBC_date by code). Nominal split2015-01-01, B182 + safety1 day. Early <=2014-07-02; late >=2015-07-03; intervening buffer excluded. Counts reverified descriptively: early1001/196 AMI, buffer271/79, later548/178. High-specificity late426/138; all match frozen registry counts. PIV is a raw ordinal index in temporal validation, not a fitted probability model. No PIV temporal calibration or DCA is supported.

Frozen Core AUC0.701321 vs PIV0.699059; difference0.002262, paired CI crosses0. Enhanced0.719283. Preserve values but acknowledge the internal incremental advantage over PIV is not supported to the same extent temporally. Exact numbers are read-only in registry/paired tables.

CRITICAL: the claimed institutional shifted-date provenance is not established. date_bound_proof inspects a different export-generating script and parsed-count audit; it does not prove the modeled input is the shifted output. Its recovered deterministic offset formula is not a documented randomized institutional transform. Source CBC years conflict with stated2020-2026 recruitment. Therefore implementation counts can be reproduced while the claim of bounded-shift clinical temporal transportability remains ON HOLD. Do not equate arithmetic guard-band separation with clinically verified chronology or external validation.
''')
    md('04_VALIDATION/CALIBRATION_PREDICTION_PROVENANCE.md',f'''
# Calibration: two incompatible source branches
Table2 metrics: canonical verified10-repeat patient-averaged OOF predictions, numeric outputs in `{V31}/05_nested_cv_robustness.csv` and registry. Joint binomial GLM y~intercept+logit(p), probability clipped1e-6 to1-1e-6. The intercept is jointly fitted with slope, not a slope-fixed-at-one calibration-in-the-large intercept.

Submitted Figure3 source CSV has20 rows (two models x10 bins) with model/bin/mean_predicted/observed_rate; NO per-bin N. The recovered R manuscript builder reads `HITS_V0.3_score_development/17_v0_3_1_oof_patient_mean_predictions.csv`, the LEGACY20-repeat output. It builds quantile deciles using R quantile(type=8), unique breaks and cut(include.lowest=TRUE), then mean predicted probability and observed outcome. Recovered renamed plotting script still references Figure4_source_data.csv although bundled data are named Figure3_source_data.csv: standalone reproducibility mismatch.

The legacy existing summary reports Core AUC0.725036, intercept-0.034419, slope0.965533 (20 repeats), whereas Table2 canonical Core AUC0.725350, intercept-0.025793, slope0.973876 (10 repeats). Thus close rounded AUC does NOT establish identical prediction provenance. This is a reporting-lineage conflict, not permission to replace canonical estimates. Figure2 ROC inherits the same legacy OOF branch and needs future source reconciliation too.

The canonical script explicitly states 'Never persist records' and only writes aggregates. Legacy patient-level predictions exist locally for all four clinical models, but are not canonical. No verified canonical prediction file recovered. Counts per bin and canonical probability distribution require recovery/authorized regeneration in WP2, not a new plot in WP1. Historical legacy bins cannot solve this. No calibration or ROC was calculated here.
''')
    md('05_MISSINGNESS/FIBRINOGEN_FAIR_COMPARISON_AUDIT.md',f'''
# Fibrinogen comparison
Primary available1705/1820; AMI426/453 (27 missing,5.9603%); non-AMI1279/1367 (88 missing,6.4375%). Similar observed proportions do not establish MCAR/MAR or exclude outcome-specific selection.

Code `{CODE31}` builds primary_fbg_cc ONCE requiring all Enhanced features; Core and Enhanced evaluated in one run_nested_oof call on the same1705 patients,426 events, same outer partitions. Paired bootstrap merge uses the same patient keys/outcome. This supports same-person/same-fold/paired comparison in code. Canonical existing Core AUC0.727061 and Enhanced0.736739; delta0.009678 with95% CI0.002300 to0.016932. No rerun. Strict CC1418 patients also exists. Main Enhanced1820 uses fold-specific median imputation, not complete-case deletion.

No dedicated missingness model or inferential missingness test run in WP1. Timing and lineage caveats remain independent of comparison fairness.
''')
    md('05_MISSINGNESS/AGE_DEFINITION_DISCREPANCY.md','''
# Age discrepancy: do not overwrite the corrected manuscript definition
Required priority: main birth_date first, baseline birth date fallback only. The current Python build_patient_frame follows that priority, uses admission date or CBC date if admission is missing, divides by365.2425 and accepts18-120 years. Its descriptive parse yields1820 available (453 AMI,1367 controls), matching historical canonical missingness output age missing0.

Current downloaded manuscript explicitly says1818 available (452/1366). That two-patient exclusion/derivation has NOT been reproduced from a recovered executable correction. Old R Table1 builders instead prioritized baseline birth date and used admission-only age, a different faulty branch. Do not restore that branch and do not silently change1818 to1820.

The CSV reports current-source parsed availability AND manuscript-reported availability separately. The final corrected age vector/reference-date rule and hash need recovery. Clinical model performance numbers exist, but whether they correspond to the manuscript-corrected age definition is UNRESOLVED. No new clinical model fitted. A correction may require explicit WP2 rerun authorization once derivation is locked.
''')
    cm=pd.read_csv(OUT/'05_MISSINGNESS/CLINICAL_VARIABLE_MISSINGNESS.csv')
    cm=cm[cm.provenance.eq('Current descriptive parse; NOT a model rerun')].drop_duplicates().copy()
    cm['definition_status']='CURRENT_CODE_DESCRIPTIVE; not accepted as corrected-age lock'
    for group,n,a in [('overall',1820,1818),('AMI',453,452),('non_AMI',1367,1366)]:
        cm=pd.concat([cm,pd.DataFrame([dict(group=group,variable='age',n=n,available_n=a,missing_n=n-a,missing_pct=100*(n-a)/n,provenance='Manuscript Table1 reported; derivation not reproduced',definition_status='AUTHOR_CORRECTED_DEFINITION_REQUIRED')])],ignore_index=True)
    csv('05_MISSINGNESS/CLINICAL_VARIABLE_MISSINGNESS.csv',cm.drop_duplicates())
    md('06_COMPARATORS/PIV_COMPARATOR_METHOD_AUDIT.md',f'''
# PIV comparator
PIV=PLT*absolute Neut*absolute Mono/absolute Lymph. Internal canonical code `{CODE31}` applies fixed log1p(max(PIV,0)), training-fold centering/scaling, then unpenalized univariable logistic regression with fitted intercept/slope. Same1820 patients and same outer5x10 partitions as Core; aggregation is the same patient arithmetic mean. No PIV hyperparameter search is needed. This supports procedural fairness for internal discrimination comparison, not clinical superiority.

Clinical+PIV instead uses the clinical covariates and PIV together in tuned elastic-net; clinical+Core/+Enhanced internally enter the raw component features jointly, not a separately fitted scalar blood score. Temporal clinical combinations use frozen blood-score features and a different520-patient analysis: do not conflate these architectures.

Temporal standalone PIV is the raw ordinal ratio on validation patients, AUC only, unlike internally calibrated logistic PIV. Monotonic transformation does not by itself change ordinal AUC, but it does not produce a probability. Do not calculate PIV temporal Brier/calibration/DCA using raw values.
''')
    md('06_COMPARATORS/COLLINEARITY_EXISTING_EVIDENCE_AUDIT.md',f'''
# Existing dependence evidence
`{V31}/16_variable_stability.csv`:300 full-development bootstrap fits; selection frequency, median/mean standardized coefficient, sign consistency, selected C/l1_ratio. Existing coefficient distributions and stability summaries are not a Core7 correlation matrix or VIF.

V051 has Hb-related correlation/direction diagnostics and PDW-year correlation exists earlier; these answer specific questions and do not replace a complete Core7 predictor-dependence audit. No canonical full Core7 Pearson/Spearman matrix, VIF or elastic-net path recovered in inspected result sets. No such analysis was computed in WP1.

WP2 smallest useful addition after source clearance: one descriptive Spearman matrix on frozen Core7; optional VIF explicitly descriptive. Report existing bootstrap stability with its actual resampling origin, not as repeated-CV selection frequency. No new selection/drop of Core7 variables, no outcome-driven architecture search.
''')
    md('06_COMPARATORS/TROPONIN_FEASIBILITY_AUDIT.md','''
# Troponin feasibility
Decision: NOT_VALID_FOR_UNIFIED_MODEL with current recovered data.
Fields found: cTnI, cTnT, hs_cTnT, each with result/unit/test_time and duplicate-named companion fields. No dedicated hs_cTnI column recovered. Nonmissing raw results:173,88,390 respectively of1820; timestamps173,90,402. Counts are not additive unique-patient coverage and duplicate-named columns must not be counted as additional assays. CK-MB appears in only1 record. See inventory for exact field names and units.

Units include ng/ml/ng/mL and ug/L. These concentration units are dimensionally compatible; their notation alone is NOT the primary problem. Assay platform/manufacturer/generation,99th-percentile ULN and sex-specific reference limits were not recovered from headers/dictionary; no validated assay-specific sampling window, serial rise/fall or index diagnosis relation exists. Calendar distribution differs across assays. Test result nonmissing is not the same as usable quantitative result (censoring/non-numeric reporting can occur).

Do not pool assays into an incremental model or silently treat absent tests as negative. A restricted assay-specific descriptive comparison could only be considered after platform/ULN/time retrieval and new authorization. Current reviewer strategy: explain limitations and phenotype-discrimination positioning, not replacement for troponin. No troponin model run.
''')
    md('06_COMPARATORS/DCA_FEASIBILITY_AUDIT.md',f'''
# DCA feasibility
Canonical Clinical/Clinical+PIV/Clinical+Core/Clinical+Enhanced patient probabilities: NOT_RECOVERED. The verified script deliberately does not persist patient-level records. Legacy20-repeat probabilities exist for all four, but frozen canonical10-repeat values differ; they must not be used as a substitute.

Technical feasibility today using valid canonical existing artifacts: NO. Conditional feasibility: recover exact canonical probabilities, or obtain explicit authorization for a deterministic regeneration after source/age issues are settled. No re-fit or DCA is authorized by this document.

An existing exploratory blood-only DCA is not the requested four-clinical-model comparison. If future WP2 permits it, use identical patients and exact probabilities, prespecified clinically defensible thresholds, treat-all/none, and retrospective phenotype caveats. Clinical deployment/net-benefit claim is not warranted by this audit.
''')
    md('07_ETHICS/ETHICS_CONSENT_HARD_GATE.md','''
# Ethics hard gate
AUTHOR_DOCUMENT_CONFIRMATION_REQUIRED

User-provided approval reference K202602-10; committee Ethics Committee of Xinjiang Medical University. Current local manuscript states all participants provided informed consent. Neither this statement nor a previous editorial consistency PASS is evidence of the actual approval/consent document.

Author must provide/verify approval document and approved study population/dates, consent wording, waiver wording if any, broad research consent scope, hospitalization/angiography consent applicability, representative/deceased patient provisions and permitted data reuse. No waiver, written-consent or representative-consent statement is inferred here. Approval number authenticity/scope is not verified by WP1.

Do not upload private consent forms or identifiable ethics attachments to the public repository. Only author-confirmed nonidentifying declarations can later be published. WP3 wording awaits documentary confirmation.
''')
    md('07_ETHICS/HUMAN_RESEARCH_GUIDELINES_REQUIREMENT.md','''
# Editor-required guidelines statement
EDITOR_REQUIRED_TEXT = YES
Required idea: all methods were performed in accordance with relevant guidelines and regulations.
WP1 records the request only. Full contextual wording and insertion belong to WP3 after ethics/source confirmation. It is not a substitute for approval/consent evidence.
''')
    md('08_REVISION_PLANNING/CONCLUSION_CLAIM_AUDIT.md','''
# Claims audit
MINOR_REWRITE_NEEDED for the current local conclusion language; CRITICAL source/reporting gates remain unresolved independently.
Current abstract acknowledges temporal attenuation, modest internal gain and need for independent time-anchored evaluation before implementation. No supported claim of a triage-ready diagnostic tool, replacement for troponin/PIV, or broad generalizability was recovered in the conclusion. Maintain that boundary.

Future WP3 should state explicitly that Core-PIV temporal paired CI crosses zero and avoid interpreting high-specificity diagnosis-text restriction as independent adjudication. The assertion that shifted dates explain inability to align index times is insufficient: a common patient-level shift preserves within-patient intervals, whereas current CBC/admission gaps are years. Institutional shift wording and2020-2026 date claims need source repair, not cosmetic softening. No manuscript text changed in WP1.
''')
    # Comment source is the adopted task summary, not a recovered verbatim decision letter.
    specs=[
      ('E1','CBC/fibrinogen selection and timing','01_TIMING/CBC_INDEX_MEASUREMENT_RULE_AUDIT.md','SOURCE_DATA_AUDIT_REQUIRED','CRITICAL','Recover index encounter and laboratory ETL; no pre-angiography claim','Methods'),
      ('E2','AMI label provenance and clinical adjudication','02_PHENOTYPE/AMI_LABEL_PROVENANCE_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','HIGH','Report text-derived phenotype; do not invent adjudication','Methods/limitations'),
      ('E3','Reconcile2548 to2279','03_COHORT_FLOW/MOST_COMPLETE_RECORD_SELECTION_RULE.md','EXISTING_RESULT_NEEDS_REPORTING','HIGH','Report269 surplus rows, not269 proven repeat admissions','Flow/Methods'),
      ('E4','Nested validation, aggregation and bootstrap','04_VALIDATION/VALIDATION_PIPELINE_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','MODERATE','Report5x10/inner5 and fixed averaged-prediction bootstrap','Statistics'),
      ('E5','Temporal validation design','04_VALIDATION/TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md','SOURCE_DATA_AUDIT_REQUIRED','CRITICAL','Verify date lineage before temporal claim; retain frozen estimates','Methods/limitations'),
      ('E6','High-specificity phenotype flow','02_PHENOTYPE/HIGH_SPECIFICITY_AMI_COHORT_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','HIGH','Explain453 to178 to138; later R flowchart only after approval','Supplement'),
      ('E7','Fibrinogen missingness and same-sample comparison','05_MISSINGNESS/FIBRINOGEN_FAIR_COMPARISON_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','MODERATE','Report by-outcome availability and paired CC comparison','Results/Supplement'),
      ('E8','Clinical missingness and full incremental performance','05_MISSINGNESS/AGE_DEFINITION_DISCREPANCY.md','SOURCE_DATA_AUDIT_REQUIRED','HIGH','Recover corrected age vector before clinical-model reuse','Methods/Results'),
      ('E9','Calibration provenance and Figure5 intervals','04_VALIDATION/CALIBRATION_PREDICTION_PROVENANCE.md','SUBSTANTIAL_NEW_ANALYSIS_REQUIRED','CRITICAL','Recover canonical predictions; reconcile legacy figure branch; no rerun now','Figures/Table2'),
      ('E10','Conclusions and clinical positioning','08_REVISION_PLANNING/CONCLUSION_CLAIM_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','MODERATE','Acknowledge limited internal increment and temporal uncertainty','Discussion/Conclusions'),
      ('E11','Human research guidelines statement','07_ETHICS/HUMAN_RESEARCH_GUIDELINES_REQUIREMENT.md','AUTHOR_ETHICS_INPUT_REQUIRED','HIGH','Verify documents; insert text only in WP3','Declarations'),
      ('R1-M1','Validation rigor and temporal generalizability','04_VALIDATION/TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md','SOURCE_DATA_AUDIT_REQUIRED','CRITICAL','Separate code verification from date-source validity','Statistics/limitations'),
      ('R1-M2','Core predictor collinearity','06_COMPARATORS/COLLINEARITY_EXISTING_EVIDENCE_AUDIT.md','LIGHTWEIGHT_NEW_ANALYSIS_REQUIRED','MODERATE','WP2 descriptive Spearman only; do not reselect','Supplement'),
      ('R1-M3','Clinical covariate missingness handling','05_MISSINGNESS/AGE_DEFINITION_DISCREPANCY.md','SOURCE_DATA_AUDIT_REQUIRED','HIGH','Resolve1818 versus1820; document fold-local imputation','Methods/Table1'),
      ('R1-M4','All traditional index benchmarks','06_COMPARATORS/TRADITIONAL_INDEX_PERFORMANCE_INVENTORY.csv','EXISTING_RESULT_NEEDS_REPORTING','LOW','Report all7 existing AUC/CI; PIV remains primary','Supplement'),
      ('R1-M5','Repeat records and prior cardiovascular history','03_COHORT_FLOW/MOST_COMPLETE_RECORD_SELECTION_RULE.md','SOURCE_DATA_AUDIT_REQUIRED','HIGH','Recover encounter/history semantics; row counts already reconcile','Methods/Table1/flow'),
      ('R1-M6','Fairness of PIV comparison','06_COMPARATORS/PIV_COMPARATOR_METHOD_AUDIT.md','EXISTING_RESULT_NEEDS_REPORTING','MODERATE','Explain internal log-logistic vs temporal ordinal comparison','Statistics'),
      ('R1-M7','Troponin comparison','06_COMPARATORS/TROPONIN_FEASIBILITY_AUDIT.md','NOT_FEASIBLE_WITH_VALID_DATA','HIGH','Do not pool incomparable assays; request assay/ULN/time only if retrievable','Limitations'),
      ('R1-m1','Consecutive screening','03_COHORT_FLOW/CONSECUTIVE_SCREENING_AND_SELECTION_BIAS_AUDIT.md','SOURCE_DATA_AUDIT_REQUIRED','CRITICAL','Retrieve screening/extraction register; do not assert consecutive','Setting'),
      ('R1-m2','CBC timing clarification','01_TIMING/CBC_INDEX_MEASUREMENT_RULE_AUDIT.md','SOURCE_DATA_AUDIT_REQUIRED','CRITICAL','State completeness-ranked row, not first/pre-event sample','Methods'),
      ('R1-m3','Informed consent in retrospective cohort','07_ETHICS/ETHICS_CONSENT_HARD_GATE.md','AUTHOR_ETHICS_INPUT_REQUIRED','CRITICAL','Documentary author confirmation; no inferred waiver','Declarations'),
      ('R2-1','DCA for clinical incremental models','06_COMPARATORS/DCA_FEASIBILITY_AUDIT.md','SUBSTANTIAL_NEW_ANALYSIS_REQUIRED','HIGH','Canonical OOF recovery required before any authorized DCA','Supplement/limitations')]
    matrix=[]
    refs={
      'E1':('master_cohort_cleaned.csv',CODE02,'select_one_row_per_patient; build_patient_frame'),
      'E2':('master_cohort_cleaned.csv',CODE02,'classify_diagnosis'),
      'E3':('master_cohort_cleaned.csv',CODE02,'select_one_row_per_patient'),
      'E4':(V31+'/05_nested_cv_robustness.csv',CODE31,'run_nested_oof; patient_mean_predictions; bootstrap_auc_ci'),
      'E5':(FREEZE+'/04_CANONICAL_RESULT_REGISTRY.csv',CODE05,'assign_guard_groups; execute_guardband; date_bound_proof'),
      'E6':('master_cohort_cleaned.csv',CODE05,'high_specificity_flag; guard_masks'),
      'E7':(V31+'/10_fibrinogen_complete_case_sensitivity.csv',CODE31,'main: primary_fbg_cc; paired_delta'),
      'E8':(V31+'/08_clinical_incremental_models.csv',CODE02+'; '+CODE31,'build_patient_frame; clinical_specs'),
      'E9':(BMC+'/Figure3_source_data.csv; '+FREEZE+'/04_CANONICAL_RESULT_REGISTRY.csv','scripts/build_hits_manuscript_v1.R; '+CODE31,'cal_curves; calibration_stats'),
      'E10':('LOCAL_DOWNLOADS/'+doc.name,'NOT_APPLICABLE','Abstract/Discussion/Conclusions'),
      'E11':('User WP1 instruction; ethics document NOT_RECOVERED','NOT_APPLICABLE','Guidelines requirement'),
      'R1-M1':(V31+'/05_nested_cv_robustness.csv; '+FREEZE+'/04_CANONICAL_RESULT_REGISTRY.csv',CODE31+'; '+CODE05,'nested CV and fixed later validation'),
      'R1-M2':(V31+'/16_variable_stability.csv',CODE31,'summary_stability; bootstrap_optimism'),
      'R1-M3':('master_cohort_cleaned.csv; LOCAL_DOWNLOADS/'+doc.name,CODE02+'; '+CODE31,'build_patient_frame; FoldPreprocessor'),
      'R1-M4':(V31+'/06_traditional_marker_comparison.csv',CODE31,'benchmark_specs; performance_table'),
      'R1-M5':('master_cohort_cleaned.csv; field_dictionary.csv',CODE02,'select_one_row_per_patient'),
      'R1-M6':(V31+'/06_traditional_marker_comparison.csv',CODE31+'; '+CODE05,'make_ordinary_pipeline; evaluate_cohort'),
      'R1-M7':('master_cohort_cleaned.csv; field_dictionary.csv','09_CODE/audit_sources.py','TROPONIN_FIELD_INVENTORY.csv'),
      'R1-m1':('LOCAL_DOWNLOADS/'+doc.name+'; master_cohort_cleaned.csv','scripts/03_create_reviewer_rescue_package.R; '+CODE05,'source input/output paths; date_bound_proof'),
      'R1-m2':('master_cohort_cleaned.csv',CODE02,'select_one_row_per_patient; build_patient_frame'),
      'R1-m3':('LOCAL_DOWNLOADS/'+doc.name+'; ethics document NOT_RECOVERED','NOT_APPLICABLE','Consent declaration; user WP1 instruction'),
      'R2-1':('HITS_V0.3_score_development/17_v0_3_1_oof_patient_mean_predictions.csv (legacy only)',CODE31,'main: never persist records')}
    for ident,summary,report,fc,risk,action,section in specs:
        source,code,obj=refs[ident]
        matrix.append(dict(reviewer_id=ident,exact_comment_summary=summary,comment_source='USER_WP1_INSTRUCTION_SUMMARY; VERBATIM_LETTER_NOT_RECOVERED',scientific_issue=summary,current_manuscript_status='Downloaded EthicsNumber v1.2 reviewed; exact portal snapshot not verified',existing_evidence=report,exact_source_file=source,**{'exact_code/script':code},exact_result_object=obj,source_data_required='YES' if fc in ['SOURCE_DATA_AUDIT_REQUIRED','NOT_FEASIBLE_WITH_VALID_DATA','SUBSTANTIAL_NEW_ANALYSIS_REQUIRED'] else 'NO_FOR_EXISTING_REPORT',new_analysis_required='WP2_AUTHORIZATION_ONLY' if 'NEW_ANALYSIS' in fc else 'NO_AUTOMATIC_ANALYSIS',ethics_author_input_required='YES' if fc=='AUTHOR_ETHICS_INPUT_REQUIRED' else 'SOURCE_OWNER_IF_GAP',feasibility_class=fc,risk_level=risk,recommended_response_strategy=action,WP2_action=action,manuscript_section_to_modify_later=section,status='AUDITED_NOT_RESPONSE_READY'))
    csv('00_EXECUTIVE_SUMMARY/REVIEWER_COMMENT_MASTER_MATRIX.csv',matrix)
    risk_specs=[('CBC timing','CRITICAL','130 dates, multi-year gaps; index sample unproven'),('AMI label validity','HIGH','Discharge text only; no independent review'),('Record selection','HIGH','Diagnosis availability ranked; qc score definition unknown'),('Validation leakage','MODERATE','Canonical fitted preprocessing fold-local; prior variable selection/lineage not eliminated'),('Bootstrap CI provenance','MODERATE','Fixed prediction bootstrap, not full pipeline uncertainty'),('Temporal source/period mismatch','CRITICAL','1802 CBC before2019; stated2020-2026; shift input/output not linked'),('Consent consistency','CRITICAL','Author documents required'),('Troponin feasibility','HIGH','Assay/ULN/index time unresolved'),('Missing fibrinogen','MODERATE','115 missing, timing not anchored'),('Clinical covariate missingness','HIGH','Corrected age denominator1818 not reproduced'),('Figure/canonical lineage','CRITICAL','Figure3 legacy20-repeat versus Table2 canonical10-repeat'),('Prediction recovery/DCA','HIGH','Canonical OOF not persisted'),('Reviewer/source document completeness','HIGH','Full verbatim decision letter and portal snapshot not recovered'),('R figure reproducibility','HIGH','Renamed source mismatches and hardcoded Figure4/5 numbers in recovered script')]
    csv('00_EXECUTIVE_SUMMARY/REVISION_RISK_REGISTER.csv',[dict(risk_id=f'R{i:02}',issue=x,risk_level=r,evidence=e,status='OPEN',mitigation='See corresponding audit; WP2 not authorized') for i,(x,r,e) in enumerate(risk_specs,1)])
    skeleton=['# Reviewer response skeleton','Not a response letter. Verbatim letter needs recovery; summaries below come from user WP1 instructions.']
    for ident,summary,report,fc,risk,action,section in specs:
        skeleton.extend([f'\n## {ident}: {summary}','Response: [NOT DRAFTED IN WP1]',f'Evidence: {report}',f'Action: {action}',f'Manuscript change: [WP3 ONLY] {section}','Status: AUDITED / AWAITING AUTHORIZATION'])
    md('08_REVISION_PLANNING/RESPONSE_TO_REVIEWERS_SKELETON.md','\n'.join(skeleton))
    md('08_REVISION_PLANNING/WP2_ANALYSIS_AUTHORIZATION_PLAN.md','''
# WP2 authorization plan (NOT authorization)
Gate: WP1_HOLD_DUE_TO_SOURCE_DATA_GAP. Resolve source blockers before targeted computation. No manuscript or response-letter edit is authorized here.

## A. Already done: report only
Code-based validation/preprocessing/aggregation/bootstrap descriptions; row-level2548->2279 reconciliation; phenotype and high-specificity counts; fibrinogen by-outcome missingness; same-sample CC comparison; all7 traditional benchmark AUC/CIs; existing clinical performance with age-provenance warning;9 of12 Figure5 AUC CIs.

## B. Lightweight new analysis recommended after approval
Descriptive Core7 Spearman matrix (optional VIF). Canonical prediction distributions/group counts and3 asymmetric AUC intervals ONLY if exact predictions recovered. R-only figures with per-figure source CSV/script and registry-loaded values; replace hardcoded figure inputs. None performed in WP1.

## C. Substantial conditional work
If canonical predictions cannot be recovered, reproducible regeneration requires EXPLICIT authorization despite unchanged seeds/model. Resolve age and data-source lineage first; otherwise rerunning propagates uncertainty. Clinical incremental paired CIs and four-model DCA depend on the resulting locked predictions. No architecture search or result-driven optimization.

## D. Source review only
Hospital export/SQL and eligible angiography screening register; actual study dates; patient-to-encounter linkage; lab sample-selection rule; actual institutional deidentification spec and exact model-input lineage; corrected age derivation; primary versus legacy OOF/figure ancestry. Recover full original reviewer letter and portal-submitted manuscript snapshot to bind comment numbering and manuscript status.

## E. Author/ethics input
K202602-10 document/scope and consent/waiver wording; approved cohort period and research consent applicability. Status remains AUTHOR_DOCUMENT_CONFIRMATION_REQUIRED.

## F. Do not do
New Core combinations, score search, outcome-driven thresholds, pooled troponin model without valid assay/time data, SHAP/nomogram/NRI/IDI, claim future prediction/triage/clinical superiority, substitute legacy OOF for canonical, infer consent or consecutive recruitment, change frozen scientific files, enter WP2 automatically or merge the PR.
''')
    answers=[
      'CBC来自按诊断存在、四项CBC非缺失数、WBC时间存在、qc完整度及原始行序排序后选中的同一宽表行；不是最早CBC规则。',
      'Admission仅130/1820有日期；CBC差值中位数-1754.205天，无法认作同次住院时序。造影/首次诊断时间未恢复；TIMING_RECONSTRUCTION=NOT_FEASIBLE（当前材料）。',
      'Fbg时间1707，数值1705；与CBC同日1553/1707。可计算检验间差值，但不能证明同次入院/术前。',
      '直接来源是discharge_diagnosis文本规则；不是肌钙蛋白或ECG裁定。',
      '没有找到独立医生复核的可核验证据，不能声称已完成。',
      '2010人各1行、269人各2行；269条是同ID多余行，整行完全重复0；没有证据称其均为独立重复住院。',
      '多行患者269；可靠重复住院人数UNKNOWN。17组有一个入院日期，252组无日期，无组有两个不同非缺失入院日期。',
      '精确排序见第1项；时间只判断有无，不按先后；qc_nonmissing_count的上游组件未恢复。',
      '诊断可用性参与选择，存在选择偏倚风险；未见按AMI标签/模型效果择行。269组均没有两条竞争的非空诊断。',
      'Canonical outer5折x10次，inner5折，elastic-net l1_ratio0.25/0.5/0.75，C0.1/1/10；单指标无需调参。',
      '拟合中位数/中心/标准差及调参局限在训练折；固定转换先验指定。代码层成立，不代表上游选择/时序无偏。',
      '每人10个OOF概率取算术平均，再计算患者层性能；重复AUC分布另报。',
      '1000次抽样固定的患者平均OOF预测及其结局；配对比较同抽患者；无模型重拟合、无重分折、无新预测。',
      '较早组训练、较晚组固定验证；development内另有3次CV参考，不是later组内CV。日期来源仍未证实。',
      '早期1001/196 AMI，缓冲271/79，后期548/178；源CBC有1802人早于2019，与稿件2020-2026冲突待回源。',
      '453-196早期-79缓冲=178后期；再排40条不符高特异文本规则=138；对照288，总426。',
      '使用出院后汇总诊断信息；阳性规则不使用肌钙蛋白、ECG或治疗证据，strict对照可含血运重建文字。',
      'AMI缺27/453=5.9603%；non-AMI缺88/1367=6.4375%；总115/1820=6.3187%。',
      '代码层同人同fold并配对：1705人、426 AMI；既存完整病例delta0.009678，CI0.002300-0.016932。',
      '性别0缺；高血压79缺（AMI18/对照61）；糖尿病48缺（11/37）。稿件年龄1818可用（452/1366），当前Python及历史canonical为1820；不擅自覆盖，待恢复修正来源。',
      '四临床模型N/AMI/AUC/CI/Brier/校准均有；对Clinical基础模型的配对增量CI和内部Enhanced对PIV增量CI未恢复。数字存在不等于年龄版本一致。',
      'Table2为canonical10次平均OOF；Figure3溯源指向legacy20次平均OOF。不能称同一预测集；需回收canonical预测修复图源。',
      'Figure5前三类各3模型共9个AUC CI已有；alternative/asymmetric3个只有AUC，无单模型CI；deltaCI不能替代。',
      '有300次full-development bootstrap系数/选择频率/符号稳定性和部分Hb诊断；完整Core7相关矩阵/VIF未恢复，本轮未新算。',
      'NLR/PLR/MLR/SII/SIRI/PIV/HRR均有主及strict验证AUC/CI；保留PIV为主要比较。',
      '内部PIV为log1p+训练标准化+单变量无惩罚logistic，同人同outer折；时间验证为raw ordinal AUC，不是校准概率。',
      'NOT_VALID_FOR_UNIFIED_MODEL：cTnI173、cTnT88、hs-cTnT390原始结果非空，平台/ULN/有效index时序未恢复；不直接相加或合并。',
      '不能有证据地称consecutive；入组筛查台账、完整造影母队列及ETL未恢复。',
      'AUTHOR_DOCUMENT_CONFIRMATION_REQUIRED；批准号/稿件声明不是知情同意文件证明。',
      '当前不能用有效canonical既存预测直接做新DCA：canonical未保存，legacy虽存在不可替代；需恢复或另行授权再生。',
      'E2/E3/E4/E6/E7/E10/R1-M4/R1-M6主要可整理已有证据；仍受源数据/表述边界限制。',
      '获授权后可做Spearman、未有CI/配对CI、canonical分布/分组数及条件性DCA；canonical预测再生属于需单独授权的重分析。',
      '作者需确认伦理与同意、真实研究期/筛查范围/日期平移、实验室与住院时序、年龄修正及实际投稿/原始评审文件。',
      GATE+'；审计交付完成不等于返修可提交。未进入WP2。'
    ]
    md('00_EXECUTIVE_SUMMARY/WP1_EXECUTIVE_SUMMARY.md',f'''# HITS BMC Revision WP1

Date:2026-09-29. User-reported revision requested; submission ID fa1e4873-011b-4f15-8b0d-29f6df21fabe. Internal deadline2026-10-10; journal deadline2026-10-12 (user instruction, not portal-verified).

## Gate
**{GATE}**

已完成本地证据恢复与描述性审计，不修改manuscript、不重跑Core/Enhanced、不新增DCA/校准/共线性模型、不生成图。22条意见已建矩阵，原始评审信未恢复，不能将摘要伪装成逐字原文。

## 三个首要问题
1. **研究期/日期来源**：当前实际输入CBC年份与2020-2026稿件入组期冲突，1802/1820早于2019；±182天无法解释。平移程序输入/输出和模型输入尚未形成验证链。
2. **图表和预测版本混用**：Table2来自verified10次CV；可恢复的Figure3/ROC脚本使用legacy20次OOF。Canonical代码没有保存患者预测。必须恢复准确来源，不允许用近似AUC替代。
3. **伦理/年龄证据缺口**：知情同意须作者文件确认；稿件年龄1818与当前代码及历史输出1820不一致，不能假定已修复。

## 冻结保护
主队列1820、AMI453、non-AMI1367重现；冻结AUC和CI只读取。数值仍保留原值，但源证据缺口影响其可解释性。PDW维持DROP、Core7架构不变。本仓库仅汇总、代码和短摘录，不含患者级数据。公开仓库由用户明确授权，PR保持OPEN不合并。

## 34项直接回答
'''+ '\n\n'.join(f'{i}. {a}' for i,a in enumerate(answers,1))+'''

## 审阅入口
- REVIEWER_COMMENT_MASTER_MATRIX.csv:22条评论、证据及后续动作。
- REVISION_RISK_REGISTER.csv:14项风险，包含新发现的版本与来源冲突。
- ../08_REVISION_PLANNING/WP2_ANALYSIS_AUTHORIZATION_PLAN.md:需审阅批准，不构成授权。
- ../09_CODE/evidence/CANONICAL_RESULT_REGISTRY.csv:原冻结数字；../09_CODE/SOURCE_MANIFEST.csv:源文件校验。

复现范围：有权限的本地源文件持有者可重跑09_CODE描述性审计；公开仓库不可能在没有受控原始数据时重建患者级分析。未以不存在的文件宣称完全复现。
''')
    md('09_CODE/README.md','''
# Reproduction and privacy
Python3 with pandas/numpy; no model fitting/plotting dependencies used by audit_sources.py. Set HITS_PROJECT_ROOT and HITS_MASTER_CSV to protected local paths, optionally HITS_CURRENT_DOCX. Run audit_sources.py then build_reports.py. The expected master SHA256 is enforced. Frozen source scripts are loaded via an AST allowlist of pure parsing/selection functions; no main/model/plot code is executed. Metadata/aggregate files alone are written.

The source_excerpts directory is redacted, numbered READ-ONLY code evidence, NOT runnable model instructions. It includes historical Python plotting functions only as archival evidence; WP1 does not execute them and future plotting remains R-only. The source functions/dictionary contain field NAMES but no patient values. Canonical aggregates are copied, never re-estimated.

The age-discrepancy CSV deliberately distinguishes CURRENT_CODE_DESCRIPTIVE from AUTHOR_CORRECTED_DEFINITION_REQUIRED. Do not collapse them. Figure-source filenames changed across manuscript stages; follow content ancestry, not the figure number alone.

No credentials, patient identifiers, admission tokens, individual diagnoses, patient predictions, full manuscripts or ethics documents belong in this public package. Source owner must independently retain protected records. No third-party worker received patient data.
''')
    csv('09_CODE/SOURCE_MANIFEST.csv',manifest)
    assert all(digest(ROOT/x['source'])==x['sha256'] for x in manifest if not x['source'].startswith('LOCAL_DOWNLOADS/'))
    assert len(matrix)==22 and len(set(x['reviewer_id'] for x in matrix))==22
    assert abs(float(reg[(reg.analysis_id=='V031_PRIMARY_OOF')&(reg.model=='Core')].iloc[0].AUC)-float(perf[(perf.analysis=='primary_core')&(perf.model=='Continuous_HITS_Core')].iloc[0].oof_auc))<1e-12
    md('09_CODE/run.log','Descriptive source audit: PASS, hash verified, cohort1820/453.\nReports: PASS,22 comments; no modeling, no figures, no manuscript changes.\nScientific gate: '+GATE+'\nSource hashes unchanged after read-only inspection.\nCanonical result values copied, not recalculated.\n')
    print(json.dumps(dict(gate=GATE,comments=len(matrix),source_files=len(manifest),file_count=len([p for p in OUT.rglob('*') if p.is_file()]),models_run=0,figures_created=0)))


if __name__=='__main__':
    main()
