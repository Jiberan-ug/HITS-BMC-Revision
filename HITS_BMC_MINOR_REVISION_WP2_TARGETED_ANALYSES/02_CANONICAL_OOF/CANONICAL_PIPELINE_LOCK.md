# Canonical Pipeline Lock

This is targeted reproduction, not model redevelopment. The executed source cohort SHA-256 is `f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660`; the exact V0.2 cohort/phenotype script SHA-256 is `089924ec5a58d09c3e96bdedd2a9316690eebd3f70377a058760a90b267ad91a`; the V0.3.1 canonical fitting script SHA-256 is `b1dcc686e2399c07c8125c373a16264dafbc7adf4b6703c809e4765fd7cf5922`; the V0.5.2 canonical result registry SHA-256 is `a3e2e6b4da20683fdd99d380e0027855b8d7da10cb29e39f4234ee3c9547536a`.

Frozen settings: outcome and row-selection logic from V0.2; Core-7 and Enhanced predictor sets unchanged; outer 5-fold × 10 repeats, stratified; inner 5-fold; seed 20260825; elastic-net C grid (0.1, 1.0, 10.0); l1 ratio grid (0.25, 0.5, 0.75); no grid expansion; no new algorithm or feature selection. Transformations, imputation, scaling, and tuning remain inside the relevant training folds.

The model blocks are the original canonical analysis IDs: `primary_core`, `primary_enhanced_imputed`, `primary_fbg_complete_case`, and `primary_clinical`. A separate, explicitly labeled `primary_clinical_fbg_complete_case` block evaluates the four clinical models on one shared fibrinogen-complete sample for paired reviewer comparisons and DCA. The full-cohort Enhanced block reproduces the exact historical fold-local median method to reconcile its frozen result; the 1705-person complete-case block performs no fibrinogen imputation.

Each patient has one held-out prediction in each outer repeat. The canonical patient-level prediction is the arithmetic mean across the 10 held-out probabilities. Patient-level data are saved only outside this repository with restrictive filesystem permissions. Public artifacts contain aggregate results only.
