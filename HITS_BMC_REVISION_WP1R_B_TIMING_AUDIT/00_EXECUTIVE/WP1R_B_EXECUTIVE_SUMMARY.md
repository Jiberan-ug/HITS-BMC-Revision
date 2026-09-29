# WP1R-B Executive Summary

Audit date: 2026-09-29.

Scope: local-only recovery of CBC/fibrinogen timing and historical measurement-selection rule for the frozen HITS cohort. No model, phenotype, manuscript, or response letter was changed.

## Result

**Final gate: `WP1R_B_PASS_SELECTION_RULE_ONLY`.** The frozen record-selection rule is recoverable exactly from the historical executable script. A defensible link from any selected CBC or fibrinogen result to an eligible index coronary-angiography hospitalization was not recovered. This is an evidence-limited result, not proof that every laboratory result came from a clinically unrelated episode.

The primary analysis cohort was reproduced through the historical selector and phenotype builder: **N=1,820; definite AMI=453; definite non-AMI CAD=1,367**. The cohort-size guard passed exactly. The result is a timing audit only; `main()` and all modeling code were not run.

## Direct Answers

| Question | Finding |
|---|---|
| Total / AMI / non-AMI CAD | 1,820 / 453 / 1,367 |
| Any defensible index-episode timing | 0/1,820; 0% |
| Direct encounter linkage | 0/1,820 |
| Unique stay-window linkage | 0/1,820 |
| Partial clinical timing linkage | 0/1,820 |
| Same-index-hospitalization CBC confirmed | 0; 1,820 remain UNKNOWN. Interpretable denominator=0. |
| CBC before angiography | 0/0 interpretable CBC–angiography pairs; not estimable. |
| CBC before initial AMI diagnosis | 0/0 AMI patients with a valid initial-diagnosis timestamp; not estimable. |
| Timing unverified | 1,820/1,820 (100%) |
| CBC timestamps present in selected rows | 1,820/1,820 (100%), but not episode-linked |
| Listed admission date paired with CBC timestamp | 130/1,820 (7.14%); date comparison only |
| Fibrinogen timestamp / value | 1,707/1,820 (93.79%) / 1,705/1,820 (93.68%) |
| Fibrinogen and CBC timestamps paired | 1,707/1,820 (93.79%); lab-to-lab timing only |
| Fibrinogen same index hospitalization | 0 confirmed; all 1,707 timed values remain UNKNOWN as to index stay |
| Study period | `AUTHOR_CONFIRMED_BUT_NOT_MACHINE_VERIFIED` |
| Temporal validation | `REMOVE_FROM_MANUSCRIPT` as temporal-transportability evidence; preserve frozen numerical artifacts unchanged |
| Ethics gate | `PASS`, based on author confirmation of approval K202602-10 and waiver; documents were not independently inspected |

The AMI and non-AMI groups have similar *field availability*: CBC timestamp 100% in both; fibrinogen timestamp 94.26% vs 93.64% (0.62 percentage-point difference); CBC/admission-date pairs 7.28% vs 7.10% (0.18-point difference). Those dates are not clinically linked to the index event. There is no differential availability of defensible episode timing: zero in both groups.

Fibrinogen versus CBC: 1,553/1,707 (90.98%) share a calendar date; by calendar-day order, fibrinogen was on an earlier date in 41, the same date in 1,553, and a later date in 113. By exact recorded timestamps, 727 were earlier, 1 exactly equal, and 979 later. These are laboratory-to-laboratory relationships in the selected flat row, not same-encounter confirmation.

## Ethics Record

`ETHICS_GATE = PASS`, based on the author's explicit confirmation of Ethics Committee of Xinjiang Medical University approval K202602-10 and an Ethics Committee-approved waiver of informed consent. The approval documents were not independently inspected or uploaded. Future author-confirmed wording is: “The study was approved by the Ethics Committee of Xinjiang Medical University (approval no. K202602-10). Given the retrospective nature of the study, the requirement for informed consent was waived by the Ethics Committee. All methods were performed in accordance with relevant guidelines and regulations.” Consent for publication: not applicable. This wording was not inserted into the manuscript in WP1R-B.

## Interpretation

The source has patient-linked CBC timestamps but no explicit encounter ID, discharge date, CAG/angiography date, PCI/procedure date, or initial AMI diagnosis date/time. A sparse `admission_date` exists, and two inpatient-number/token columns exist, but neither binds the selected laboratory measurement to the eligible index CAG episode. A separate deidentified `visit_id_hash_list` is an aggregate of inpatient-number tokens per patient, not a per-laboratory visit key. Temporal proximity, even on the same calendar day, was not used as proof of encounter identity.

The exact historical row selection is completeness-ranked, not chronological: non-empty discharge diagnosis, number of nonmissing core absolute counts, WBC timestamp availability, `qc_nonmissing_count`, then original source-row order. It does **not** select the first/earliest CBC, first admission, pre-diagnosis sample, or pre-angiography sample. The upstream definition of `qc_nonmissing_count` remains unrecovered.

## Next Boundary

Editor Comment 1 and Reviewer 1 timing concerns can now be answered with these facts and limitations; the fact-pattern files are not polished response prose. The temporal analysis should not be presented as temporal validation. Do not enter WP2 or alter the frozen model/manuscript until the user/GPT reviews this WP1R-B handoff.

## Reproduction and Privacy

`09_CODE/wp1r_b_timing_audit.py` loads only the historical selector/phenotype functions from the script AST and emits aggregate results. Patient identifiers, pseudonyms, row-level dates, row-level flags, model predictions, and raw sources are not included. See `09_CODE/SOURCE_HASHES.csv`, `09_CODE/run.log`, and the exact source inventory.
