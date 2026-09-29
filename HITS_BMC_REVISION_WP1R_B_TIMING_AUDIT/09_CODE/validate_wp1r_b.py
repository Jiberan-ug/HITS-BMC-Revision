#!/usr/bin/env python3
"""Validate the aggregate-only WP1R-B timing handoff."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "00_EXECUTIVE/WP1R_B_EXECUTIVE_SUMMARY.md",
    "00_EXECUTIVE/WP1R_B_GATE.md",
    "01_SOURCE_LINKAGE/TIMING_SOURCE_INVENTORY.csv",
    "01_SOURCE_LINKAGE/INDEX_EPISODE_RECONSTRUCTION_METHOD.md",
    "01_SOURCE_LINKAGE/ALTERNATIVE_LINKAGE_SOURCE_AUDIT.csv",
    "02_CBC/CBC_MEASUREMENT_SELECTION_RULE_FINAL.md",
    "02_CBC/CBC_TIMING_VERIFICATION_SUMMARY.csv",
    "03_FIBRINOGEN/FIBRINOGEN_TIMING_VERIFICATION_SUMMARY.csv",
    "04_PHENOTYPE/TIMING_AVAILABILITY_BY_PHENOTYPE.csv",
    "04_PHENOTYPE/DIFFERENTIAL_TIMING_AVAILABILITY_AUDIT.md",
    "05_MASTER_SUMMARY/TIMING_VERIFICATION_MASTER_SUMMARY.csv",
    "06_STUDY_PERIOD/STUDY_PERIOD_FINAL_AUDIT.md",
    "07_TEMPORAL/TEMPORAL_ANALYSIS_FINAL_DECISION_AFTER_TIMING_AUDIT.md",
    "08_REVIEWER_FACTS/EDITOR_COMMENT_1_FACT_PATTERN.md",
    "08_REVIEWER_FACTS/REVIEWER1_TIMING_FACT_PATTERN.md",
    "09_CODE/wp1r_b_timing_audit.py",
    "09_CODE/validate_wp1r_b.py",
    "09_CODE/run.log",
    "09_CODE/SOURCE_HASHES.csv",
    "09_CODE/AUDIT_METRICS.json",
]


def read_rows(relpath: str) -> list[dict[str, str]]:
    with (ROOT / relpath).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    failures: list[str] = []
    missing = [rel for rel in REQUIRED if not (ROOT / rel).is_file()]
    if missing:
        failures.append(f"Missing required files: {missing}")

    master = read_rows("05_MASTER_SUMMARY/TIMING_VERIFICATION_MASTER_SUMMARY.csv")
    expected = {"Total": 1820, "AMI": 453, "non-AMI CAD": 1367}
    for row in master:
        group = row["analysis_group"]
        if int(row["n_total"]) != expected[group]:
            failures.append(f"Unexpected cohort N for {group}")
        if int(row["any_defensible_index_episode_timing_n"]) != 0:
            failures.append(f"Unexpected linked timing count for {group}")
        if int(row["timing_unverified_n"]) != expected[group]:
            failures.append(f"Unexpected unverified count for {group}")
        if int(row["cbc_same_index_hospitalization_interpretable_denominator_n"]) != 0:
            failures.append(f"Unexpected same-stay denominator for {group}")
        if int(row["cbc_before_angiography_interpretable_denominator_n"]) != 0:
            failures.append(f"Unexpected angiography timing denominator for {group}")

    fbg = read_rows("03_FIBRINOGEN/FIBRINOGEN_TIMING_VERIFICATION_SUMMARY.csv")
    total_fbg = [row for row in fbg if row["analysis_group"] == "Total"]
    fbg_metrics = {row["metric"]: row for row in total_fbg}
    if int(fbg_metrics["Fibrinogen and CBC timestamps paired"]["numerator_n"]) != 1707:
        failures.append("Fibrinogen/CBC paired count is not 1,707")
    date_partition = sum(int(fbg_metrics[name]["numerator_n"]) for name in (
        "Fibrinogen calendar date before CBC calendar date",
        "Fibrinogen on same calendar date as CBC",
        "Fibrinogen calendar date after CBC calendar date",
    ))
    exact_partition = sum(int(fbg_metrics[name]["numerator_n"]) for name in (
        "Fibrinogen exact timestamp before CBC",
        "Fibrinogen exact timestamp equal to CBC",
        "Fibrinogen exact timestamp after CBC",
    ))
    if date_partition != 1707 or exact_partition != 1707:
        failures.append("Fibrinogen timing partitions do not reconcile to the paired denominator")

    denied_headers = re.compile(r"^(patient_sn|patient_id|patient_hash|research_patient_id|name|mrn|inpatient_no_id|diagnosis_text)$", re.I)
    privacy_hits: list[str] = []
    row_level_extensions = {".xlsx", ".xls", ".sav", ".dta", ".parquet", ".sqlite", ".db"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in row_level_extensions:
            privacy_hits.append(f"Unexpected clinical-data extension: {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".csv", ".tsv"}:
            with path.open(encoding="utf-8", newline="") as handle:
                header = next(csv.reader(handle), [])
            if any(denied_headers.match(col.strip()) for col in header):
                privacy_hits.append(f"Patient-level identifier column: {path.relative_to(ROOT)}")
        if path.suffix.lower() in {".md", ".csv", ".json", ".log", ".py", ".txt"}:
            content = path.read_text(encoding="utf-8", errors="replace")
            if ("/" + "Users" + "/") in content:
                privacy_hits.append(f"Local absolute path in package: {path.relative_to(ROOT)}")
            if re.search(r"AMI_P_[0-9a-f]{8,}|\bP\d{4,}\b", content):
                privacy_hits.append(f"Patient audit token-like value in package: {path.relative_to(ROOT)}")
    if privacy_hits:
        failures.extend(privacy_hits)

    run_log = (ROOT / "09_CODE/run.log").read_text(encoding="utf-8")
    for phrase in ("No patient identifier", "No model fitting", "all remain UNKNOWN"):
        if phrase not in run_log:
            failures.append(f"Run log missing required boundary: {phrase}")

    report = {
        "status": "PASS" if not failures else "FAIL",
        "required_files_n": len(REQUIRED),
        "cohort_n": expected["Total"],
        "ami_n": expected["AMI"],
        "non_ami_cad_n": expected["non-AMI CAD"],
        "timing_unverified_n": 1820,
        "fibrinogen_cbc_pairs_n": 1707,
        "privacy_hits_n": len(privacy_hits),
        "failures": failures,
        "models_refit": False,
        "manuscript_edited": False,
    }
    (ROOT / "09_CODE/QA_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
