# WP1R-B Gate

## Final Gate

**`WP1R_B_PASS_SELECTION_RULE_ONLY`**

## Basis

- Frozen primary cohort reproduced exactly: N=1,820, including 453 definite AMI and 1,367 definite non-AMI CAD.
- Historical record-selection algorithm is verified from its executable implementation.
- No direct CBC/fibrinogen-to-index-encounter key, complete admission/discharge window, CAG/PCI/procedure time, or initial AMI diagnosis time was recovered.
- An admission-date field and inpatient-number/token fields exist, but they do not bind the selected test to an index episode.
- The local source search covered the original mother file, Scheme C source ZIP and member list, field dictionary, deidentified derivatives, information-score encounter/timing audits, Article-5 source/audit folders, and relevant Downloads/TwoPapers extraction folders. No obvious same-source clinical encounter/procedure export remains unexamined in those relevant roots.
- The historical selection rule is fully established. Absence of encounter linkage is not evidence that all measurements are incompatible with the phenotype, so `FAIL_TIMING_PROVEN_INCOMPATIBLE` is not warranted.

## Locked Counts

| Measure | Count |
|---|---:|
| Any defensible index-episode timing | 0/1,820 |
| Direct encounter linkage | 0/1,820 |
| Unique stay-window linkage | 0/1,820 |
| Partial clinical timing linkage | 0/1,820 |
| Timing unverified | 1,820/1,820 |
| CBC same index hospitalization confirmed | 0; 1,820 UNKNOWN |
| CBC before angiography | 0/0 interpretable pairs; not estimable |
| CBC before initial AMI diagnosis | 0/0 AMI patients with valid diagnosis time; not estimable |
| Fibrinogen same index hospitalization confirmed | 0; 1,707 timed results UNKNOWN |

## Authorization Boundary

This gate authorizes only the local timing/source audit package and its handoff. It does not authorize model refitting, result regeneration, response-letter drafting, manuscript editing, deletion of frozen temporal artifacts, or WP2. The temporal analysis decision is `REMOVE_FROM_MANUSCRIPT` as clinical temporal-transportability evidence; frozen numerical outputs remain unchanged.

Ethics is recorded as `PASS` only because the author explicitly confirmed approval K202602-10 and the Ethics Committee-approved waiver of consent. No ethics documents were requested, inspected, or published in this WP.

Future author-confirmed ethics wording (not inserted into the manuscript here): “The study was approved by the Ethics Committee of Xinjiang Medical University (approval no. K202602-10). Given the retrospective nature of the study, the requirement for informed consent was waived by the Ethics Committee. All methods were performed in accordance with relevant guidelines and regulations.” Consent for publication: not applicable. The current manuscript's contrary statement that all participants provided informed consent must be corrected only in a separately authorized manuscript stage.
