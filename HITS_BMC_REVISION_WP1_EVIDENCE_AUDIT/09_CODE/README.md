# Reproduction and privacy
Python3 with pandas/numpy; no model fitting/plotting dependencies used by audit_sources.py. Set HITS_PROJECT_ROOT and HITS_MASTER_CSV to protected local paths, optionally HITS_CURRENT_DOCX. Run audit_sources.py then build_reports.py. The expected master SHA256 is enforced. Frozen source scripts are loaded via an AST allowlist of pure parsing/selection functions; no main/model/plot code is executed. Metadata/aggregate files alone are written.

The source_excerpts directory is redacted, numbered READ-ONLY code evidence, NOT runnable model instructions. It includes historical Python plotting functions only as archival evidence; WP1 does not execute them and future plotting remains R-only. The source functions/dictionary contain field NAMES but no patient values. Canonical aggregates are copied, never re-estimated.

The age-discrepancy CSV deliberately distinguishes CURRENT_CODE_DESCRIPTIVE from AUTHOR_CORRECTED_DEFINITION_REQUIRED. Do not collapse them. Figure-source filenames changed across manuscript stages; follow content ancestry, not the figure number alone.

No credentials, patient identifiers, admission tokens, individual diagnoses, patient predictions, full manuscripts or ethics documents belong in this public package. Source owner must independently retain protected records. No third-party worker received patient data.
