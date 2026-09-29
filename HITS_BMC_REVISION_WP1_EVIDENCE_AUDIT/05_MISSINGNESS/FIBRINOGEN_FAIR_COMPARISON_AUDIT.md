# Fibrinogen comparison
Primary available1705/1820; AMI426/453 (27 missing,5.9603%); non-AMI1279/1367 (88 missing,6.4375%). Similar observed proportions do not establish MCAR/MAR or exclude outcome-specific selection.

Code `HITS_V0.3.1_verified_completion_20260825/scripts/01_run_hits_v0_3_1_verified_completion.py` builds primary_fbg_cc ONCE requiring all Enhanced features; Core and Enhanced evaluated in one run_nested_oof call on the same1705 patients,426 events, same outer partitions. Paired bootstrap merge uses the same patient keys/outcome. This supports same-person/same-fold/paired comparison in code. Canonical existing Core AUC0.727061 and Enhanced0.736739; delta0.009678 with95% CI0.002300 to0.016932. No rerun. Strict CC1418 patients also exists. Main Enhanced1820 uses fold-specific median imputation, not complete-case deletion.

No dedicated missingness model or inferential missingness test run in WP1. Timing and lineage caveats remain independent of comparison fairness.
