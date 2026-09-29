"""WP1 descriptive audit only. No model fitting or patient-level output."""
import ast
import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ['HITS_PROJECT_ROOT'])
SOURCE = Path(os.environ['HITS_MASTER_CSV'])
OUT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv(path, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False, lineterminator='\n')


def pure_functions(path, constants, functions, namespace):
    tree = ast.parse(path.read_text())
    nodes = []
    for n in tree.body:
        if isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id in constants for t in n.targets):
            nodes.append(n)
        elif isinstance(n, ast.FunctionDef) and n.name in functions:
            nodes.append(n)
    assert {n.name for n in nodes if isinstance(n, ast.FunctionDef)} == set(functions)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def delta_record(a, b, label, n, note):
    pair = a.notna() & b.notna()
    delta = (a[pair] - b[pair]).dt.total_seconds() / 86400
    same = a[pair].dt.normalize().eq(b[pair].dt.normalize())
    denom = len(delta)
    return dict(comparison=label, cohort_n=n, available_n=denom,
                median_days=delta.median(), q1_days=delta.quantile(.25), q3_days=delta.quantile(.75),
                before_timestamp_n=int(delta.lt(0).sum()), after_timestamp_n=int(delta.gt(0).sum()),
                same_timestamp_n=int(delta.eq(0).sum()), same_calendar_day_n=int(same.sum()),
                before_timestamp_pct=100*delta.lt(0).mean(), after_timestamp_pct=100*delta.gt(0).mean(),
                same_calendar_day_pct=100*same.mean(), semantic_caveat=note)


def main():
    expected = 'f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660'
    assert sha(SOURCE) == expected, 'Source hash mismatch; stop without changing frozen sources'
    v02 = ROOT / 'scripts/06_hits_ami_predevelopment_v0_2.py'
    v05 = ROOT / 'scripts/12_hits_v0_5_shift_robust_validation.py'
    ns = dict(pd=pd, np=np, re=re, hashlib=hashlib)
    constants = ['COL', 'BIOMARKERS', 'CORE', 'CORE_REQUIRED', 'MI_RE', 'ACUTE_RE', 'OLD_RE', 'UNCERTAIN_RE', 'NEGATED_MI_RE', 'CAD_RE', 'ANGINA_CAD_RE', 'ACS_RE']
    funcs = ['parse_numeric', 'parse_datetime', 'audit_id', 'normalize_text', 'binary_flag', 'sex_binary', 'split_diagnosis', 'acute_mi_pattern', 'classify_diagnosis', 'select_one_row_per_patient', 'build_patient_frame']
    pure_functions(v02, constants, funcs, ns)
    ns.update(B=182, SAFETY_DAYS=1)
    pure_functions(v05, [], ['assign_guard_groups', 'high_specificity_flag'], ns)
    raw = pd.read_csv(SOURCE, low_memory=False)
    selected, _ = ns['select_one_row_per_patient'](raw)
    d = ns['build_patient_frame'](selected)
    d = ns['assign_guard_groups'](d)
    d['highspec'] = ns['high_specificity_flag'](d)
    primary = d[d.primary_analysis].copy()
    chosen = selected.reset_index(drop=True).loc[d.primary_analysis].copy()
    assert len(primary) == 1820 and primary.y_primary.sum() == 453
    assert primary[ns['CORE']].notna().all().all()
    col = ns['COL']
    parse = ns['parse_datetime']
    counts = raw.groupby(col['patient'], dropna=False).size()
    metrics = {'raw_rows':len(raw), 'unique_patients':len(counts), 'patients_one_row':int(counts.eq(1).sum()),
               'patients_two_rows':int(counts.eq(2).sum()), 'patients_three_plus_rows':int(counts.ge(3).sum()),
               'patients_multiple_rows':int(counts.gt(1).sum()), 'surplus_rows_removed':int((counts-1).sum()),
               'identical_full_row_duplicates':int(raw.duplicated().sum()), 'missing_patient_identifier':int(raw[col['patient']].isna().sum()),
               'other_exclusions_before_selection':0, 'final_primary_n':len(primary), 'final_ami_n':int(primary.y_primary.sum()),
               'postselection_not_primary':int((~d.primary_analysis).sum()), 'FLOW_COUNTS_RECONCILE':'YES'}
    admissions=raw.assign(_admission=parse(raw[col['admission']])).groupby(col['patient'])['_admission'].nunique()
    metrics['patients_multiple_distinct_admission_dates']=int(admissions.gt(1).sum())
    metrics['patients_multiple_rows_but_one_distinct_admission_date']=int(((counts>1)&(admissions==1)).sum())
    metrics['patients_multiple_rows_no_admission_date']=int(((counts>1)&(admissions==0)).sum())
    metrics['postselection_phenotypes']=d.phenotype_class.value_counts().to_dict()
    metrics['primary_missing_age']=int(primary.age.isna().sum())
    metrics['age_manuscript_available_n']=1818
    metrics['age_manuscript_denominator_reproduced']=False
    metrics['primary_cbc_before_2019_n']=int(primary.cbc_year.lt(2019).sum())
    metrics['admission_linkage_not_validated']=True
    multi=raw[raw[col['patient']].isin(counts[counts.gt(1)].index)]
    metrics['multirow_patients_two_nonempty_diagnoses']=int(multi.groupby(col['patient'])[col['diagnosis']].count().eq(2).sum())
    metrics['multirow_patients_distinct_nonempty_diagnoses']=int(multi.groupby(col['patient'])[col['diagnosis']].nunique().gt(1).sum())
    metrics['multirow_patients_two_CBC_times']=int(multi.groupby(col['patient'])[col['wbc_time']].count().eq(2).sum())
    for field in ['inpatient_no_id','基线_inpatient_no_id']:
        if field in raw:
            metrics[field+'_multirow_distinct_token_patient_n']=int(multi.groupby(col['patient'])[field].nunique().gt(1).sum())
    metrics['cbc_year_min']=int(primary.cbc_year.min())
    metrics['cbc_year_max']=int(primary.cbc_year.max())
    metrics['admission_year_min']=int(primary.admission_datetime.dt.year.min())
    metrics['admission_year_max']=int(primary.admission_datetime.dt.year.max())
    flow = [dict(metric=k,value=v,interpretation='Rows are not proven distinct hospital encounters') for k,v in metrics.items() if not isinstance(v,dict)]
    csv('03_COHORT_FLOW/REPEATED_ADMISSION_FLOW_AUDIT.csv',flow)
    csv('03_COHORT_FLOW/RECORD_MULTIPLICITY.csv',[dict(rows_per_patient=int(k),patients=int(v),surplus_rows=int((k-1)*v)) for k,v in counts.value_counts().sort_index().items()])
    inventory=[]
    for c in raw:
        if re.search(r'date|time|日期|时间|admission|discharge|angiog|PCI|troponin|cTn|hs.?Tn|住院|造影|手术|history|既往|病史|ULN|reference|参考|platform|assay',c,re.I):
            v=chosen[c]
            row=dict(field=c,raw_nonmissing_n=int(raw[c].notna().sum()),primary_nonmissing_n=int(v.notna().sum()),primary_n=len(primary))
            if re.search(r'date|time|日期|时间',c,re.I):
                dt=parse(v)
                row.update(primary_parseable_n=int(dt.notna().sum()),earliest_year=dt.dt.year.min(),latest_year=dt.dt.year.max())
            inventory.append(row)
    csv('01_TIMING/CBC_TIMING_VARIABLE_INVENTORY.csv',inventory)
    csv('09_CODE/MASTER_FIELD_NAMES.csv',[dict(position=i+1,field=c) for i,c in enumerate(raw)])
    timing=[delta_record(primary.cbc_datetime,primary.admission_datetime,'CBC_minus_admission',len(primary),'Selected flat-row dates; index-encounter linkage unproven')]
    for v in ns['CORE']:
        timing.append(delta_record(primary[v+'_datetime'],primary.cbc_datetime,v+'_minus_WBC_time',len(primary),'Within selected flat row; not proof of specimen identity'))
    for c in chosen:
        if re.search(r'test_time',c) and re.search(r'cTn|troponin|CK.?MB',c,re.I):
            timing.append(delta_record(primary.cbc_datetime,parse(chosen[c]),'CBC_minus_'+c,len(primary),'Same selected row; assay/encounter linkage unproven'))
    csv('01_TIMING/CBC_TIMING_COVERAGE.csv',timing)
    csv('01_TIMING/FIBRINOGEN_TIMING_COVERAGE.csv',[
        delta_record(primary.fbg_datetime,primary.cbc_datetime,'Fbg_minus_CBC',len(primary),'Descriptive only; selected flat row'),
        delta_record(primary.fbg_datetime,primary.admission_datetime,'Fbg_minus_admission',len(primary),'Encounter linkage unproven')])
    miss=[]
    for group,sub in [('overall',primary),('AMI',primary[primary.y_primary.eq(1)]),('non_AMI',primary[primary.y_primary.eq(0)])]:
        for v in ['fbg','age','male','hypertension','diabetes']:
            n=len(sub); missing=int(sub[v].isna().sum())
            miss.append(dict(group=group,variable=v,n=n,available_n=n-missing,missing_n=missing,missing_pct=100*missing/n,provenance='Current descriptive parse; NOT a model rerun'))
    csv('05_MISSINGNESS/FIBRINOGEN_MISSINGNESS_BY_OUTCOME.csv',[x for x in miss if x['variable']=='fbg'])
    csv('05_MISSINGNESS/CLINICAL_VARIABLE_MISSINGNESS.csv',[x for x in miss if x['variable']!='fbg'])
    high=[]
    for group,sub in primary.groupby('guard_group'):
        high.append(dict(stage=group,primary_n=len(sub),primary_ami_n=int(sub.y_primary.sum()),highspecific_ami_n=int(sub.highspec.sum()),strict_control_n=int(sub.strict_control_candidate.sum()),highspecific_total_n=int(sub.highspec.sum()+sub.strict_control_candidate.sum())))
    csv('02_PHENOTYPE/SUPPLEMENTARY_HIGHSPEC_FLOW_SOURCE.csv',high)
    metrics['guardband']=high
    metrics['fibrinogen_complete_case_n']=int(primary.fbg.notna().sum())
    metrics['fibrinogen_complete_case_ami_n']=int(primary.loc[primary.fbg.notna(),'y_primary'].sum())
    metrics['fbg_timestamp_with_numeric_value_n']=int((primary.fbg_datetime.notna() & primary.fbg.notna()).sum())
    # Header audit plus aggregate availability; never output diagnoses or patient identifiers.
    trop=[]
    for c in chosen:
        if re.search(r'cTn|troponin|CK.?MB',c,re.I):
            row=dict(field=c,available_n=int(chosen[c].notna().sum()),missing_n=int(chosen[c].isna().sum()),cohort_n=len(primary))
            if re.search(r'_unit$',c):
                row['unit_counts']=json.dumps(chosen[c].value_counts().to_dict(),ensure_ascii=False)
            trop.append(row)
    csv('06_COMPARATORS/TROPONIN_FIELD_INVENTORY.csv',trop)
    dictionary=SOURCE.parent/'field_dictionary.csv'
    if dictionary.exists():
        dd=pd.read_csv(dictionary)
        keep=dd.clean_variable.str.contains(r'date|time|diagnos|history|PCI|CABG|cTn|vsn|qc_',case=False,na=False)
        csv('09_CODE/FIELD_DICTIONARY_SELECTED.csv',dd.loc[keep,['module','chinese_label','raw_variable','clean_variable','recommended_status','reason']])
    histories=[]
    for c in chosen:
        if re.search(r'PCI|CABG|CAD|history|既往|病史|冠脉|冠状动脉|梗死',c,re.I) and not re.search(r'lab_',c):
            histories.append(dict(field=c,field_exists='YES',coding='Raw source field; index-relative prior status not validated',available_n=int(chosen[c].notna().sum()),missing_n=int(chosen[c].isna().sum()),reliability='Temporal semantics unverified',usable='NO_AS_VERIFIED_PRIOR_HISTORY'))
    for concept in ['prior_CAD','previous_MI','prior_PCI_or_CABG']:
        histories.append(dict(field=concept,field_exists='NO_VALIDATED_DEDICATED_FIELD_RECOVERED',coding='Diagnosis mentions are not verified prior-history fields',reliability='UNKNOWN',usable='NO'))
    csv('03_COHORT_FLOW/PRIOR_CARDIOVASCULAR_HISTORY_AVAILABILITY.csv',histories)
    (OUT/'09_CODE/descriptive_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
    (OUT/'09_CODE/sessionInfo.json').write_text(json.dumps(dict(python=sys.version,pandas=pd.__version__,numpy=np.__version__,platform=platform.platform(),models_run=False,figures_created=False),indent=2)+'\n')
    csv('09_CODE/INPUT_HASHES.csv',[dict(source=label,sha256=sha(path)) for label,path in [('master_cohort_cleaned.csv',SOURCE),('scripts/06_hits_ami_predevelopment_v0_2.py',v02),('scripts/12_hits_v0_5_shift_robust_validation.py',v05)]])
    print(json.dumps(metrics,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
