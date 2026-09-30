# Frozen temporal source conflict

This is a separate submission blocker from the age anchor. It does not authorize rerunning or regrouping the temporal analysis.

- Frozen V0.5 executable script SHA-256: `480f3fb66ddd50ce09e8fb85ddf8edbfed834ff5f1b5d00e254c3a6f8b17e53d`, matching the archived `source_hashes.csv` and `run_manifest.csv`.
- Its `assign_guard_groups` function sets `cut = pd.Timestamp("2015-01-01")`, assigns `shifted_CBC_date = cbc_datetime`, tests `cbc_datetime` for availability, and defines development/buffer/later groups against that date. See the immutable local script at `scripts/12_hits_v0_5_shift_robust_validation.py`, lines 263-281, and archived `03_guard_band_cohort_flow.csv`.
- The archived flow reports 1,001/196 AMI, 271/79 AMI, and 548/178 AMI for the three groups, with the 2015 date rule recorded. These numbers are not disputed as file contents; their *target-hospitalization/CAG* interpretation is disputed.
- WP3.2 `SOURCE_DATE_LINEAGE_RESOLUTION.md` says the temporal allocation used the deidentified 2020-2026 hospitalization/CAG axis, not the legacy WBC timestamp, and that the 2015 cutpoint was stale. No alternate executable allocation or per-patient target-date source was supplied. The user has separately confirmed that 2015 was old-draft residue and must not be used as a factual clinical cutpoint.

The two accounts cannot both describe the same archived V0.5 execution. A document-level assertion or deletion of the cutpoint cannot resolve the executable provenance conflict. The historical script's use of 2015 is evidence of what it computed, **not** evidence that 2015 is the true target episode date. The currently submitted interpretation of temporal robustness must remain on HOLD until the source owner provides the actual target-date source/allocation evidence or the authors transparently revise the claim under a separately authorized analysis plan.
