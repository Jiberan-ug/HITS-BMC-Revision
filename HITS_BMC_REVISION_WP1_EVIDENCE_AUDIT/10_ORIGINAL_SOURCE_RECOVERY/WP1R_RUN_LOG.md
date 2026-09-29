# WP1R-A Run Log

- Run date: 2026-09-29 (local, Asia/Shanghai).
- Input scope: four named original-file candidates in local Downloads and the historical `Dual_Score_V0.3/source_raw` folder; cleaned analysis master used only for aggregate source-lineage comparison.
- Operation: read-only SHA-256, file/header/shape counts, patient-key set equality in memory, selected mapped-field value/time exact-match counts, repeated-row identifier/date audit, and date-field inventory.
- Outcome: primary source structure/counts and key-set equality reproduced; 3/4 unique source-file types found; 269 repeated patient pairs did not evidence distinct second admissions; encounter/index-CBC semantics remain unresolved.
- Privacy: no source row, patient key, admission token, or ethics attachment was written to the package. Only aggregate counts, source hashes, and field names were retained.
- Package QA: 81 checks passed, including source immutability, count reconciliation, identifier scanning against both the cleaned master and primary original mother file, required-output checks, and ZIP integrity.
- Models run: 0. Manuscript modified: no. WP2 entered: no.
