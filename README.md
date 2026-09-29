# HITS / BMC Cardiovascular Disorders: Revision Evidence Audit

This public repository contains a bounded **WP1 evidence-recovery and feasibility audit**, not a new model release or a submission-ready revision. Public publication of aggregate audit materials was explicitly authorized by the project owner on 2026-09-29.

## Current Review

**Scientific gate: `WP1_HOLD_DUE_TO_SOURCE_DATA_GAP`.**

[Open the WP1 executive summary and 34 direct answers](https://github.com/Jiberan-ug/HITS-BMC-Revision/blob/revision/bmc-major-revision-wp1-evidence-audit/HITS_BMC_REVISION_WP1_EVIDENCE_AUDIT/00_EXECUTIVE_SUMMARY/WP1_EXECUTIVE_SUMMARY.md)

[Browse the complete audit branch](https://github.com/Jiberan-ug/HITS-BMC-Revision/tree/revision/bmc-major-revision-wp1-evidence-audit)

The dedicated revision pull request remains OPEN for review. The main branch is an administrative index; audit evidence is on the revision branch. Do not interpret an open review package or technical QA PASS as scientific approval.

## Main Findings

1. The frozen 1,820-patient cohort and 453 AMI labels can be reconstructed descriptively, but the model-input CBC dates and stated recruitment period have unresolved provenance conflicts.
2. The recovered calibration/ROC figure branch uses legacy 20-repeat predictions, while the canonical Table 2 comes from a different verified 10-repeat validation run.
3. Corrected age provenance and ethics/consent documentation require source-owner confirmation. Canonical patient-level predictions were not persisted and cannot be replaced by legacy predictions for new DCA.

The audit preserves all frozen model values. It does not edit the manuscript, refit Core-7/Enhanced, create new DCA/calibration/collinearity analyses, generate figures, authorize WP2, or claim the data are irretrievably unusable.

## Review Instructions

Review the executive summary, 22-comment reviewer matrix, risk register, numbered source excerpts, and source hashes. Prioritize source-date lineage, record-selection semantics, canonical-versus-legacy prediction ancestry, corrected age derivation, and documentary ethics evidence. Provide a source-specific clearance plan before authorizing targeted analyses. Reviewer-comment summaries come from the adopted WP1 instruction; the complete original decision letter and exact portal-submitted manuscript snapshot were not independently recovered.

## Privacy and Reproducibility

Only aggregate tables, code, short relevant manuscript excerpts, and reproducibility metadata are included. No patient-level raw data, identifiers, diagnoses, admission tokens, individual predictions, credentials, complete manuscript, or private ethics documents are published. The ZIP has the same safe audit scope. Local source owners can reproduce the descriptive audit using protected inputs and the supplied scripts; public readers cannot reconstruct patient-level data from this repository.

Future scientific figures must use R, independent source-data CSVs and reproducible scripts, with values loaded from the canonical registry. Existing historical plotting code is retained only as read-only evidence, not as permission to rerun it.
