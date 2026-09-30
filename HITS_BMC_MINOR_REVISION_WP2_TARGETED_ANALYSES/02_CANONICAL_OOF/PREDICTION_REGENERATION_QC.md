# Prediction Regeneration QC

Canonical out-of-fold predictions were regenerated using the locked V0.3.1 code and 5×10 split design. There is one held-out prediction per eligible patient in each repeat, followed by arithmetic-mean aggregation across 10 repeats. The aggregate QC table records per-model patient counts, repeat/fold counts, missing predictions, and probability ranges.

Two patient-level CSVs were saved outside the repository under a mode-0700 directory, with files chmod 0600. They contain pseudonymous patient tokens, phenotype labels, repeat/fold assignment, and OOF predictions; they are excluded from Git, ZIP, and the public package. This report intentionally omits their local path and hashes.
