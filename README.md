# HITS / BMC Cardiovascular Disorders: Revision Evidence Audit

This public repository contains a bounded **WP1 evidence-recovery and feasibility audit**, not a new model release or a submission-ready revision. Public publication of aggregate audit materials was explicitly authorized by the project owner on 2026-09-29.

## Current Review

**Latest source-recovery gate: `WP1R_SOURCE_RECOVERY_PARTIAL_PASS_INDEX_CBC_RECONSTRUCTION_REQUIRED`.** The original WP1 package remains historical; WP1R supersedes its source-date and ethics statements where noted below. The broader manuscript-revision readiness remains on hold.

[Open the WP1R final decision](https://github.com/Jiberan-ug/HITS-BMC-Revision/blob/revision/bmc-major-revision-wp1-evidence-audit/HITS_BMC_REVISION_WP1_EVIDENCE_AUDIT/10_ORIGINAL_SOURCE_RECOVERY/WP1R_DECISION.md)

[Browse the WP1R source-recovery evidence](https://github.com/Jiberan-ug/HITS-BMC-Revision/tree/revision/bmc-major-revision-wp1-evidence-audit/HITS_BMC_REVISION_WP1_EVIDENCE_AUDIT/10_ORIGINAL_SOURCE_RECOVERY)

[Open the WP1 executive summary and 34 direct answers](https://github.com/Jiberan-ug/HITS-BMC-Revision/blob/revision/bmc-major-revision-wp1-evidence-audit/HITS_BMC_REVISION_WP1_EVIDENCE_AUDIT/00_EXECUTIVE_SUMMARY/WP1_EXECUTIVE_SUMMARY.md)

[Browse the complete audit branch](https://github.com/Jiberan-ug/HITS-BMC-Revision/tree/revision/bmc-major-revision-wp1-evidence-audit)

The dedicated revision pull request remains OPEN for review. The main branch is an administrative index; audit evidence is on the revision branch. Do not interpret an open review package or technical QA PASS as scientific approval.

## Main Findings

1. WP1R recovered the primary 2,548-row/431-column mother file and matched its 2,279-patient key set exactly to the analysis master; three of the four named source files were found. The author confirms the 2020–2026 coronary-angiography eligibility rule, but no query/date field machine-verifies it.
2. The source row grain and encounter linkage remain unresolved. CBC test times cannot be classified as index-admission versus historical values, and same-hospitalization index CBC reconstruction is not feasible from the recovered files. Frozen temporal results therefore are not credible as temporal-transportability evidence until date lineage is verified.
3. The ethics gate is PASS based on the author's explicit confirmation of approval K202602-10 and waiver of informed consent; the existing manuscript statement that all participants provided consent conflicts and requires correction. Approval documents were not independently inspected or published.
4. The recovered calibration/ROC figure branch uses legacy 20-repeat predictions, while the canonical Table 2 comes from a different verified 10-repeat validation run. Corrected age provenance remains unresolved; canonical patient-level predictions were not persisted and cannot be replaced by legacy predictions for new DCA.

The audit preserves all frozen model values. It does not edit the manuscript, refit Core-7/Enhanced, create new DCA/calibration/collinearity analyses, generate figures, authorize WP2, or claim the data are irretrievably unusable. No patient-level raw data or protected ethics documents are included.

## Review Instructions

Review the executive summary, 22-comment reviewer matrix, risk register, numbered source excerpts, and source hashes. Prioritize source-date lineage, record-selection semantics, canonical-versus-legacy prediction ancestry, corrected age derivation, and documentary ethics evidence. Provide a source-specific clearance plan before authorizing targeted analyses. Reviewer-comment summaries come from the adopted WP1 instruction; the complete original decision letter and exact portal-submitted manuscript snapshot were not independently recovered.

## Privacy and Reproducibility

Only aggregate tables, code, short relevant manuscript excerpts, and reproducibility metadata are included. No patient-level raw data, identifiers, diagnoses, admission tokens, individual predictions, credentials, complete manuscript, or private ethics documents are published. The ZIP has the same safe audit scope. Local source owners can reproduce the descriptive audit using protected inputs and the supplied scripts; public readers cannot reconstruct patient-level data from this repository.

Future scientific figures must use R, independent source-data CSVs and reproducible scripts, with values loaded from the canonical registry. Existing historical plotting code is retained only as read-only evidence, not as permission to rerun it.
