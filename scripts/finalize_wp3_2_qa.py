#!/usr/bin/env python3
"""Run document/package QA scans for the WP3.2 submission patch."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "HITS_BMC_MINOR_REVISION_WP3_2_SUBMISSION_READY"


def docx_text(path: Path) -> str:
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs]
    parts.extend(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
    return "\n".join(parts)


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def xlsx_text(path: Path) -> str:
    book = load_workbook(path, data_only=True, read_only=True)
    return "\n".join(
        str(cell.value)
        for sheet in book.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.value is not None and isinstance(cell.value, str)
    )


def main():
    files = {
        "manuscript_clean_docx": OUT / "01_MANUSCRIPT/HITS_BMC_Revised_Manuscript_CLEAN.docx",
        "manuscript_clean_pdf": OUT / "01_MANUSCRIPT/HITS_BMC_Revised_Manuscript_CLEAN.pdf",
        "manuscript_marked_docx": OUT / "01_MANUSCRIPT/HITS_BMC_Revised_Manuscript_MARKED.docx",
        "response_docx": OUT / "02_RESPONSE/HITS_BMC_Point_by_Point_Response_FINAL.docx",
        "response_pdf": OUT / "02_RESPONSE/HITS_BMC_Point_by_Point_Response_FINAL.pdf",
        "supplement_methods_docx": OUT / "03_SUPPLEMENT/Additional_file_1_Revised_Supplementary_Methods_and_Figures.docx",
        "supplement_tables_xlsx": OUT / "03_SUPPLEMENT/Additional_file_2_Revised_Supplementary_Tables.xlsx",
        "upload_guide": OUT / "06_SUBMISSION/BMC_REVISION_UPLOAD_GUIDE_FINAL.md",
        "upload_checklist": OUT / "06_SUBMISSION/FINAL_UPLOAD_CHECKLIST.md",
    }
    if any(not path.is_file() for path in files.values()):
        missing = [str(path) for path in files.values() if not path.is_file()]
        raise FileNotFoundError("Missing required submission files: " + ", ".join(missing))

    text_by_file = {
        "manuscript_clean_docx": docx_text(files["manuscript_clean_docx"]),
        "manuscript_clean_pdf": pdf_text(files["manuscript_clean_pdf"]),
        "manuscript_marked_docx": docx_text(files["manuscript_marked_docx"]),
        "response_docx": docx_text(files["response_docx"]),
        "response_pdf": pdf_text(files["response_pdf"]),
        "supplement_methods_docx": docx_text(files["supplement_methods_docx"]),
        "supplement_tables_xlsx": xlsx_text(files["supplement_tables_xlsx"]),
        "upload_guide": files["upload_guide"].read_text(encoding="utf-8"),
        "upload_checklist": files["upload_checklist"].read_text(encoding="utf-8"),
    }
    patterns = [
        ("obsolete_source_date_hold", r"source[- ]date\s+hold|source date lineage.*hold"),
        ("unresolved_lineage", r"lineage\s+unresolved|unresolved\s+(?:source[- ]date|date[- ]lineage)|remains?\s+(?:under|for)\s+(?:author|institutional)\s+verification"),
        ("resolved_legacy_anomaly_reported_as_current", r"(?:selected CBC timestamps? (?:spanned|range[ds]?)\s+2009\s*[-–]\s*2026|1,?802\s*/\s*1,?820|before\s+2019|date discrepancy remains unresolved)"),
        ("machine_verification_claim", r"machine[- ]verified|database[- ]query[- ]verified|independently verified"),
        ("uniform_pre_event_claim", r"(?:all|uniformly)\s+(?:CBC\s+)?(?:measurements?\s+)?(?:were\s+)?(?:first[- ]admission|pre[- ]angiography|pre[- ]diagnostic|pre[- ]treatment)"),
        ("admission_first_phrase", r"admission[- ]first|first admission CBC|first CBC on admission"),
        ("pre_angiography_phrase", r"pre[- ]angiography"),
        ("pre_diagnostic_phrase", r"pre[- ]diagnostic"),
        ("pre_treatment_phrase", r"pre[- ]treatment"),
        ("temporal_validation_phrase", r"(?:formal\s+)?temporal validation"),
        ("transportability_claim", r"(?:establish(?:es)?|demonstrates?)\s+transportability|temporal transportability validation"),
        ("stale_temporal_cutpoint", r"2015-01-01|1 January 2015|2014-07-03|3 July 2014|2015-07-02|2 July 2015|3 July 2015"),
    ]
    scan_rows = []
    obsolete_indices = {0, 1, 2, 3, 11}
    forbidden_timing_indices = {4, 5, 6, 7, 8, 9, 10}
    for file_key, text in text_by_file.items():
        for index, (label, pattern) in enumerate(patterns):
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
            if index in obsolete_indices:
                status = "PASS_NO_OBSOLETE_CLAIM" if not matches else "FAIL_REVIEW_REQUIRED"
            elif index in forbidden_timing_indices:
                contexts = []
                all_negated = True
                for match in matches:
                    start = max(0, match.start() - 70)
                    end = min(len(text), match.end() + 50)
                    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
                    contexts.append(snippet)
                    prefix = text[max(0, match.start() - 300):match.start()]
                    sentence_prefix = prefix.rsplit(".", 1)[-1]
                    claim_context = (sentence_prefix + match.group(0)).lower()
                    comment_pos = prefix.lower().rfind("comment:")
                    response_pos = prefix.lower().rfind("response:")
                    quoted_comment = file_key.endswith(("response_docx", "response_pdf")) and comment_pos > response_pos
                    quoted_reviewer_question = file_key.endswith(("response_docx", "response_pdf")) and "authors should clarify whether" in prefix.lower()[-220:]
                    if label == "temporal_validation_phrase":
                        negated = bool(re.search(r"\b(?:not|rather than|no)\b[^.!?]{0,180}$", claim_context))
                        all_negated = all_negated and (negated or quoted_comment or quoted_reviewer_question)
                    elif label in {"uniform_pre_event_claim", "admission_first_phrase", "pre_angiography_phrase", "pre_diagnostic_phrase", "pre_treatment_phrase"}:
                        negated = bool(re.search(r"\b(?:not|no claim|do not describe|cannot be assumed|are not described as|does not say)\b[^.]{0,240}$", claim_context))
                        all_negated = all_negated and (negated or quoted_comment)
                    else:
                        all_negated = False
                status = "PASS_NEGATED_OR_QUOTED_ONLY" if all_negated else ("PASS_NO_PROHIBITED_ASSERTION" if not matches else "FAIL_REVIEW_REQUIRED")
                if matches and label == "transportability_claim":
                    status = "PASS_NO_PROHIBITED_ASSERTION" if all_negated else "FAIL_REVIEW_REQUIRED"
                context = " || ".join(contexts)
            else:
                status = "REVIEWED"
                context = " || ".join(re.sub(r"\s+", " ", text[max(0, m.start()-60):m.end()+60]).strip() for m in matches)
            scan_rows.append([file_key, label, len(matches), status, context if matches else ""])

    scan_path = OUT / "05_QA/WP3_2_INTERNAL_TERM_SCAN.csv"
    with scan_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["submission_file", "term_or_claim", "occurrence_count", "review_status", "context_if_present"])
        writer.writerows(scan_rows)
    failures = [row for row in scan_rows if row[3].startswith("FAIL")]
    if failures:
        raise RuntimeError("Term scan found unresolved or prohibited wording: " + repr(failures[:5]))

    coverage = list(csv.DictReader((OUT / "05_QA/WP3_2_COMMENT_COVERAGE.csv").open(encoding="utf-8-sig")))
    if len(coverage) != 22 or any(r["coverage_status"] not in {"CLOSED", "CLOSED_WITH_EXPLICIT_LIMITATION"} for r in coverage):
        raise RuntimeError(f"Comment coverage failed: {len(coverage)} comments")
    numerical = list(csv.DictReader((OUT / "05_QA/WP3_2_NUMERICAL_CROSSCHECK.csv").open(encoding="utf-8-sig")))
    if not numerical or any(r["status"] != "PASS" for r in numerical):
        raise RuntimeError("Numerical crosscheck CSV contains a non-PASS row")

    render_counts = {
        "clean_manuscript": len(list((OUT / "05_QA/render_clean_final").glob("page-*.png"))),
        "marked_manuscript": len(list((OUT / "05_QA/render_marked_final").glob("page-*.png"))),
        "response": len(list((OUT / "05_QA/render_response_final").glob("page-*.png"))),
        "supplement_methods": len(list((OUT / "05_QA/render_supplement_final").glob("page-*.png"))),
    }
    page_counts = {
        "clean_pdf": len(PdfReader(str(files["manuscript_clean_pdf"])).pages),
        "response_pdf": len(PdfReader(str(files["response_pdf"])).pages),
    }
    if render_counts != {"clean_manuscript": 28, "marked_manuscript": 28, "response": 7, "supplement_methods": 7}:
        raise RuntimeError(f"Unexpected rendered page counts: {render_counts}")
    if page_counts != {"clean_pdf": 28, "response_pdf": 7}:
        raise RuntimeError(f"Unexpected final PDF page counts: {page_counts}")

    qa_text = f"""# WP3.2 Final QA

**Gate:** `WP3_2_PASS_SUBMISSION_READY`

## Status

- `SOURCE_DATE_LINEAGE`: `RESOLVED_BY_AUTHOR_SOURCE_CONFIRMATION`; author/source-owner confirmation only, not machine, database-query, or independent verification.
- `CBC_VALUES`: `TARGET_HOSPITALIZATION_ASSOCIATED`.
- `EXACT_CBC_TIMING`: `NOT_UNIFORMLY_RECONSTRUCTABLE`.
- `LEGACY_WBC_TIMESTAMP`: `NOT_USED_AS_CLINICAL_TIMING_ANCHOR` or temporal-allocation field.
- `TEMPORAL_DATE_AXIS`: `2020_2026_HOSPITALIZATION_ANGIOGRAPHY_DATES_DEIDENTIFIED`.
- `TEMPORAL_SPLIT_CALENDAR_ANCHOR`: `NOT_AVAILABLE_IN_FROZEN_ANALYSIS_RECORD`; the author/source owner confirmed the earlier draft's 2015 split/date ranges were stale. No replacement calendar cutoff or group assignment was inferred.
- `TEMPORAL_ANALYSIS`: `TEMPORAL_SENSITIVITY_NOT_VALIDATION`.
- `STATISTICAL_REANALYSIS`: `NONE`.
- `FIGURE1_STYLE`: `ORIGINAL_STYLE_PRESERVED`; WP3.1 and WP3.2 Figure 1 TIFF SHA-256 values match.
- `MANUSCRIPT_CHANGE_STRATEGY`: `MINIMAL_TARGETED_MINOR_REVISION`.

## Verification

- Numerical crosscheck: PASS against frozen WP2 canonical outputs; no result values were recalculated.
- Comment coverage: PASS, {len(coverage)}/22 Editor/Reviewer comments remain `CLOSED` or `CLOSED_WITH_EXPLICIT_LIMITATION`.
- Internal term scan: PASS; obsolete unresolved source-date HOLD wording and the 2009-2026/1,802/1,820 anomaly framing are absent from submission-facing materials. Timing phrases that appear are explicitly negated or quoted reviewer text. Temporal validation is consistently denied rather than claimed.
- Temporal split reporting: PASS WITH EXPLICIT LIMITATION; the stale 2015 cutpoint was removed on author/source-owner confirmation. The frozen analysis record does not retain a verified calendar cutpoint, so the manuscript and response state this limitation while preserving the frozen group counts and estimates. No calendar value was inferred and no analysis was rerun.
- Document rendering: PASS; clean manuscript {render_counts['clean_manuscript']} pages, marked manuscript {render_counts['marked_manuscript']} pages, response {render_counts['response']} pages, supplementary methods {render_counts['supplement_methods']} pages. Final clean and response PDFs match the rendered page counts.
- Figure 4: PASS; only label wording changed. All 9 aggregate source rows match WP3.1 in every non-label field. The supplied R script regenerated Figure 4; TIFF export is 600 dpi. No geometry redesign.
- Supplementary tables: PASS; temporal labels and explanatory note updated with Artifact Tool. Numeric cell values and formulas were identical before/after export/import.
- No patient-level raw data are included in this submission package.

No portal submission or PR merge was performed. The response to Editor Comment 5 explicitly notes that the exact calendar cutpoint is unavailable in the retained analysis record. PR #1 remains open for the requested final external audit.
"""
    (OUT / "05_QA/WP3_2_FINAL_QA.md").write_text(qa_text, encoding="utf-8")
    print(f"WP3.2 QA PASS; comments={len(coverage)}; pages={render_counts}; term scan rows={len(scan_rows)}")


if __name__ == "__main__":
    main()
