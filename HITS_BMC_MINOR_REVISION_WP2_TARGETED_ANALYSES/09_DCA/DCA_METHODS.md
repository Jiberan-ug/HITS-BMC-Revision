# Decision-Curve Analysis Methods

The reviewer-facing DCA uses only canonical 5-fold × 10-repeat patient-level mean OOF probabilities from the fibrinogen-complete primary sample (N=1705, AMI=426). Clinical-only, Clinical+PIV, Clinical+Core-7, and Clinical+Enhanced predictions are matched to the same patients and validation partitions; no fibrinogen values are missing in this sample. The full-cohort Enhanced historical reproduction is not mixed into this paired DCA.

Net benefit is calculated as TP/N − FP/N × pt/(1−pt). Thresholds are prespecified at 0.05–0.50 in 0.01 increments, matching the historical exploratory range; no threshold is optimized. Treat-all and treat-none are included. This retrospective phenotype-discrimination DCA is exploratory and does not establish clinical utility or treatment benefit.

Uncertainty is not represented as full model-development uncertainty. The input predictions are fixed mean OOF probabilities; the DCA is descriptive.
