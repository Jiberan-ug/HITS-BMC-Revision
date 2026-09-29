# Bootstrap uncertainty
Source `HITS_V0.3.1_verified_completion_20260825/scripts/01_run_hits_v0_3_1_verified_completion.py` bootstrap_auc_ci527-538, paired_delta577-615; archived numbered source.

Metric and delta confidence intervals:1000 resamples of PATIENT rows from FIXED patient-averaged repeated OOF probabilities. Ordinary bootstrap with replacement; paired comparisons merge patient key and outcome1:1 and resample common rows together. Percentile2.5/97.5 intervals; single-class samples skipped and valid count saved. Model refit NO; fold regeneration NO; prediction regeneration NO. These intervals reflect resampling of the fixed evaluated patient-prediction pairs and do not incorporate full model-building or shared-training-dependence uncertainty. They must not be described as1000 complete nested pipeline repeats.

A SEPARATE300-replicate full-development bootstrap re-fits/tunes models for optimism/stability. It is not the1000-resample metric CI and not an external validation. Temporal fixed-validation paired bootstrap uses2000 resamples in V05/V051. Keep all three procedures distinct.
