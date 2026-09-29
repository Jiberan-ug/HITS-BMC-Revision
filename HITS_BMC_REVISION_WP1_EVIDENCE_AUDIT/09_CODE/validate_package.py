"""Bounded privacy and integrity checks. Protected identifiers stay in memory."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile
import pandas as pd

OUT=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ['HITS_PROJECT_ROOT'])
MASTER=Path(os.environ['HITS_MASTER_CSV'])
required={
'00_EXECUTIVE_SUMMARY':['WP1_EXECUTIVE_SUMMARY.md','REVIEWER_COMMENT_MASTER_MATRIX.csv','REVISION_RISK_REGISTER.csv'],
'01_TIMING':['CBC_TIMING_VARIABLE_INVENTORY.csv','CBC_INDEX_MEASUREMENT_RULE_AUDIT.md','CBC_TIMING_COVERAGE.csv','FIBRINOGEN_TIMING_COVERAGE.csv'],
'02_PHENOTYPE':['AMI_LABEL_PROVENANCE_AUDIT.md','HIGH_SPECIFICITY_AMI_COHORT_AUDIT.md','SUPPLEMENTARY_HIGHSPEC_FLOW_SOURCE.csv'],
'03_COHORT_FLOW':['REPEATED_ADMISSION_FLOW_AUDIT.csv','MOST_COMPLETE_RECORD_SELECTION_RULE.md','PRIOR_CARDIOVASCULAR_HISTORY_AVAILABILITY.csv','CONSECUTIVE_SCREENING_AND_SELECTION_BIAS_AUDIT.md'],
'04_VALIDATION':['VALIDATION_PIPELINE_AUDIT.md','BOOTSTRAP_CI_METHOD_AUDIT.md','TEMPORAL_SENSITIVITY_ANALYSIS_AUDIT.md','CALIBRATION_PREDICTION_PROVENANCE.md','FIGURE5_CI_AVAILABILITY.csv'],
'05_MISSINGNESS':['FIBRINOGEN_MISSINGNESS_BY_OUTCOME.csv','FIBRINOGEN_FAIR_COMPARISON_AUDIT.md','CLINICAL_VARIABLE_MISSINGNESS.csv'],
'06_COMPARATORS':['TRADITIONAL_INDEX_PERFORMANCE_INVENTORY.csv','PIV_COMPARATOR_METHOD_AUDIT.md','CLINICAL_INCREMENTAL_PERFORMANCE_EXISTING_RESULTS.csv','COLLINEARITY_EXISTING_EVIDENCE_AUDIT.md','TROPONIN_FEASIBILITY_AUDIT.md'],
'07_ETHICS':['ETHICS_CONSENT_HARD_GATE.md','HUMAN_RESEARCH_GUIDELINES_REQUIREMENT.md'],
'08_REVISION_PLANNING':['WP2_ANALYSIS_AUTHORIZATION_PLAN.md','RESPONSE_TO_REVIEWERS_SKELETON.md','CONCLUSION_CLAIM_AUDIT.md']}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    check('Required files present',all((OUT/d/f).is_file() for d,files in required.items() for f in files))
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in {'QA_REPORT.json','PACKAGE_SHA256.csv'}]
    check('No unexpected binary/patient artifacts',all(p.suffix in {'.md','.csv','.py','.txt','.json','.log'} for p in files))
    for p in OUT.glob('09_CODE/*.py'):ast.parse(p.read_text())
    check('Python syntax',True)
    mat=pd.read_csv(OUT/'00_EXECUTIVE_SUMMARY/REVIEWER_COMMENT_MASTER_MATRIX.csv')
    check('22 unique comments',len(mat)==22 and mat.reviewer_id.nunique()==22)
    cls={'EXISTING_EVIDENCE_NO_RERUN','EXISTING_RESULT_NEEDS_REPORTING','SOURCE_DATA_AUDIT_REQUIRED','LIGHTWEIGHT_NEW_ANALYSIS_REQUIRED','SUBSTANTIAL_NEW_ANALYSIS_REQUIRED','AUTHOR_ETHICS_INPUT_REQUIRED','NOT_FEASIBLE_WITH_VALID_DATA','SCIENTIFICALLY_INAPPROPRIATE_REQUEST'}
    check('Feasibility enum',set(mat.feasibility_class)<=cls)
    metric=json.loads((OUT/'09_CODE/descriptive_metrics.json').read_text())
    check('Cohort and row reconciliation',metric['raw_rows']==2548 and metric['unique_patients']==2279 and metric['surplus_rows_removed']==269 and metric['final_primary_n']==1820 and metric['final_ami_n']==453)
    c=pd.read_csv(OUT/'05_MISSINGNESS/CLINICAL_VARIABLE_MISSINGNESS.csv')
    check('Age disagreement preserved without duplication',len(c)==15 and len(c[c.variable.eq('age')])==6)
    lin=pd.read_csv(OUT/'04_VALIDATION/FIGURE_SOURCE_LINEAGE_CHECK.csv')
    check('Figure source ancestry verified',len(lin)==3 and lin.submitted_calibration_equal.all())
    for row in pd.read_csv(OUT/'09_CODE/SOURCE_MANIFEST.csv').itertuples():
        p=Path.home()/'Downloads'/row.source.split('/')[-1] if row.source.startswith('LOCAL_DOWNLOADS/') else ROOT/row.source
        check('Source unchanged: '+row.source,sha(p)==row.sha256)
    check('Master hash unchanged',sha(MASTER)=='f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660')
    raw=pd.read_csv(MASTER,dtype=str,low_memory=False)
    protected=[c for c in raw if re.fullmatch(r'(patient_sn|.*inpatient_no_id|name|patient_name|phone|mobile|address|id_card)',c,re.I)]
    tokens=set()
    for c in protected:
        for v in raw[c].dropna().str.strip().unique():
            if len(v)>=6 and v.lower() not in {'unknown','missing','not available'}:
                tokens.add(v)
    # Name/ID exact value matches only; generic column names are allowed metadata.
    hay='\n'.join(p.read_text() for p in files)
    matches=[v for v in tokens if v in hay]
    check('No protected source identifier values of length>=6 found',not matches)
    check('No patient pseudonym rows',not re.search(r'AMI_P_[0-9a-f]{12}',hay))
    check('No credential tokens',not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',hay))
    for p in OUT.rglob('*.csv'):
        frame=pd.read_csv(p)
        check('Aggregate CSV: '+str(p.relative_to(OUT)),not {'patient_sn','research_patient_id','inpatient_no_id','diagnosis_text'}.intersection(frame.columns))
    result={'technical_package_qa':'PASS','scientific_gate':'WP1_HOLD_DUE_TO_SOURCE_DATA_GAP','checks':checks,'privacy_scope':'Exact source identifier values >=6 chars; pseudonym/credential scans; schema/allowlist checks. Does not claim universal deidentification proof. Manual review also required.','models_run':0,'new_figures':0,'manuscript_modified':False}
    (OUT/'09_CODE/QA_REPORT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='PACKAGE_SHA256.csv']
    pd.DataFrame([dict(path=str(p.relative_to(OUT)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(files)]).to_csv(OUT/'09_CODE/PACKAGE_SHA256.csv',index=False,lineterminator='\n')
    target=OUT.parent/(OUT.name+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,str(Path(OUT.name)/p.relative_to(OUT)))
    with zipfile.ZipFile(target) as z:check('ZIP integrity',z.testzip() is None)
    target.with_suffix('.zip.sha256').write_text(sha(target)+'  '+target.name+'\n')
    print(json.dumps(dict(status='PASS',checks=len(checks),zip=str(target),sha256=sha(target),size_bytes=target.stat().st_size)))


if __name__=='__main__':main()
