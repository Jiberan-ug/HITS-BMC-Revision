# Figure style audit

Style references are the five standalone TIFFs in the recovered v1.0 upload package. The user confirmed the source manuscript; the portal-integrated figure binaries were not independently recovered.

| Figure | Style decision | Required content update | QA status |
|---|---|---|---|
| 1 | Portrait, centered flow chart; muted fills, thin gray arrows, rounded rectangles, and original hierarchy retained. | Adds source-record counts, one/two-record multiplicity, separate missing/ambiguous counts, final cohort counts. | PASS: visually reviewed against recovered original TIFF |
| 2 | Original square ROC composition with curve labels inside the plotting area and legend below. | Uses the frozen cross-validated ROC source. | PASS: visually reviewed against recovered original TIFF |
| 3 | Original square calibration plot with two lines, points, diagonal reference, and legend below. | Uses the frozen mean held-out prediction source. | PASS: visually reviewed against recovered original TIFF |
| 4 | Original horizontal A/B composition: date-axis flow at left and AUC forest plot at right. | Uses frozen allocation counts, exploratory wording, and available confidence intervals. | PASS: visually reviewed against recovered original TIFF |
| 5 | Original one-panel horizontal forest-plot layout and model color scheme retained. | Uses frozen sensitivity estimates and available 95% CIs. | PASS: visually reviewed against recovered original TIFF |
| S1-S4 | Supplementary DCA, high-specificity flow, correlation, and domain figures. | Rendered from included aggregate source CSVs. | PASS: visually reviewed |

No manual raster editing was used. Each figure has a source-data CSV and R script; shared helper code is included. All PDFs are vector exports; TIFF/PNG exports are 600 dpi.
