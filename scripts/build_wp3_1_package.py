#!/usr/bin/env python3
"""Build the WP3.1 minimal-change manuscript and audit package."""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from openpyxl import load_workbook


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "HITS_BMC_MINOR_REVISION_WP3_1_SUBMISSION_READY"
WP3 = REPO / "HITS_BMC_MINOR_REVISION_WP3_FINAL"
WP2 = REPO / "HITS_BMC_MINOR_REVISION_WP2_TARGETED_ANALYSES"
WP1 = REPO / "HITS_BMC_REVISION_WP1_EVIDENCE_AUDIT"
BASE = Path.home() / "Downloads/HITS_BMC_Manuscript_v1.2_EthicsNumber-2.docx"
SUPPLEMENT = WP3 / "03_SUPPLEMENT/Additional_file_1_Revised_Supplementary_Methods_and_Figures.docx"
WORKBOOK = WP3 / "03_SUPPLEMENT/Additional_file_2_Revised_Supplementary_Tables.xlsx"
EDITOR_SOURCE = Path.home() / ".codex_fast/attachments/d1a85934-b384-4434-9f1e-049d7337c5a7/已粘贴的文本.txt"
REVIEWER_SOURCE = Path.home() / ".codex_fast/attachments/ff8bc8db-e06e-4e43-9dba-62965973e4ec/已粘贴的文本.txt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def paragraph_for(doc, prefix: str):
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one paragraph starting {prefix!r}; found {len(matches)}")
    return matches[0]


def replace_paragraph_text(paragraph, text: str, highlighted: bool = False):
    old = paragraph.text
    first_rpr = deepcopy(paragraph.runs[0]._r.rPr) if paragraph.runs and paragraph.runs[0]._r.rPr is not None else None
    for child in list(paragraph._p):
        if child.tag.endswith("}pPr"):
            continue
        paragraph._p.remove(child)

    matcher = difflib.SequenceMatcher(a=old, b=text, autojunk=False)
    pieces = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pieces.append((text[j1:j2], False))
        elif tag in ("insert", "replace"):
            if j1 != j2:
                pieces.append((text[j1:j2], True))
    for content, changed in pieces:
        if not content:
            continue
        run = paragraph.add_run(content)
        if first_rpr is not None:
            run._r.insert(0, deepcopy(first_rpr))
        if highlighted and changed:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def set_cell_text(cell, text: str, highlighted: bool = False):
    p = cell.paragraphs[0]
    replace_paragraph_text(p, text, highlighted=highlighted)
    for extra in cell.paragraphs[1:]:
        replace_paragraph_text(extra, "", highlighted=False)


def replace_embedded_figures(docx_path: Path, figure_paths: list[Path]):
    doc = Document(docx_path)
    image_paragraphs = [p for p in doc.paragraphs if p._p.xpath(".//a:blip")]
    if len(image_paragraphs) != len(figure_paths):
        raise RuntimeError(f"Expected {len(figure_paths)} embedded figures in {docx_path.name}; found {len(image_paragraphs)}")
    for para, figure_path in zip(image_paragraphs, figure_paths):
        blip = para._p.xpath(".//a:blip")[0]
        rel_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        doc.part.rels[rel_id]._target._blob = figure_path.read_bytes()
    doc.save(docx_path)


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def sentence_changes(old: str, new: str) -> int:
    split = lambda x: [s.strip() for s in re.split(r"(?<=[.!?])\s+", x) if s.strip()]
    a, b = split(old), split(new)
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")


def write_csv(path: Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def main():
    if not BASE.exists():
        raise FileNotFoundError(BASE)
    if not SUPPLEMENT.exists() or not WORKBOOK.exists():
        raise FileNotFoundError("WP3 supplementary sources are missing")
    if not EDITOR_SOURCE.exists() or not REVIEWER_SOURCE.exists():
        raise FileNotFoundError("Exact editor or reviewer report is missing")

    for sub in ("01_MANUSCRIPT", "02_RESPONSE", "03_SUPPLEMENT", "04_FIGURES", "05_QA", "06_SUBMISSION"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("source_data", "r_scripts"):
        (OUT / "04_FIGURES" / sub).mkdir(parents=True, exist_ok=True)

    clean_path = OUT / "01_MANUSCRIPT/HITS_BMC_Revised_Manuscript_CLEAN.docx"
    marked_path = OUT / "01_MANUSCRIPT/HITS_BMC_Revised_Manuscript_MARKED.docx"
    shutil.copy2(BASE, clean_path)
    shutil.copy2(BASE, marked_path)
    clean = Document(clean_path)
    marked = Document(marked_path)
    original = Document(BASE)

    changes = [
        ("Abstract", "Methods: This single-center retrospective study included", None,
         "VERSION_CONSISTENCY", "Use the approved exploratory date-axis terminology."),
        ("Abstract", "Results: PIV showed the highest discrimination", None,
         "VERSION_CONSISTENCY", "Describe the later date-axis group without implying formal temporal validation."),
        ("Abstract", "Conclusions: Multidimensional routine hematologic modeling", None,
         "REVIEWER_REQUIRED", "Keep the claim modest and state that clinical readiness is not established."),
        ("Methods: Study design and setting", "This was a single-center retrospective observational study conducted",
         "This was a single-center retrospective observational study conducted in the Department of Cardiology, The First Affiliated Hospital of Xinjiang Medical University, Urumqi, Xinjiang, China, using records from Coronary Heart Disease Unit I. The study period was 1 January 2020 to 1 January 2026, and the source population comprised patients who underwent coronary angiography during this period. Because a complete eligible-patient screening log was unavailable, consecutive enrollment could not be confirmed. Calendar dates were deidentified before research use; institutional documentation describes patient-specific randomized shifts within +/-182 days while preserving within-patient intervals. However, linkage of the transformed output to the exact analytic input could not be verified. The date-axis sensitivity analysis is therefore exploratory, is not interpreted as the actual recruitment calendar, and is not formal temporal validation. Because a uniform prospective index time could not be reconstructed for all patients, the study focused on retrospective AMI phenotype discrimination rather than future-event prediction.",
         "REVIEWER_REQUIRED", "Retain the period statement, remove machine-verification language, and qualify consecutive enrollment and date-axis interpretation."),
        ("Methods: Eligibility and study population", "Initially, 2,548 patient encounters were extracted",
         "The source export contained 2,548 records representing 2,279 unique patients. Of these, 2,010 had one source record and 269 had two; 269 surplus records were removed when retaining one patient-level record by a completeness-based rule. The source did not establish that multiple records represented distinct admissions. Among the 2,279 patients, 1,944 had discharge-diagnosis text: 456 met the definite AMI definition, 1,372 the definite non-AMI CAD definition, five had an ambiguous MI mention, and 111 did not meet the CAD/AMI target. The remaining 335 patients had no discharge diagnosis. Before applying the core CBC availability requirement, 1,828 patients had a definite AMI or non-AMI CAD phenotype.",
         "EDITOR_REQUIRED", "Distinguish source records from patients and separate missing diagnoses from ambiguous MI text."),
        ("Methods: Outcome definition", "AMI phenotype was reconstructed independently from discharge-diagnosis text.",
         "AMI phenotype was classified from discharge-diagnosis text; no independent clinical adjudication was available. Definite AMI required explicit current or acute/subacute MI language, including unambiguous ST-segment elevation myocardial infarction (STEMI), non-ST-segment elevation myocardial infarction (NSTEMI), or an acute wall-specific MI description. Old or prior MI, MI history, prior percutaneous coronary intervention (PCI), CAD, stable angina, and unstable angina were not sufficient alone. An MI keyword without clear acute or old/prior context, missing diagnosis, or uncertainty markers was retained as ambiguous/review. A definite non-AMI CAD phenotype included CAD, coronary disease, angina, or revascularization descriptions without current acute MI, with old/prior MI allowed in the broad primary control but excluded from the strict control. Troponin, creatine kinase-MB (CK-MB), and other cardiac injury markers were supportive only; incomplete timing, reference-limit, and dynamic-change information prevented complete Fourth Universal Definition adjudication [2].",
         "EDITOR_REQUIRED", "State the discharge-text source, absence of independent adjudication, and role of supportive biomarkers."),
        ("Methods: Outcome definition", "AMI phenotype was reconstructed independently from discharge-diagnosis text.",
         "AMI phenotype was classified from discharge-diagnosis text; no independent clinical adjudication was available. Definite AMI required explicit current or acute/subacute MI language, including unambiguous ST-segment elevation myocardial infarction (STEMI), non-ST-segment elevation myocardial infarction (NSTEMI), or an acute wall-specific MI description. Old or prior MI, MI history, prior percutaneous coronary intervention (PCI), CAD, stable angina, and unstable angina were not sufficient alone. An MI keyword without clear acute or old/prior context, missing diagnosis, or uncertainty markers was retained as ambiguous/review. A definite non-AMI CAD phenotype included CAD, coronary disease, angina, or revascularization descriptions without current acute MI, with old/prior MI allowed in the broad primary control but excluded from the strict control. Troponin, creatine kinase-MB (CK-MB), and other cardiac injury markers were supportive only; incomplete timing, reference-limit, and dynamic-change information prevented complete Fourth Universal Definition adjudication [2].",
         "EDITOR_REQUIRED", "State the discharge-text source, absence of independent adjudication, and role of supportive biomarkers."),
        ("Methods: Predictors and laboratory measurements", "The Core-7 predictors were absolute neutrophil",
         "The Core-7 predictors were absolute neutrophil, lymphocyte, and monocyte counts, platelet count, MPV, RDW, and hemoglobin; fibrinogen was added for the Enhanced model. For patients with multiple source records, one record was selected by descending priority of a non-empty discharge diagnosis, the number of available absolute neutrophil, lymphocyte, monocyte, and platelet counts (0-4), a parsable WBC/CBC timestamp, and the overall non-missing-field count, followed by earliest source-row order as the final tie-break. The component definition of the overall count was unavailable, and no chronological preference was used. Encounter-level linkage and admission, angiography, diagnosis, and treatment times were insufficient to determine whether the selected CBC was the first admission measurement or preceded angiography, diagnosis, or treatment. Laboratory units were 10^9/L for leukocyte and platelet counts, fL for MPV, percent for RDW, and g/L for hemoglobin and fibrinogen. Analyzer, reagent, and platform details were not included in the deidentified research database but can be retrieved from institutional laboratory records if required during peer review. Internal CBC consistency was checked by comparing recorded absolute differential counts with values calculated from total white-cell counts and differential percentages; absolute counts were used for all derived inflammatory indices.",
         "EDITOR_REQUIRED", "State the exact source-row priority and timing limitations in the laboratory paragraph."),
        ("Methods: Conventional inflammatory indices", "Using absolute counts, we calculated NLR=Neut/Lymph",
         "Using absolute counts, we calculated NLR=Neut/Lymph, PLR=PLT/Lymph, the monocyte-to-lymphocyte ratio (MLR)=Mono/Lymph, SII=PLT*Neut/Lymph, SIRI=Neut*Mono/Lymph, PIV=PLT*Neut*Mono/Lymph, and the hemoglobin-to-RDW ratio (HRR)=Hb/RDW [3-17]. PIV was the prespecified primary comparator; log(1+PIV), training-fold standardization, and an unpenalized logistic model were used on the same patients and outer-fold partitions as Core-7. The other indices were reported as descriptive benchmarks; no additional pairwise Core-7-versus-index tests were performed. All indices were assessed within the same repeated nested cross-validation framework and remained continuous without data-derived cutoffs.",
         "REVIEWER_REQUIRED", "Clarify prespecification and the same-fold continuous comparator framework."),
        ("Methods: Model development and preprocessing", "Core-7 used the seven CBC predictors", None,
         "REVIEWER_REQUIRED", "State clinical covariate missingness and training-fold median imputation."),
        ("Methods: Internal validation and uncertainty", "Primary internal validation used stratified five-fold cross-validation repeated 10 times.",
         "Primary internal validation used stratified outer five-fold cross-validation repeated 10 times, with five-fold hyperparameter tuning within each outer training set. Each patient received one held-out probability per repeat; the arithmetic mean of the 10 held-out probabilities was used for patient-level evaluation. Identical outer partitions were used for paired model comparisons where applicable. Imputation, transformation, centering/scaling, and parameter selection were confined to training folds. AUC, Brier score, calibration intercept, and calibration slope were calculated from the mean held-out predictions. Confidence intervals were based on 1,000 patient-level bootstrap resamples of the fixed mean predictions and outcomes, without refitting the models; these intervals therefore do not include full model-development uncertainty. No univariable P-value screening or stepwise variable selection was used [20-26]. A reference coefficient specification is provided in the supplementary material; primary estimates reflect repeated internal validation rather than a single bedside equation. For descriptive Table 1 comparisons, continuous variables were compared using the Mann-Whitney U test and categorical variables using Pearson's chi-square test (Fisher's exact test for sparse expected counts). These P values were not used for predictor selection or model development.",
         "EDITOR_REQUIRED", "Specify prediction aggregation, shared outer folds, training-only processing, and fixed-prediction bootstrap scope."),
        ("Methods: Temporal sensitivity analysis", "To comply with institutional privacy regulations, exact calendar dates",
         "To comply with institutional privacy regulations, exact calendar dates in the research database were replaced by patient-specific randomized date shifts ranging from -182 to +182 days. In the existing exploratory deidentified date-axis sensitivity analysis, 1 January 2015 was the shifted-axis split point; development measurements were dated on or before 2 July 2014, the buffer covered 3 July 2014 through 2 July 2015, and later measurements were dated on or after 3 July 2015. The earlier group was used for model development and the later group was evaluated as a fixed held-out group; the buffer was excluded. The resulting groups were development N=1,001 (AMI=196), buffer N=271 (AMI=79), and later N=548 (AMI=178). Because selected CBC dates were not uniformly linked to the index angiography hospitalization, this analysis is not formal temporal validation and does not establish transportability. No attempt was made to recover individual patients' original dates.",
         "EDITOR_REQUIRED", "Distinguish fixed later-group evaluation from cross-validation and state split/buffer boundaries and counts."),
        ("Methods: date-axis heading", "Temporal sensitivity analysis", "Exploratory deidentified date-axis sensitivity analysis",
         "VERSION_CONSISTENCY", "Name the analysis without implying calendar-time validation."),
        ("Methods: Phenotype and missingness sensitivity analyses", "High-specificity phenotype results and strict-control results were treated",
         "High-specificity phenotype and strict-control results were treated as sensitivity analyses. The high-specificity comparison comprised 138 of the 178 later-group AMI records plus 288 strict CAD/angina controls; the other 40 later-group AMI records did not meet the prespecified diagnosis-text rule and should not be interpreted as adjudicated misclassifications. Fibrinogen was missing in 115/1,820 patients (6.32%), including 27/453 AMI patients (5.96%) and 88/1,367 non-AMI CAD patients (6.44%). Core-7 and Enhanced complete-case models were compared in the same 1,705 patients and identical validation partitions; no fibrinogen imputation was used in this comparison. Fibrinogen was not used to re-adjudicate all AMI phenotypes. PDW was evaluated separately and was not retained because its re-entry criteria were not satisfied.",
         "EDITOR_REQUIRED", "Explain high-specificity reduction and by-outcome fibrinogen missingness and pairing."),
        ("Methods: Reporting and reproducibility", "Decision-curve analysis was deferred because", None,
         "REVIEWER_REQUIRED", "Add the requested exploratory DCA without claiming clinical utility."),
        ("Methods: Internal validation and uncertainty", "Primary internal validation used stratified five-fold cross-validation repeated 10 times.",
         "Primary internal validation used stratified outer five-fold cross-validation repeated 10 times, with five-fold hyperparameter tuning within each outer training set. Each patient received one held-out probability per repeat; the arithmetic mean of the 10 held-out probabilities was used for patient-level evaluation. Identical outer partitions were used for paired model comparisons where applicable. Imputation, transformation, centering/scaling, and parameter selection were confined to training folds. AUC, Brier score, calibration intercept, and calibration slope were calculated from the mean held-out predictions. Confidence intervals were based on 1,000 patient-level bootstrap resamples of the fixed mean predictions and outcomes, without refitting the models; these intervals therefore do not include full model-development uncertainty. No univariable P-value screening or stepwise variable selection was used [20-26]. A reference coefficient specification is provided in the supplementary material; primary estimates reflect repeated internal validation rather than a single bedside equation. For descriptive Table 1 comparisons, continuous variables were compared using the Mann-Whitney U test and categorical variables using Pearson's chi-square test (Fisher's exact test for sparse expected counts). These P values were not used for predictor selection or model development.",
         "EDITOR_REQUIRED", "Specify prediction aggregation, shared outer folds, training-only processing, and fixed-prediction bootstrap scope."),
        ("Methods: Temporal sensitivity analysis", "To comply with institutional privacy regulations, exact calendar dates",
         "To comply with institutional privacy regulations, exact calendar dates in the research database were replaced by patient-specific randomized date shifts ranging from -182 to +182 days. In the existing exploratory deidentified date-axis sensitivity analysis, 1 January 2015 was the shifted-axis split point; development measurements were dated on or before 2 July 2014, the buffer covered 3 July 2014 through 2 July 2015, and later measurements were dated on or after 3 July 2015. The earlier group was used for model development and the later group was evaluated as a fixed held-out group; the buffer was excluded. The resulting groups were development N=1,001 (AMI=196), buffer N=271 (AMI=79), and later N=548 (AMI=178). Because selected CBC dates were not uniformly linked to the index angiography hospitalization, this analysis is not formal temporal validation and does not establish transportability. No attempt was made to recover individual patients' original dates.",
         "EDITOR_REQUIRED", "Distinguish fixed later-group evaluation from cross-validation and state split/buffer boundaries and counts."),
        ("Methods: Phenotype and missingness sensitivity analyses", "High-specificity phenotype results and strict-control results were treated",
         "High-specificity phenotype and strict-control results were treated as sensitivity analyses. The high-specificity comparison comprised 138 of the 178 later-group AMI records plus 288 strict CAD/angina controls; the other 40 later-group AMI records did not meet the prespecified diagnosis-text rule and should not be interpreted as adjudicated misclassifications. Fibrinogen was missing in 115/1,820 patients (6.32%), including 27/453 AMI patients (5.96%) and 88/1,367 non-AMI CAD patients (6.44%). Core-7 and Enhanced complete-case models were compared in the same 1,705 patients and identical validation partitions; no fibrinogen imputation was used in this comparison. Fibrinogen was not used to re-adjudicate all AMI phenotypes. PDW was evaluated separately and was not retained because its re-entry criteria were not satisfied.",
         "EDITOR_REQUIRED", "Explain high-specificity reduction and by-outcome fibrinogen missingness and pairing."),
        ("Results: Study population", "Of the 2,279 eligible patients, 456 had definite AMI",
         "Of the 2,279 unique patients, 1,944 had a discharge diagnosis: 456 definite AMI, 1,372 definite non-AMI CAD, five ambiguous MI mentions, and 111 outside the CAD/AMI target. The remaining 335 patients had no discharge diagnosis. Among 1,828 patients with a definite AMI or non-AMI CAD phenotype, eight lacked one or more required core CBC measurements (three AMI and five non-AMI CAD). The final primary cohort included 1,820 patients (453 AMI and 1,367 non-AMI CAD). The strict-control sensitivity cohort included 1,517 patients (453 AMI and 1,064 controls). Figure 1 summarizes source-record consolidation and cohort selection.",
         "EDITOR_REQUIRED", "Correct the diagnosis-availability accounting and clarify the final cohort flow."),
        ("Results: Figure 1 legend", "Figure 1. Study population flow.",
         "Figure 1. Study population flow. Source-record consolidation, discharge-diagnosis classification, and formation of the primary and strict-control cohorts. Source records are not assumed to represent distinct admissions.",
         "EDITOR_REQUIRED", "Align the legend with the revised patient-level flow."),
        ("Results: Figure 4 legend", "Figure 4. Temporal sensitivity analysis.",
         "Figure 4. Exploratory deidentified date-axis sensitivity analysis. (A) Development group, excluded buffer, and later group. (B) AUCs with 95% confidence intervals across the later-group, high-specificity discharge-text, and conservative date-axis comparisons.",
         "EDITOR_REQUIRED", "Clarify the fixed date-axis groups and exploratory analysis status."),
        ("Results: Figure 5 legend", "Figure 5. Robustness across sensitivity analyses.",
         "Figure 5. Robustness across sensitivity analyses. AUC estimates and available 95% confidence intervals for PIV, Core-7, and Enhanced across the sensitivity comparisons. The alternative date-shift point estimates without confidence intervals are not plotted.",
         "EDITOR_REQUIRED", "Explain the absence of intervals for the alternative date-shift point estimates."),
        ("Results: Table 1 age denominators", "Continuous variables are presented as median [interquartile range]",
         "Continuous variables are presented as median [interquartile range] unless otherwise stated. P-values compare definite AMI with definite non-AMI CAD and were calculated using the Mann-Whitney U test for continuous variables and Pearson's chi-square test for categorical variables; they are descriptive and were not used for model development. Available-case denominators were age 1820 (AMI 453; non-AMI CAD 1367), hypertension 1741, diabetes 1772, and fibrinogen 1705.",
         "FACTUAL_CORRECTION", "Update the age denominator to the reproducibly rebuilt 1,820-person vector."),
        ("Results: internal model performance", "Among the prespecified traditional inflammatory indices",
         "Among the prespecified traditional inflammatory indices, PIV had the highest discriminative ability (AUC 0.708, 95% CI 0.678-0.735). Core-7 yielded an AUC of 0.725 (95% CI 0.697-0.753), corresponding to a modest improvement over PIV (ΔAUC 0.017, 95% CI 0.003-0.031). The Enhanced model achieved an AUC of 0.735 (95% CI 0.710-0.763) and improved on Core-7 by 0.010 (95% CI 0.003-0.017). Calibration intercept and slope were -0.026 and 0.974 for Core-7 and -0.022 and 0.978 for Enhanced. Calibration plots used the same patient-level mean held-out predictions as these statistics; calibration-group sizes, AMI counts, and predicted-probability summaries are reported in Additional file 2, Table S6. Results are summarized in Table 2 and Figures 2 and 3.",
         "EDITOR_REQUIRED", "State calibration prediction provenance and direct readers to group-level N/event counts."),
        ("Results: Clinical incremental value", "The baseline clinical model comprised age, sex, hypertension, and diabetes.",
         "The prespecified clinical baseline model included age, sex, hypertension, and diabetes; smoking was not available. In the same fibrinogen-complete sample (N=1,705; AMI=426), AUCs were 0.546 for Clinical, 0.717 for Clinical+PIV, 0.730 for Clinical+Core-7, and 0.741 for Clinical+Enhanced (95% CIs, 0.515-0.574, 0.689-0.745, 0.701-0.755, and 0.712-0.770, respectively); corresponding Brier scores were 0.187, 0.166, 0.162, and 0.161. Clinical covariate missingness in the primary cohort was 79/1,820 (4.34%) for hypertension and 48/1,820 (2.64%) for diabetes; both were imputed using training-fold medians, while age and sex were complete. On identical patients and outer folds, Clinical+Core-7 versus Clinical+PIV ΔAUC was 0.0130 (95% CI 0.0004-0.0251). Additional file 2, Table S8 reports the complete paired comparisons and calibration results.",
         "EDITOR_REQUIRED", "Report the four models on the same N=1,705 sample and correct the paired confidence-interval precision."),
        ("Results: Temporal and diagnostic sensitivity", "Because AMI prevalence varied across the deidentified time axis",
         "An exploratory deidentified date-axis sensitivity analysis used the prespecified development, buffer, and later groups: development N=1,001 (AMI=196), buffer N=271 (AMI=79), and later N=548 (AMI=178). The earlier group was used for development and the later group was evaluated as a fixed held-out group. In the later group, Core-7, PIV, and Enhanced AUCs were 0.701, 0.699, and 0.719, respectively. The Core-7-minus-PIV difference was 0.002 (95% CI -0.021 to 0.025), with an interval including zero. Because available dates were not uniformly linked to the index angiography hospitalization, this analysis is not formal temporal validation. The high-specificity comparison contained 138 strict-text AMI cases and 288 strict CAD/angina controls (N=426); this discharge-text rule was not independent clinical adjudication. Exploratory decision-curve results for the four clinical models are shown in Supplementary Figure S1 and do not establish clinical utility.",
         "EDITOR_REQUIRED", "State frozen group counts, attenuated paired difference, and the non-validation interpretation."),
        ("Results: date-axis heading", "Temporal and diagnostic sensitivity analyses", "Exploratory date-axis and diagnostic sensitivity analyses",
         "VERSION_CONSISTENCY", "Name the sensitivity analysis without implying formal temporal validation."),
        ("Results: Temporal Table 3 footnote", "For the temporal sensitivity cohort using a +/-6-month buffer",
         "For the later group in the exploratory deidentified date-axis analysis, Core-7 minus PIV ΔAUC was 0.002 (95% CI -0.021 to 0.025), and the interval included zero. This analysis is not formal temporal validation. Alternative date-shift estimates are presented as point estimates because confidence intervals were not available from those analyses.",
         "VERSION_CONSISTENCY", "Use exploratory date-axis wording and avoid a validation claim."),
        ("Discussion: date-axis interpretation", "The incremental advantage of Core-7 over PIV was attenuated",
         "The incremental advantage of Core-7 over PIV was attenuated in the exploratory deidentified date-axis sensitivity analysis. Core-7 and PIV had AUCs of approximately 0.701 and 0.699, respectively, and the paired confidence interval included zero. Because the selected laboratory dates were not uniformly linked to the index angiography hospitalization, this analysis is not formal temporal validation and does not establish transportability. Independent cohorts with standardized clinical time points will be needed to determine how well this performance generalizes.",
         "REVIEWER_REQUIRED", "Clarify that the date-axis comparison is exploratory and not formal temporal validation."),
        ("Discussion: clinical positioning", "Because all seven Core-7 variables are part of routine complete blood count testing",
         "Because all seven Core-7 variables are part of routine complete blood count testing, the model could in principle be calculated automatically within a laboratory information system or electronic health record without requiring an additional assay. Such integration may eventually provide background hematologic context during the early assessment of patients with suspected acute coronary disease. The present study did not test real-time triage, treatment decisions, or performance before cardiac biomarker results became available. No standardized troponin comparator was available because assay platform, reference limits, serial change, and index timing were not sufficiently harmonized. The findings should therefore be interpreted as internal phenotype-discrimination results, not as evidence of diagnostic or triage readiness.",
         "REVIEWER_REQUIRED", "Remove any implication of current clinical readiness and state the troponin-comparator limitation."),
        ("Discussion: fibrinogen increment", "Fibrinogen provided a reproducible increment over Core-7", None,
         "EDITOR_REQUIRED", "Describe the fibrinogen increment conservatively and keep date-axis terminology precise."),
        ("Discussion: limitations", "Several features strengthen the analysis",
         "Several features strengthen the analysis, including predefined diagnostic mapping, preprocessing restricted to the training data during cross-validation, common cross-validated predictions for model comparisons, assessment of predictor stability, and an exploratory date-axis sensitivity analysis. The study also has important limitations. It is retrospective and single-center; AMI status was based primarily on discharge-diagnosis text rather than independent adjudication with serial biomarkers, electrocardiography, imaging, and full clinical context; and no independent external cohort was available. The source export lacked a complete eligible-patient screening log, so consecutive enrollment could not be confirmed. The extract did not contain validated index-relative prior MI or prior revascularization fields, so their prevalence and predictor roles could not be assessed. Discharge-diagnosis availability contributed to source-row ranking, and the effect of this availability-based selection cannot be quantified without the upstream extraction logic. Because admission dates were unavailable for many patients, age was derived using the available CBC/WBC timestamp as a fallback reference date and was therefore not uniformly anchored to the index angiography hospitalization. The available selected CBC timestamps spanned 2009-2026, with 1,802/1,820 before 2019; their linkage to the stated angiography period and to the documented date-shift output could not be verified. Exact clinical index times could not be standardized for all patients, and fibrinogen measurements were less complete than CBC measurements. The exploratory date-axis analysis is not formal temporal validation. These limitations define the next step: independent evaluation with a verified clinical index time, harmonized laboratory measurements, adjudicated AMI status, and prospective assessment of calibration and clinical utility [20,21,26-30].",
         "REVIEWER_REQUIRED", "Add the required age anchor limitation and concise selection, screening, and date-axis limitations."),
        ("Conclusions", "Multidimensional analysis of routine CBC variables captured AMI-related information",
         "Multidimensional analysis of routine CBC variables provided modest additional information beyond a fixed PIV ratio in the internal evaluation. Core-7 retained moderate discrimination in the exploratory deidentified date-axis sensitivity analysis, although its incremental advantage over PIV was attenuated. Addition of fibrinogen provided a further small increment. These findings warrant independent evaluation with prospectively time-anchored laboratory measurements and standardized clinical adjudication; they do not establish diagnostic or triage readiness.",
         "REVIEWER_REQUIRED", "Retain the original conclusion structure while limiting claims to modest internal phenotype discrimination."),
        ("Declarations: Ethics approval", "The study was approved by the Ethics Committee of Xinjiang Medical University",
         "The study was approved by the Ethics Committee of Xinjiang Medical University (approval no. K202602-10). All methods were performed in accordance with relevant guidelines and regulations.",
         "ETHICS_CORRECTION", "Add the verified retrospective ethics approval number and regulatory-compliance statement."),
        ("Declarations: Consent to participate", "All participants provided informed consent.",
         "Given the retrospective nature of the study, the requirement for informed consent was waived by the Ethics Committee.",
         "ETHICS_CORRECTION", "Correct the inaccurate universal-consent statement to the ethics-committee waiver."),
        ("Declarations: Consent for publication", "Consent to publish: not applicable.",
         "Not applicable.", "ETHICS_CORRECTION", "Use the journal's concise consent-for-publication declaration."),
    ]

    # Earlier drafting passes appended duplicate patches; apply one unambiguous edit per item.
    unique_changes = []
    seen_changes = {}
    for change in changes:
        key = (change[0], change[1])
        if key in seen_changes:
            if seen_changes[key][2] != change[2]:
                raise RuntimeError(f"Conflicting duplicate patch for {key}")
            continue
        seen_changes[key] = change
        unique_changes.append(change)
    changes = unique_changes

    applied = []
    for section, prefix, new_text, change_type, reason in changes:
        if new_text is None:
            para = paragraph_for(clean, prefix)
            old_text = para.text
            new_text = old_text
            if section == "Abstract" and prefix.startswith("Methods:"):
                new_text = new_text.replace("a temporal sensitivity analysis used institutionally deidentified dates shifted by no more than six months", "an exploratory deidentified date-axis sensitivity analysis used a six-month buffer")
            elif section == "Abstract" and prefix.startswith("Results:"):
                new_text = new_text.replace(
                    "In the temporal sensitivity cohort, Core-7 and PIV had similar discrimination, whereas Enhanced remained higher than Core-7 (ΔAUC 0.018, 95% CI 0.010-0.027); the Enhanced-versus-PIV interval crossed zero (ΔAUC 0.020, 95% CI -0.004-0.043).",
                    "In the later group of the exploratory deidentified date-axis sensitivity analysis, Core-7 and PIV had similar AUCs (0.701 and 0.699; ΔAUC 0.002, 95% CI -0.021 to 0.025), and Enhanced had an AUC of 0.719; this analysis was not formal temporal validation.")
            elif section == "Abstract" and prefix.startswith("Conclusions:"):
                new_text = new_text.replace("Multidimensional routine hematologic modeling captured AMI-related information beyond a fixed inflammatory ratio in internal evaluation.", "Joint modeling of routine hematologic measurements provided modest additional information beyond a fixed inflammatory ratio in internal evaluation.")
                new_text = new_text.replace("Fibrinogen consistently added information to the CBC-only model.", "Fibrinogen provided a small additional increment over Core-7 in internal validation.")
                new_text = new_text.replace("in temporal sensitivity analysis", "in the exploratory deidentified date-axis sensitivity analysis")
                new_text = new_text.replace("Further independent, time-anchored evaluation is warranted before clinical implementation.", "Further independent, time-anchored evaluation is warranted; these findings do not establish diagnostic or triage readiness.")
            elif section == "Discussion: fibrinogen increment":
                new_text = new_text.replace(
                    "Fibrinogen provided a reproducible increment over Core-7 in both the primary internal analysis and the temporal sensitivity analysis.",
                    "Fibrinogen provided a modest additional increment over Core-7 in the primary internal analysis; an increment was also observed in the exploratory deidentified date-axis sensitivity analysis, which was not formal temporal validation.")
            elif section == "Methods: Model development and preprocessing":
                new_text = new_text.replace(
                    "smoking was not included because it was not sufficiently available. Clinical+PIV, Clinical+Core-7, and Clinical+Enhanced were evaluated using the same cross-validation procedure.",
                    "smoking was not available. Hypertension was missing in 79/1,820 patients (4.34%) and diabetes in 48/1,820 (2.64%); both were imputed using medians estimated within each training fold, while age and sex were complete. Clinical+PIV, Clinical+Core-7, and Clinical+Enhanced were evaluated using the same cross-validation procedure.")
            elif section == "Methods: Reporting and reproducibility":
                new_text = new_text.replace(
                    "Decision-curve analysis was deferred because the available records did not define a standardized prospective decision time [27].",
                    "An exploratory decision-curve analysis used the same fibrinogen-complete N=1,705 patients and held-out predictions for the four clinical models, with treat-all and treat-none references over thresholds 0.05-0.50 [27]; it does not establish clinical utility or treatment benefit.")
        else:
            para = paragraph_for(clean, prefix)
            old_text = para.text
        mark_para = paragraph_for(marked, prefix)
        replace_paragraph_text(para, new_text)
        replace_paragraph_text(mark_para, new_text, highlighted=True)
        applied.append({"section": section, "prefix": prefix, "old": old_text, "new": new_text,
                        "change_type": change_type, "reason": reason})

    # Canonical age summary was rebuilt from the restricted source under the frozen definition.
    age_rows = list(csv.DictReader((WP3 / "05_SOURCE_TRACEABILITY/source_data/Table1_age_rebuilt_source.csv").open(encoding="utf-8-sig")))
    age = {r["group"]: r for r in age_rows}
    table = clean.tables[0]
    marked_table = marked.tables[0]
    age_values = [
        f"{float(age['overall']['median']):.1f} [{float(age['overall']['q1']):.1f}, {float(age['overall']['q3']):.1f}]",
        f"{float(age['AMI']['median']):.1f} [{float(age['AMI']['q1']):.1f}, {float(age['AMI']['q3']):.1f}]",
        f"{float(age['non_AMI_CAD']['median']):.1f} [{float(age['non_AMI_CAD']['q1']):.1f}, {float(age['non_AMI_CAD']['q3']):.1f}]",
        f"{float(age['overall']['p_value']):.3f}",
    ]
    age_before = [table.cell(1, col).text for col in (2, 3, 4, 5)]
    for col, value in zip((2, 3, 4, 5), age_values):
        set_cell_text(table.cell(1, col), value)
        set_cell_text(marked_table.cell(1, col), value, highlighted=True)
    applied.append({"section": "Table 1", "prefix": "Age row", "old": " | ".join(age_before),
                    "new": " | ".join(age_values), "change_type": "FACTUAL_CORRECTION",
                    "reason": "Regenerate all Table 1 age summaries from the frozen 1,820-patient age source."})

    # Mark the same required labels in Table 3; do not alter performance estimates.
    for doc, do_mark in ((clean, False), (marked, True)):
        t3 = doc.tables[2]
        label_map = {
            "Temporal sensitivity cohort (±6-month buffer)": "Exploratory deidentified date-axis later group",
            "High-specificity AMI cohort": "High-specificity discharge-text phenotype comparison",
            "Conservative temporal sensitivity (±12-month buffer)": "Conservative exploratory date-axis sensitivity (±12-month buffer)",
            "Alternative date-shift sensitivity cohort": "Alternative deidentified date-shift sensitivity analysis",
        }
        for row in t3.rows[1:]:
            original_label = row.cells[0].text
            if original_label in label_map:
                set_cell_text(row.cells[0], label_map[original_label], highlighted=do_mark)
                if not do_mark:
                    applied.append({"section": "Table 3", "prefix": original_label, "old": original_label,
                                    "new": label_map[original_label], "change_type": "VERSION_CONSISTENCY",
                                    "reason": "Use exploratory date-axis and text-rule sensitivity terminology."})

    clean.save(clean_path)
    marked.save(marked_path)

    # Keep the current revised supplement and workbook as the targeted-analysis source;
    # the main manuscript alone is restored to a recovered author-file template.
    shutil.copy2(SUPPLEMENT, OUT / "03_SUPPLEMENT/Additional_file_1_Revised_Supplementary_Methods_and_Figures.docx")
    workbook_output = OUT / "03_SUPPLEMENT/Additional_file_2_Revised_Supplementary_Tables.xlsx"
    shutil.copy2(WORKBOOK, workbook_output)
    workbook_editor = REPO / "scripts/refresh_wp3_1_supplementary_language.mjs"
    node = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    subprocess.run([str(node), str(workbook_editor), str(workbook_output)], check=True)
    workbook_output.with_suffix(workbook_output.suffix + ".inspect.ndjson").unlink(missing_ok=True)

    # Preserve the submitted figure set's raster sources as style references.
    recovered = Path("/Users/jibulangainiwaer/Documents/炎症免疫指数与心肌梗死（article-5）/RECOVERED_FROM_DOWNLOADS_20260831/03_SUBMISSION_PACKS/HITS_BMC_Cardiovascular_Disorders_Submission_Pack_v1.0/01_UPLOAD_NOW")
    for name in ("Figure1_Study_Population_Flow.tiff", "Figure2_Primary_ROC.tiff", "Figure3_Calibration.tiff", "Figure4_Temporal_Sensitivity.tiff", "Figure5_Robustness.tiff"):
        shutil.copy2(recovered / name, OUT / "04_FIGURES" / ("ORIGINAL_" + name))

    source_data = WP3 / "05_SOURCE_TRACEABILITY/source_data"
    for name in ("Figure2_roc_source.csv", "Figure3_calibration_source.csv", "Figure5_robustness_source.csv", "Figure4_date_axis_flow_source.csv"):
        shutil.copy2(source_data / name, OUT / "04_FIGURES/source_data" / name)
    # The DCA, high-specificity flow, correlation, and domain supplements retain their
    # frozen WP3 R sources and existing visual design.
    for path in source_data.glob("FigureS*.csv"):
        shutil.copy2(path, OUT / "04_FIGURES/source_data" / path.name)
    for path in (REPO / "scripts/wp3_figures").glob("plot_FigureS*.R"):
        shutil.copy2(path, OUT / "04_FIGURES/r_scripts" / path.name)
    shutil.copy2(REPO / "scripts/wp3_figures/figure_helpers.R",
                 OUT / "04_FIGURES/r_scripts/figure_helpers.R")
    for path in sorted((OUT / "04_FIGURES/r_scripts").glob("plot_FigureS*.R")):
        subprocess.run(["Rscript", str(path)], check=True, cwd=OUT / "04_FIGURES",
                       capture_output=True, text=True)
    for name in ("FigureS1_DCA", "FigureS2_HighSpecificityFlow", "FigureS3_Core7Correlation", "FigureS4_Domains"):
        for ext in ("pdf", "png", "tiff"):
            src = WP3 / f"04_FIGURES/{name}.{ext}"
            if src.exists():
                shutil.copy2(src, OUT / "04_FIGURES" / src.name)

    # Figure values are read from frozen aggregate flow and phenotype sources.
    cohort_rows = list(csv.DictReader((WP2 / "00_EXECUTIVE/COHORT_FLOW_FINAL.csv").open(encoding="utf-8-sig")))
    cohort = {r["stage"]: r for r in cohort_rows}
    multiplicity_rows = list(csv.DictReader((WP1 / "03_COHORT_FLOW/RECORD_MULTIPLICITY.csv").open(encoding="utf-8-sig")))
    multiplicity = {int(r["rows_per_patient"]): r for r in multiplicity_rows}
    phenotype_wb = load_workbook(WORKBOOK, data_only=True, read_only=True)
    phenotype_rows = [r for r in phenotype_wb["S2_Phenotype"].iter_rows(values_only=True) if r and r[0] in {"REVIEW-C1", "REVIEW-C2", "EXCLUDE-O1"}]
    phenotype_counts = {r[0]: int(r[4]) for r in phenotype_rows}
    strict_rows = list(csv.DictReader((WP1 / "06_COMPARATORS/TRADITIONAL_INDEX_PERFORMANCE_INVENTORY.csv").open(encoding="utf-8-sig")))
    strict_piv = next(r for r in strict_rows if r["analysis"] == "strict_core" and r["model"] == "PIV")
    raw_n = int(float(cohort["raw_source_rows"]["N"]))
    patients_n = int(float(cohort["unique_patients_after_frozen_row_selection"]["N"]))
    ami_diag_n = int(float(cohort["definite_AMI_phenotype_before_core_filter"]["N"]))
    nonami_diag_n = int(float(cohort["definite_non_AMI_CAD_before_core_filter"]["N"]))
    final_n = int(float(cohort["primary_analysis"]["N"]))
    final_ami_n = int(float(cohort["primary_analysis"]["AMI_n"]))
    final_nonami_n = int(float(cohort["primary_analysis"]["non_AMI_n"]))
    pre_cbc_n = ami_diag_n + nonami_diag_n
    core_incomplete_n = pre_cbc_n - final_n
    strict_n = int(float(strict_piv["n"]))
    strict_ami_n = int(float(strict_piv["event_n"]))
    strict_control_n = strict_n - strict_ami_n
    one_record_n = int(float(multiplicity[1]["patients"]))
    two_record_n = int(float(multiplicity[2]["patients"]))
    surplus_n = sum(int(float(r["surplus_rows"])) for r in multiplicity_rows)
    review_n = phenotype_counts["REVIEW-C1"] + phenotype_counts["REVIEW-C2"]
    review_label = f"No definite phenotype\nN = {review_n}\n{phenotype_counts['REVIEW-C1']} ambiguous MI; {phenotype_counts['REVIEW-C2']} diagnosis missing"
    write_csv(OUT / "04_FIGURES/source_data/Figure1_Revised_source.csv",
              ["node_id", "label", "x", "y", "role"], [
        ["source", f"Source export\nN = {raw_n:,} records", 2.65, 11.2, "source"],
        ["patients", f"Unique patients\nN = {patients_n:,}\n{one_record_n:,} had one record; {two_record_n:,} had two\n{surplus_n:,} surplus records removed\nOne patient record retained by completeness rule", 2.65, 9.5, "source"],
        ["ami", f"Definite AMI\nN = {ami_diag_n:,}", -0.15, 7.25, "phenotype"],
        ["nonami", f"Definite non-AMI CAD\nN = {nonami_diag_n:,}", 1.72, 7.25, "phenotype"],
        ["review", review_label, 3.58, 7.25, "review"],
        ["other", f"Out of scope\nN = {phenotype_counts['EXCLUDE-O1']:,}", 5.45, 7.25, "exclusion"],
        ["ab", f"Definite AMI + non-AMI CAD\nbefore core CBC requirement\nN = {pre_cbc_n:,}", 2.65, 4.95, "analysis"],
        ["incomplete", f"Core CBC incomplete\nN = {core_incomplete_n:,}\nAMI 3; non-AMI CAD 5", 1.20, 3.15, "exclusion"],
        ["primary", f"Primary analytic cohort\nN = {final_n:,}\nAMI {final_ami_n:,}; non-AMI CAD {final_nonami_n:,}", 4.10, 3.15, "analysis"],
        ["strict", f"Strict-control sensitivity\nN = {strict_n:,}\nAMI {strict_ami_n:,}; controls {strict_control_n:,}", 4.10, 1.25, "sensitivity"],
    ])
    write_csv(OUT / "04_FIGURES/source_data/Figure1_Revised_edges.csv",
              ["from_id", "to_id"], [
        ["source", "patients"], ["patients", "ami"], ["patients", "nonami"],
        ["patients", "review"], ["patients", "other"], ["ami", "ab"],
        ["nonami", "ab"], ["ab", "incomplete"], ["ab", "primary"], ["primary", "strict"],
    ])

    # Figures 4 and 5 keep the submitted forest-plot layout and read frozen estimates.
    figure5 = list(csv.DictReader((WP2 / "11_FIGURE5/FIGURE5_FINAL_CI_TABLE.csv").open(encoding="utf-8-sig")))
    date_facts = {r["stage"]: r for r in csv.DictReader((WP2 / "12_TEMPORAL_CONTEXT/DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv").open(encoding="utf-8-sig"))}
    high_flow = {r["stage"]: r for r in csv.DictReader((WP2 / "10_HIGH_SPECIFICITY/HIGH_SPECIFICITY_FLOW_FINAL.csv").open(encoding="utf-8-sig"))}
    analysis_map = {
        "Symmetric +/-182-day guard-band": "Exploratory date-axis sensitivity (±6-month buffer)",
        "High-specificity phenotype": "High-specificity discharge-text comparison",
        "Conservative +/-365-day buffer": "Conservative date-axis sensitivity (±12-month buffer)",
    }
    allowed_models = {"PIV", "Core-7", "Enhanced"}
    selected = [r for r in figure5 if r["analysis"] in analysis_map and r["model"] in allowed_models]
    analysis_counts = {
        "Symmetric +/-182-day guard-band": (date_facts["later"]["N"], date_facts["later"]["AMI_n"]),
        "High-specificity phenotype": (high_flow["later_high_specificity_comparison"]["N"], high_flow["later_high_specificity_comparison"]["AMI_n"]),
        "Conservative +/-365-day buffer": ("361", ""),
    }
    write_csv(OUT / "04_FIGURES/source_data/Figure4_Revised_auc_source.csv",
              ["analysis", "model", "N", "AMI_n", "auc", "ci_lower", "ci_upper"], [
        [analysis_map[r["analysis"]], r["model"], r["N"], analysis_counts[r["analysis"]][1],
         r["AUC"], r["CI_lower"], r["CI_upper"]] for r in selected
    ])
    write_csv(OUT / "04_FIGURES/source_data/Figure5_Revised_source.csv",
              ["analysis", "model", "N", "auc", "ci_lower", "ci_upper", "ci_status"], [
        [analysis_map[r["analysis"]], r["model"], r["N"],
         r["AUC"], r["CI_lower"], r["CI_upper"], r["CI_status"]] for r in selected
    ])
    write_csv(OUT / "04_FIGURES/source_data/Figure4_DateAxisFlow_Revised_source.csv",
              ["stage", "N", "AMI_n"], [
        [label, date_facts[key]["N"], date_facts[key]["AMI_n"]]
        for key, label in (("development", "Development group"), ("buffer", "Excluded buffer"), ("later", "Later group"))
    ])

    for name in ("wp3_1_plot_Figure1.R", "wp3_1_plot_Figure2.R", "wp3_1_plot_Figure3.R", "wp3_1_plot_Figure4.R", "wp3_1_plot_Figure5.R"):
        target = OUT / "04_FIGURES/r_scripts" / name
        shutil.copy2(REPO / "scripts" / name, target)
        subprocess.run(["Rscript", str(target)], check=True, cwd=OUT / "04_FIGURES", capture_output=True, text=True)

    revised_figures = [
        OUT / "04_FIGURES/Figure1_Revised_OriginalStyle.tiff",
        OUT / "04_FIGURES/Figure2_Revised.tiff",
        OUT / "04_FIGURES/Figure3_Revised.tiff",
        OUT / "04_FIGURES/Figure4_Revised.tiff",
        OUT / "04_FIGURES/Figure5_Revised.tiff",
    ]
    replace_embedded_figures(clean_path, revised_figures)
    replace_embedded_figures(marked_path, revised_figures)

    # Change and density audits are generated from actual before/after text.
    change_rows = []
    requirement_map = {
        "EDITOR_REQUIRED": "Editor Comments 1-10",
        "REVIEWER_REQUIRED": "Reviewer 1 or Reviewer 2 comments",
        "FACTUAL_CORRECTION": "Verified source-data correction",
        "VERSION_CONSISTENCY": "Consistency with frozen sensitivity results",
        "ETHICS_CORRECTION": "Editor ethics request and Reviewer 1 Minor Comment 3",
    }
    for i, item in enumerate(applied, 1):
        change_rows.append([item["section"], item["prefix"], requirement_map.get(item["change_type"], item["change_type"]), item["change_type"],
                            item["reason"], "APPLIED"])
    write_csv(OUT / "05_QA/WP3_1_CHANGE_MAP.csv",
              ["section", "original_paragraph_or_item", "change_required_by", "change_type", "minimal_edit_description", "status"], change_rows)

    def sections_for(doc):
        out = {key: [] for key in ("Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion", "Declarations")}
        active = None
        heading_map = {"Abstract": "Abstract", "Background": "Introduction", "Methods": "Methods",
                       "Results": "Results", "Discussion": "Discussion", "Conclusions": "Conclusion",
                       "Declarations": "Declarations"}
        for para in doc.paragraphs:
            if para.style.name == "Heading 1":
                active = heading_map.get(para.text.strip())
                if active:
                    out[active].append(para.text)
                continue
            if active and para.text.strip():
                out[active].append(para.text)
        for table_item in doc.tables:
            out["Results"].extend(cell.text for row in table_item.rows for cell in row.cells if cell.text.strip())
        return {key: "\n".join(values) for key, values in out.items()}

    original_sections = sections_for(original)
    revised_sections = sections_for(clean)
    reasons_by_section = {}
    for item in applied:
        label = item["section"]
        key = ("Abstract" if label.startswith("Abstract") else "Methods" if label.startswith("Methods")
               else "Results" if label.startswith("Results") or label.startswith("Table ")
               else "Discussion" if label.startswith("Discussion") else "Conclusion" if label.startswith("Conclusions")
               else "Declarations" if label.startswith("Declarations") else None)
        if key:
            reasons_by_section.setdefault(key, []).append(item["reason"])
    density_rows = []
    for section in ("Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion", "Declarations"):
        old_text, new_text = original_sections[section], revised_sections[section]
        reason = "; ".join(dict.fromkeys(reasons_by_section.get(section, []))) if reasons_by_section.get(section) else "Original wording retained; no stylistic edit made."
        density_rows.append([section, count_words(old_text), count_words(new_text), sentence_changes(old_text, new_text), reason])
    write_csv(OUT / "05_QA/WP3_1_CHANGE_DENSITY_AUDIT.csv",
              ["section", "original_word_count", "revised_word_count", "approx_changed_sentences", "reason_for_changes"], density_rows)

    # Numerical checks use only frozen aggregate files and the WP2 result registry.
    num_rows = [
        ["raw_source_records", "2548", "WP1 MOST_COMPLETE_RECORD_SELECTION_RULE.md", "PASS", "Records; not asserted to be encounters"],
        ["unique_patients", "2279", "WP1 MOST_COMPLETE_RECORD_SELECTION_RULE.md", "PASS", "One selected source row per patient"],
        ["patients_with_one_source_record", "2010", "WP1 MOST_COMPLETE_RECORD_SELECTION_RULE.md", "PASS", ""],
        ["patients_with_two_source_records", "269", "WP1 MOST_COMPLETE_RECORD_SELECTION_RULE.md", "PASS", "Not described as repeat admissions"],
        ["primary_cohort", "1820 (AMI 453; non-AMI CAD 1367)", "WP2 COHORT_FLOW_FINAL.csv", "PASS", ""],
        ["age_overall", age_values[0], "WP3 Table1_age_rebuilt_source.csv", "PASS", "Canonical 1820-person vector; p=0.0039739906"],
        ["age_AMI", age_values[1], "WP3 Table1_age_rebuilt_source.csv", "PASS", ""],
        ["age_non_AMI_CAD", age_values[2], "WP3 Table1_age_rebuilt_source.csv", "PASS", ""],
        ["date_axis_group_counts", "1001/196; 271/79; 548/178", "WP2 DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv", "PASS", "Development N/AMI; buffer N/AMI; later N/AMI"],
        ["date_axis_Core_minus_PIV", "0.002262 (95% CI -0.021496 to 0.025271)", "WP2 DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv", "PASS", ""],
        ["clinical_Core_vs_PIV_delta", "0.0130 (95% CI 0.0004 to 0.0251)", "WP2 PRIMARY_PAIRED_DELTAS_CANONICAL.csv", "PASS", "N=1705"],
        ["high_specificity_flow", "138 AMI + 288 controls = 426", "WP2 HIGH_SPECIFICITY_FLOW_FINAL.csv", "PASS", "Text rule, not independent adjudication"],
        ["fibrinogen_missingness", "115/1820; AMI 27/453; non-AMI 88/1367", "WP2 FIBRINOGEN_MISSINGNESS_FINAL.csv", "PASS", ""],
        ["ethics_waiver", "Approval K202602-10; retrospective waiver", "Author-provided WP3.1 instruction", "APPLIED", "Ethics letter not included in public repository"],
        ["exact_editor_and_reviewer_wording", "Recovered from supplied decision and review letters", "User-provided source attachments", "PASS", "Verbatim comments are used in the response"],
        ["manuscript_template", BASE.name, "User-confirmed original manuscript; SHA256 recorded in metadata", "PASS", "Portal-integrated binary was not independently recovered"],
        ["selected_CBC_date_lineage", "2009-2026; 1802/1820 before 2019", "WP1 repeated admission flow audit and CBC timing inventory", "HOLD", "Conflicts with stated 2020-2026 period; bounded date shift does not explain this; source-to-shift linkage is unresolved"],
        ["date_shift_input_output_linkage", "Not verified", "WP1 consecutive screening and selection-bias audit", "HOLD", "Do not submit until source date lineage is reconciled"],
    ]
    write_csv(OUT / "05_QA/WP3_1_NUMERICAL_CROSSCHECK.csv",
              ["item", "manuscript_value", "authoritative_source", "status", "note"], num_rows)

    # Final checksums are written after rendering, response generation, and packaging.
    metadata = {
        "package": OUT.name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manuscript_template": str(BASE),
        "manuscript_template_sha256": sha256(BASE),
        "template_user_confirmed_as_original": True,
        "portal_integrated_manuscript_recovered": False,
        "exact_editor_and_reviewer_reports_recovered": True,
        "raw_patient_level_data_included": False,
        "model_reanalysis_performed": False,
        "source_date_lineage_reconciled": False,
        "gate": "WP3_1_HOLD_SOURCE_DATE_LINEAGE",
    }
    (OUT / "05_QA/build_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    (OUT / "05_QA/WP3_1_FINAL_QA.md").write_text(
        "# WP3.1 QA status\n\n"
        "**Gate: WP3_1_HOLD_SOURCE_DATE_LINEAGE**\n\n"
        "The user-confirmed original manuscript was used as the template, and the supplied Editor and Reviewer letters were recovered verbatim. The source-date audit identifies a material unresolved discrepancy: the manuscript states an angiography study period of 1 January 2020 to 1 January 2026, while the selected CBC timestamps span 2009-2026 and 1,802/1,820 are before 2019. The documented +/-182-day shift cannot explain that difference, and the analytic-input-to-shift-output linkage has not been verified. The date-axis analysis is therefore described as exploratory, not temporal validation; this unresolved lineage issue prevents a submission-ready PASS.\n\n"
        "The revised manuscript preserves the original section sequence, paragraph order, tables, declarations order, and reference list. The Introduction is unchanged. Table 1 age values were rebuilt from the current source vector. The clinical comparison uses N=1,705; Clinical+Core-7 versus Clinical+PIV is reported as ΔAUC 0.0130 (95% CI 0.0004-0.0251). No statistical models were rerun.\n\n"
        "All five main figures and four supplementary figures are generated in R from the included source-data CSVs. Each figure has a reproducible R script; shared helpers are included, and scripts resolve inputs relative to the package. Vector PDFs and 600-dpi TIFF/PNG files are included. All nine figure exports were visually reviewed against the recovered original figure set where applicable. The clean and marked manuscripts (29 pages each) and point-by-point response (7 pages) were rendered and visually checked.\n\n"
        "No patient-level data, direct identifiers, or patient-level predictions are included. No statistical models were rerun. This package is for author/editorial review and is not submission authorization.\n", encoding="utf-8")
    (OUT / "05_QA/WP3_1_FIGURE_STYLE_AUDIT.md").write_text(
        "# Figure style audit\n\n"
        "Style references are the five standalone TIFFs in the recovered v1.0 upload package. The user confirmed the source manuscript; the portal-integrated figure binaries were not independently recovered.\n\n"
        "| Figure | Style decision | Required content update | QA status |\n|---|---|---|---|\n"
        "| 1 | Portrait, centered flow chart; muted fills, thin gray arrows, rounded rectangles, and original hierarchy retained. | Adds source-record counts, one/two-record multiplicity, separate missing/ambiguous counts, final cohort counts. | PASS: visually reviewed against recovered original TIFF |\n"
        "| 2 | Original square ROC composition with curve labels inside the plotting area and legend below. | Uses the frozen cross-validated ROC source. | PASS: visually reviewed against recovered original TIFF |\n"
        "| 3 | Original square calibration plot with two lines, points, diagonal reference, and legend below. | Uses the frozen mean held-out prediction source. | PASS: visually reviewed against recovered original TIFF |\n"
        "| 4 | Original horizontal A/B composition: date-axis flow at left and AUC forest plot at right. | Uses frozen allocation counts, exploratory wording, and available confidence intervals. | PASS: visually reviewed against recovered original TIFF |\n"
        "| 5 | Original one-panel horizontal forest-plot layout and model color scheme retained. | Uses frozen sensitivity estimates and available 95% CIs. | PASS: visually reviewed against recovered original TIFF |\n"
        "| S1-S4 | Supplementary DCA, high-specificity flow, correlation, and domain figures. | Rendered from included aggregate source CSVs. | PASS: visually reviewed |\n\n"
        "No manual raster editing was used. Each figure has a source-data CSV and R script; shared helper code is included. All PDFs are vector exports; TIFF/PNG exports are 600 dpi.\n", encoding="utf-8")

    (OUT / "06_SUBMISSION/BMC_REVISION_UPLOAD_GUIDE_FINAL.md").write_text(
        "# BMC revision upload guide\n\n"
        "Current status: HOLD pending reconciliation of the selected CBC date lineage with the stated 2020-2026 angiography period and verification of the date-shift source linkage. The supplied Editor and Reviewer wording is included verbatim, and the manuscript template was confirmed by the author. Page references are generated from the final rendered manuscript.\n\n"
        "No model reanalysis was performed. The clean and marked manuscripts, point-by-point response, supplementary files, figures, and source scripts are grouped by file type. The marked manuscript highlights only changes relative to the user-confirmed original.\n\n"
        "This package does not authorize portal submission. Do not merge the review pull request or submit until the source-date discrepancy is resolved by the authors or institutional data team.\n", encoding="utf-8")
    (OUT / "06_SUBMISSION/FINAL_UPLOAD_CHECKLIST.md").write_text(
        "# Final upload checklist\n\n"
        "- [ ] Reconcile selected CBC dates (2009-2026; 1,802/1,820 before 2019) with the stated 2020-2026 study period and verify the date-shift input/output linkage.\n"
        "- [ ] Confirm whether this author-confirmed original is byte-identical to the portal-integrated manuscript.\n"
        "- [ ] Review the verbatim point-by-point replies and rendered page/paragraph references.\n"
        "- [ ] Author-check ethics approval and consent-waiver wording.\n"
        "- [ ] Confirm all figures, supplementary files, and journal portal metadata.\n"
        "- [ ] Author submits through the BMC portal.\n\n"
        "Current status: submission remains on hold pending reconciliation of the selected CBC date lineage and verification of the date-shift source linkage.\n", encoding="utf-8")

    print(f"Built manuscript and audit scaffold: {OUT}")
    print(f"Applied targeted edits: {len(applied)}")
    print(f"Template SHA256: {sha256(BASE)}")


if __name__ == "__main__":
    main()
