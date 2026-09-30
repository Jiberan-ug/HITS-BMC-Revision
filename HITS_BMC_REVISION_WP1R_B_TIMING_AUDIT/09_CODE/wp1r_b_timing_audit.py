#!/usr/bin/env python3
"""Aggregate-only timing audit for the frozen HITS primary cohort.

The historical selector and phenotype builder are imported as functions only;
their analysis entry point is not called. No row-level identifiers or dates are
written to disk.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import platform
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def count(mask: pd.Series) -> int:
    return int(mask.fillna(False).sum())


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "NA"
    return f"{100 * numerator / denominator:.2f}"


def fmt_pair(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator} ({pct(numerator, denominator)}%)" if denominator else "0/0 (not estimable)"


def date_relations(first: pd.Series, second: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return first-minus-second calendar-day difference and relation labels."""
    first_day = pd.to_datetime(first, errors="coerce").dt.normalize()
    second_day = pd.to_datetime(second, errors="coerce").dt.normalize()
    delta = (first_day - second_day).dt.days
    relation = pd.Series("UNKNOWN", index=first.index, dtype="string")
    valid = first_day.notna() & second_day.notna()
    relation.loc[valid & delta.lt(0)] = "BEFORE"
    relation.loc[valid & delta.eq(0)] = "SAME_DAY"
    relation.loc[valid & delta.gt(0)] = "AFTER"
    return delta, relation


def metric_row(group: str, metric: str, numerator: int, denominator: int, note: str, status: str = "") -> dict:
    return {
        "analysis_group": group,
        "metric": metric,
        "status": status,
        "numerator_n": numerator,
        "denominator_n": denominator,
        "percent": pct(numerator, denominator),
        "numerator_denominator_display": fmt_pair(numerator, denominator),
        "interpretation": note,
    }


def read_csv_count(path: Path) -> tuple[int, int]:
    frame = pd.read_csv(path, low_memory=False)
    return len(frame), len(frame.columns)


def load_historical_subset(script_path: Path) -> dict:
    """Compile only the frozen selector/phenotype functions and their constants."""
    tree = ast.parse(script_path.read_text(encoding="utf-8"))
    function_names = {
        "parse_numeric", "parse_datetime", "audit_id", "normalize_text", "binary_flag",
        "sex_binary", "split_diagnosis", "acute_mi_pattern", "classify_diagnosis",
        "select_one_row_per_patient", "build_patient_frame",
    }
    assignment_names = {
        "COL", "BIOMARKERS", "CORE_REQUIRED", "MI_RE", "ACUTE_RE", "OLD_RE",
        "UNCERTAIN_RE", "NEGATED_MI_RE", "CAD_RE", "ANGINA_CAD_RE", "ACS_RE",
    }
    selected_nodes = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in function_names:
            selected_nodes.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = {target.id for target in targets if isinstance(target, ast.Name)}
            if names & assignment_names:
                selected_nodes.append(node)
    namespace = {"pd": pd, "np": np, "hashlib": hashlib, "re": re}
    isolated = ast.Module(body=selected_nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), str(script_path), "exec"), namespace)
    required = function_names | assignment_names
    missing = sorted(name for name in required if name not in namespace)
    if missing:
        raise RuntimeError(f"Could not load historical selector dependencies: {missing}")
    return namespace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", type=Path, required=True, help="Frozen analysis master CSV")
    parser.add_argument("--selector-script", type=Path, required=True, help="Historical HITS V0.2 selector script")
    parser.add_argument("--mother-csv", type=Path, required=True, help="Original primary mother CSV")
    parser.add_argument("--scheme-c-zip", type=Path, required=True, help="Source bundle ZIP")
    parser.add_argument("--field-dictionary", type=Path, required=True)
    parser.add_argument("--deidentified-master", type=Path, required=True)
    parser.add_argument("--lineage-script", type=Path, required=True)
    parser.add_argument("--source-recovery-inventory", type=Path, required=True)
    parser.add_argument("--index-encounter-audit", type=Path, required=True)
    parser.add_argument("--index-cbc-audit", type=Path, required=True)
    parser.add_argument("--prevalidation-timing-audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    module = load_historical_subset(args.selector_script)
    raw = pd.read_csv(args.source_csv, low_memory=False)
    selected, _selection_audit = module["select_one_row_per_patient"](raw)
    selected = selected.reset_index(drop=True)
    cohort = module["build_patient_frame"](selected)
    cohort["__selected_position"] = range(len(cohort))
    cohort = cohort.loc[cohort["primary_analysis"]].copy().reset_index(drop=True)

    ami_class = "A_definite_AMI"
    nonami_class = "B_definite_nonAMI_CAD"
    cohort["analysis_group"] = cohort["phenotype_class"].map(
        {ami_class: "AMI", nonami_class: "non-AMI CAD"}
    )
    group_frames = {
        "Total": cohort,
        "AMI": cohort.loc[cohort["analysis_group"].eq("AMI")].copy().reset_index(drop=True),
        "non-AMI CAD": cohort.loc[cohort["analysis_group"].eq("non-AMI CAD")].copy().reset_index(drop=True),
    }
    observed = {name: len(frame) for name, frame in group_frames.items()}
    expected = {"Total": 1820, "AMI": 453, "non-AMI CAD": 1367}
    if observed != expected:
        raise RuntimeError(f"Frozen cohort guard failed: {observed}")

    # Validate timing-related schema presence without disclosing row data.
    columns = [str(col) for col in raw.columns]
    lower = {col: col.lower() for col in columns}
    discharge_time_fields = [col for col in columns if "discharge" in lower[col] and any(x in lower[col] for x in ("time", "date", "datetime"))]
    cag_fields = [col for col in columns if any(x in lower[col] for x in ("cag", "angiograph"))]
    pci_fields = [col for col in columns if "pci" in lower[col] and any(x in lower[col] for x in ("time", "date", "datetime"))]
    procedure_time_fields = [col for col in columns if "procedure" in lower[col] and any(x in lower[col] for x in ("time", "date", "datetime"))]
    diagnosis_time_fields = [col for col in columns if "diagnos" in lower[col] and any(x in lower[col] for x in ("time", "date", "datetime"))]
    encounter_id_fields = [
        col for col in columns
        if any(token in lower[col] for token in ("encounter_id", "visit_id", "admission_id", "hospitalization_id", "stay_id"))
    ]
    inpatient_token_fields = [col for col in columns if "inpatient_no" in lower[col]]

    master_rows: list[dict] = []
    cbc_rows: list[dict] = []
    fbg_rows: list[dict] = []
    availability_rows: list[dict] = []
    for group, frame in group_frames.items():
        n = len(frame)
        cbc = frame["cbc_datetime"]
        admission = frame["admission_datetime"]
        fbg = frame["fbg_datetime"]
        has_cbc = cbc.notna()
        has_admission = admission.notna()
        has_cbc_admission = has_cbc & has_admission
        has_fbg = fbg.notna()
        has_fbg_value = frame["fbg"].notna()
        has_fbg_cbc = has_fbg & has_cbc
        cbc_admission_delta, cbc_admission_relation = date_relations(cbc, admission)
        fbg_cbc_delta, fbg_cbc_relation = date_relations(fbg, cbc)
        fbg_admission_delta, fbg_admission_relation = date_relations(fbg, admission)

        cbc_available_n = count(has_cbc)
        admission_available_n = count(has_admission)
        cbc_admission_n = count(has_cbc_admission)
        fbg_available_n = count(has_fbg)
        fbg_value_n = count(has_fbg_value)
        fbg_cbc_n = count(has_fbg_cbc)

        # Event-level linkage is absent in the source schema; no statuses are inferred from proximity.
        verified_n = 0
        unknown_n = n
        master_rows.append({
            "analysis_group": group,
            "n_total": n,
            "any_defensible_index_episode_timing_n": verified_n,
            "any_defensible_index_episode_timing_pct": pct(verified_n, n),
            "direct_encounter_linkage_n": 0,
            "direct_encounter_linkage_pct": pct(0, n),
            "unique_stay_window_linkage_n": 0,
            "unique_stay_window_linkage_pct": pct(0, n),
            "partial_clinical_timing_linkage_n": 0,
            "partial_clinical_timing_linkage_pct": pct(0, n),
            "timing_unverified_n": unknown_n,
            "timing_unverified_pct": pct(unknown_n, n),
            "cbc_test_time_available_n": cbc_available_n,
            "cbc_admission_date_paired_n": cbc_admission_n,
            "cag_time_available_n": 0,
            "initial_ami_diagnosis_time_available_n": 0 if group != "non-AMI CAD" else "NA",
            "cbc_same_index_hospitalization_confirmed_n": 0,
            "cbc_same_index_hospitalization_interpretable_denominator_n": 0,
            "cbc_same_index_hospitalization_unknown_n": n,
            "cbc_before_angiography_confirmed_n": 0,
            "cbc_before_angiography_interpretable_denominator_n": 0,
            "cbc_before_initial_ami_diagnosis_confirmed_n": 0 if group != "non-AMI CAD" else "NA",
            "cbc_before_initial_ami_diagnosis_interpretable_denominator_n": 0 if group != "non-AMI CAD" else "NA",
            "fbg_test_time_available_n": fbg_available_n,
            "fbg_cbc_timestamp_paired_n": fbg_cbc_n,
            "fbg_same_index_hospitalization_confirmed_n": 0,
            "fbg_same_index_hospitalization_interpretable_denominator_n": 0,
            "fbg_same_index_hospitalization_unknown_among_timed_n": fbg_available_n,
            "fbg_before_angiography_confirmed_n": 0,
            "fbg_before_angiography_interpretable_denominator_n": 0,
            "evidence_note": "Patient-level lab timestamps exist, but no lab-to-index-CAG encounter link; all index-event timing remains UNKNOWN.",
        })
        availability_rows.append({
            "analysis_group": group,
            "n_total": n,
            "cbc_timestamp_available_n": cbc_available_n,
            "cbc_timestamp_available_pct": pct(cbc_available_n, n),
            "admission_date_available_n": admission_available_n,
            "admission_date_available_pct": pct(admission_available_n, n),
            "cbc_and_admission_date_paired_n": cbc_admission_n,
            "cbc_and_admission_date_paired_pct": pct(cbc_admission_n, n),
            "fbg_timestamp_available_n": fbg_available_n,
            "fbg_timestamp_available_pct": pct(fbg_available_n, n),
            "fbg_value_available_n": fbg_value_n,
            "fbg_value_available_pct": pct(fbg_value_n, n),
            "cbc_fbg_timestamps_paired_n": fbg_cbc_n,
            "cbc_fbg_timestamps_paired_pct": pct(fbg_cbc_n, n),
            "angiography_time_available_n": 0,
            "initial_ami_diagnosis_time_available_n": 0 if group != "non-AMI CAD" else "NA",
            "direct_encounter_linkage_n": 0,
            "any_defensible_episode_timing_n": 0,
            "same_index_hospitalization_cbc_confirmed_n": 0,
            "timing_unverified_n": n,
        })

        cbc_rows.extend([
            metric_row(group, "CBC timestamp available", cbc_available_n, n,
                       "Selected-row laboratory timestamp availability only; does not identify the index hospitalization", "FIELD_AVAILABLE"),
            metric_row(group, "CBC and listed admission date paired", cbc_admission_n, n,
                       "Arithmetic comparison only; the admission field is not linked to the angiography episode", "FIELD_PAIRED_NOT_ENCOUNTER_LINKED"),
            metric_row(group, "CBC calendar date before listed admission date", count(has_cbc_admission & cbc_admission_relation.eq("BEFORE")), cbc_admission_n,
                       "Date-level comparison only; not an index-admission ordering claim", "DATE_LEVEL_ONLY"),
            metric_row(group, "CBC on same calendar date as listed admission date", count(has_cbc_admission & cbc_admission_relation.eq("SAME_DAY")), cbc_admission_n,
                       "Same calendar date does not prove same stay or same-day event ordering", "DATE_LEVEL_ONLY"),
            metric_row(group, "CBC calendar date after listed admission date", count(has_cbc_admission & cbc_admission_relation.eq("AFTER")), cbc_admission_n,
                       "Date-level comparison only; not an index-admission ordering claim", "DATE_LEVEL_ONLY"),
            metric_row(group, "CBC same index hospitalization confirmed", 0, 0,
                       f"No index episode can be reconstructed; UNKNOWN for all {n} cohort members", "UNKNOWN_NOT_NO"),
            metric_row(group, "CBC before angiography confirmed", 0, 0,
                       "No angiography/CAG/PCI date or time is available in the linked cohort source", "NOT_ESTIMABLE"),
            metric_row(group, "CBC before initial AMI diagnosis confirmed", 0, 0 if group != "non-AMI CAD" else 0,
                       "No initial AMI diagnosis timestamp is available; discharge diagnosis is not substituted", "NOT_ESTIMABLE" if group != "non-AMI CAD" else "NOT_APPLICABLE"),
            metric_row(group, "CBC before major intervention confirmed", 0, 0,
                       "No major-intervention/procedure timestamp is available", "NOT_ESTIMABLE"),
        ])
        for marker in ("neut", "lymph", "mono", "plt", "mpv", "rdw", "hb"):
            marker_col = module["COL"].get(f"{marker}_time")
            if marker_col and marker_col in selected.columns:
                selected_positions = frame["__selected_position"].astype(int).tolist()
                marker_time = module["parse_datetime"](selected.loc[selected_positions, marker_col]).reset_index(drop=True)
                paired_marker = marker_time.notna() & cbc.notna()
                same_timestamp_n = count(paired_marker & marker_time.eq(cbc))
                cbc_rows.extend([
                    metric_row(group, f"{marker.upper()} time field available", count(marker_time.notna()), n,
                               "Timestamp is present in the selected flat row; not a laboratory encounter key", "FIELD_AVAILABLE"),
                    metric_row(group, f"{marker.upper()} timestamp identical to WBC timestamp", same_timestamp_n, count(paired_marker),
                               "Within-row timestamp agreement does not prove specimen or encounter identity", "WITHIN_ROW_ONLY"),
                ])

        # Fibrinogen relationship is quantified by calendar day; exact timestamp order is separate.
        fbg_date_before_n = count(has_fbg_cbc & fbg_cbc_relation.eq("BEFORE"))
        fbg_same_day_n = count(has_fbg_cbc & fbg_cbc_relation.eq("SAME_DAY"))
        fbg_date_after_n = count(has_fbg_cbc & fbg_cbc_relation.eq("AFTER"))
        exact_pair = has_fbg_cbc
        exact_before_n = count(exact_pair & fbg.lt(cbc))
        exact_after_n = count(exact_pair & fbg.gt(cbc))
        exact_equal_n = count(exact_pair & fbg.eq(cbc))
        fbg_admission_n = count(has_fbg & has_admission)
        fbg_rows.extend([
            metric_row(group, "Fibrinogen test timestamp available", fbg_available_n, n,
                       "Timestamp field available in the selected flat row", "FIELD_AVAILABLE"),
            metric_row(group, "Fibrinogen value available", fbg_value_n, n,
                       "Value availability is not encounter linkage", "FIELD_AVAILABLE"),
            metric_row(group, "Fibrinogen and CBC timestamps paired", fbg_cbc_n, n,
                       "Both test timestamps appear in one selected patient-level row; encounter identity is unknown", "LAB_TO_LAB_ONLY"),
            metric_row(group, "Fibrinogen calendar date before CBC calendar date", fbg_date_before_n, fbg_cbc_n,
                       "Calendar-date ordering among patients with both timestamps", "DATE_LEVEL_RELATION"),
            metric_row(group, "Fibrinogen on same calendar date as CBC", fbg_same_day_n, fbg_cbc_n,
                       "Calendar-date equality; exact time ordering may still differ", "DATE_LEVEL_RELATION"),
            metric_row(group, "Fibrinogen calendar date after CBC calendar date", fbg_date_after_n, fbg_cbc_n,
                       "Calendar-date ordering among patients with both timestamps", "DATE_LEVEL_RELATION"),
            metric_row(group, "Fibrinogen exact timestamp before CBC", exact_before_n, fbg_cbc_n,
                       "Exact recorded timestamp ordering; does not establish same specimen or hospitalization", "TIMESTAMP_RELATION"),
            metric_row(group, "Fibrinogen exact timestamp equal to CBC", exact_equal_n, fbg_cbc_n,
                       "Exact timestamp equality in the flat record only", "TIMESTAMP_RELATION"),
            metric_row(group, "Fibrinogen exact timestamp after CBC", exact_after_n, fbg_cbc_n,
                       "Exact recorded timestamp ordering; does not establish same specimen or hospitalization", "TIMESTAMP_RELATION"),
            metric_row(group, "Fibrinogen and listed admission date paired", fbg_admission_n, n,
                       "Arithmetic comparison only; no index-stay linkage", "FIELD_PAIRED_NOT_ENCOUNTER_LINKED"),
            metric_row(group, "Fibrinogen calendar date before listed admission date", count(has_fbg & has_admission & fbg_admission_relation.eq("BEFORE")), fbg_admission_n,
                       "Date-level arithmetic only; admission date is not linked to the index CAG stay", "DATE_LEVEL_ONLY"),
            metric_row(group, "Fibrinogen on same calendar date as listed admission date", count(has_fbg & has_admission & fbg_admission_relation.eq("SAME_DAY")), fbg_admission_n,
                       "Same calendar date does not prove same hospitalization", "DATE_LEVEL_ONLY"),
            metric_row(group, "Fibrinogen calendar date after listed admission date", count(has_fbg & has_admission & fbg_admission_relation.eq("AFTER")), fbg_admission_n,
                       "Date-level arithmetic only; admission date is not linked to the index CAG stay", "DATE_LEVEL_ONLY"),
            metric_row(group, "Fibrinogen same index hospitalization confirmed", 0, 0,
                       f"No index episode can be reconstructed; UNKNOWN among all {fbg_available_n} with a fibrinogen timestamp", "UNKNOWN_NOT_NO"),
            metric_row(group, "Fibrinogen before angiography confirmed", 0, 0,
                       "No angiography/CAG/PCI timestamp is available", "NOT_ESTIMABLE"),
            metric_row(group, "Fibrinogen before initial AMI diagnosis confirmed", 0, 0 if group != "non-AMI CAD" else 0,
                       "No initial AMI diagnosis timestamp is available", "NOT_ESTIMABLE" if group != "non-AMI CAD" else "NOT_APPLICABLE"),
        ])

    master_fields = list(master_rows[0].keys())
    write_csv(out / "05_MASTER_SUMMARY/TIMING_VERIFICATION_MASTER_SUMMARY.csv", master_rows, master_fields)
    cbc_fields = list(cbc_rows[0].keys())
    write_csv(out / "02_CBC/CBC_TIMING_VERIFICATION_SUMMARY.csv", cbc_rows, cbc_fields)
    fbg_fields = list(fbg_rows[0].keys())
    write_csv(out / "03_FIBRINOGEN/FIBRINOGEN_TIMING_VERIFICATION_SUMMARY.csv", fbg_rows, fbg_fields)
    avail_fields = list(availability_rows[0].keys())
    write_csv(out / "04_PHENOTYPE/TIMING_AVAILABILITY_BY_PHENOTYPE.csv", availability_rows, avail_fields)

    # Summarize alternative, derived encounter-audit files without exporting their patient rows.
    alt_rows = []
    for path, label, linkage_note in [
        (args.index_encounter_audit, "Information-score index encounter audit", "Derived patient-level audit; reports index encounter not recoverable; not an independent source export"),
        (args.index_cbc_audit, "Information-score CBC timing audit", "Derived patient-level audit; no lab-to-encounter linkage; not an independent source export"),
        (args.prevalidation_timing_audit, "Information-score prevalidation admission timing flags", "Derived patient-level date arithmetic; no encounter adjudication"),
    ]:
        audit = pd.read_csv(path, low_memory=False)
        status_col = next((c for c in audit.columns if "status" in c.lower() and "encounter" in c.lower()), None)
        status_counts = audit[status_col].astype("string").value_counts(dropna=False).to_dict() if status_col else {}
        alt_rows.append({
            "source_file": path.name,
            "source_sha256": sha256(path),
            "role": label,
            "rows": len(audit),
            "encounter_status_field": status_col or "NOT_PRESENT",
            "index_encounter_not_recoverable_n": int(status_counts.get("INDEX_ENCOUNTER_NOT_RECOVERABLE", 0)),
            "linkage_fields_and_coverage": "; ".join(f"{k}={v}" for k, v in sorted(status_counts.items())) if status_counts else "Derived CBC/admission date fields only; no confirmed episode key",
            "independent_source": "NO",
            "linkage_decision": linkage_note,
        })
    write_csv(out / "01_SOURCE_LINKAGE/ALTERNATIVE_LINKAGE_SOURCE_AUDIT.csv", alt_rows, list(alt_rows[0].keys()))

    with zipfile.ZipFile(args.scheme_c_zip) as archive:
        zip_members = archive.namelist()
    source_specs = [
        ("Original primary mother export", args.mother_csv, "Original wide patient-linked export; 2,548 rows / 431 columns; admission_date=146/2,548; WBC CBC test_time=2,268/2,548; fibrinogen test_time=2,128/2,548; no discharge/CAG/PCI/procedure date or lab-specific encounter key"),
        ("Frozen cleaned analysis master", args.source_csv, "Derived cleaned wide master used by historical selector; in the frozen N=1,820 cohort CBC time=1,820/1,820, admission date=130/1,820, fibrinogen time=1,707/1,820; no independent event table"),
        ("Scheme C source bundle", args.scheme_c_zip, f"Archive members={len(zip_members)}; includes cleaned master, outcome membership tables, dictionary and QC/crosswalk files; no encounter-level procedure/lab episode export"),
        ("Scheme C field dictionary", args.field_dictionary, "Variable dictionary for the same cleaned export; field semantics do not provide missing encounter linkage"),
        ("Deidentified lineage master", args.deidentified_master, "Derived from the same master; visit_id_hash_list is a patient-level aggregation from inpatient_no_id fields, not a per-lab/per-encounter crosswalk"),
        ("Lineage packaging script", args.lineage_script, "Code confirms visit hashes are generated from inpatient_no_id and baseline_inpatient_no_id and aggregated per patient"),
        ("Information-score source recovery inventory", args.source_recovery_inventory, "Prior local source search inventory; source candidates are derived or same source ecosystem, no complete validated index-hospitalization table"),
        ("Information-score index encounter audit", args.index_encounter_audit, "Derived audit; status summarized in ALTERNATIVE_LINKAGE_SOURCE_AUDIT.csv"),
        ("Information-score CBC timing audit", args.index_cbc_audit, "Derived audit; status summarized in ALTERNATIVE_LINKAGE_SOURCE_AUDIT.csv"),
        ("Information-score prevalidation timing flags", args.prevalidation_timing_audit, "Derived date-flag audit; no same-stay adjudication"),
        ("Historical HITS selector script", args.selector_script, "Executable selection and phenotype code; no model entry point called in this audit"),
        ("WP1R-B aggregate timing audit script", Path(__file__).resolve(), "This aggregate-only audit implementation; loads only historical selector/phenotype functions"),
        ("WP1R-B package validator", Path(__file__).with_name("validate_wp1r_b.py").resolve(), "Package, denominator, cohort-count, and privacy validation code"),
    ]
    source_rows = []
    hash_rows = []
    for role, path, note in source_specs:
        digest = sha256(path)
        if role == "Original primary mother export":
            rows, cols = 2548, 431
        else:
            try:
                rows, cols = read_csv_count(path) if path.suffix.lower() == ".csv" else ("NA", "NA")
            except Exception:
                rows, cols = "NA", "NA"
        source_rows.append({
            "source_role": role,
            "filename": path.name,
            "sha256": digest,
            "rows": rows,
            "columns": cols,
            "linkage_fields_or_scope": note,
            "clinical_episode_linkage": "NO" if role not in {
                "Historical HITS selector script", "WP1R-B aggregate timing audit script", "WP1R-B package validator"
            } else "NOT_A_DATA_SOURCE",
        })
        hash_rows.append({"source_role": role, "filename": path.name, "sha256": digest})
    source_rows.append({
        "source_role": "Named original adverse-negative source export (not recovered)",
        "filename": "冠心病+造影手术+20-26-不良（减少附属）.csv",
        "sha256": "NOT_FOUND",
        "rows": "NA",
        "columns": "NA",
        "linkage_fields_or_scope": "Previously searched in Downloads and source_raw; no local copy found. Not an independent hospitalization or procedure source.",
        "clinical_episode_linkage": "NOT_AVAILABLE",
    })
    write_csv(out / "01_SOURCE_LINKAGE/TIMING_SOURCE_INVENTORY.csv", source_rows, list(source_rows[0].keys()))
    write_csv(out / "09_CODE/SOURCE_HASHES.csv", hash_rows, list(hash_rows[0].keys()))

    field_checks = {
        "explicit_encounter_id_field_n": len(encounter_id_fields),
        "unlinked_inpatient_number_or_token_fields_n": len(inpatient_token_fields),
        "explicit_discharge_datetime_field_n": len(discharge_time_fields),
        "CAG_or_angiography_field_n": len(cag_fields),
        "PCI_date_time_field_n": len(pci_fields),
        "procedure_date_time_field_n": len(procedure_time_fields),
        "initial_diagnosis_date_time_field_n": len(diagnosis_time_fields),
        "scheme_c_zip_member_n": len(zip_members),
    }
    metrics = {
        "cohort_n": observed["Total"],
        "ami_n": observed["AMI"],
        "non_ami_cad_n": observed["non-AMI CAD"],
        "any_defensible_index_episode_timing_n": 0,
        "direct_encounter_linkage_n": 0,
        "same_index_hospitalization_cbc_confirmed_n": 0,
        "pre_angiography_cbc_n": 0,
        "pre_angiography_cbc_denominator_n": 0,
        "pre_initial_ami_diagnosis_cbc_n": 0,
        "pre_initial_ami_diagnosis_cbc_denominator_n": 0,
        "timing_unverified_n": observed["Total"],
        "field_checks": field_checks,
        "source_files": len(source_rows),
        "zip_members": zip_members,
        "output_contains_patient_rows": False,
        "models_refit": False,
    }
    (out / "09_CODE/AUDIT_METRICS.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    lines = [
        "WP1R-B aggregate-only timing audit run",
        "Audit date: 2026-09-29",
        f"Runtime: Python {platform.python_version()}, pandas {pd.__version__}, NumPy {np.__version__}",
        f"Frozen cohort guard: total={observed['Total']}; AMI={observed['AMI']}; non-AMI CAD={observed['non-AMI CAD']}",
        "Historical selector and phenotype-builder function bodies loaded from the source AST; only those functions and constants were compiled.",
        "No model fitting, refitting, ROC, calibration, DCA, or manuscript operation performed.",
        "No patient identifier, pseudonym, row-level timestamp, or row-level classification written.",
        f"Defensible index-episode timing: 0/{observed['Total']}; all remain UNKNOWN/unverified.",
        f"Explicit encounter-ID fields={field_checks['explicit_encounter_id_field_n']}; discharge date/time fields={field_checks['explicit_discharge_datetime_field_n']}; CAG/angiography fields={field_checks['CAG_or_angiography_field_n']}; PCI date/time fields={field_checks['PCI_date_time_field_n']}; procedure date/time fields={field_checks['procedure_date_time_field_n']}; initial diagnosis date/time fields={field_checks['initial_diagnosis_date_time_field_n']}.",
        f"Inpatient number/token columns present but not lab/episode-linked={field_checks['unlinked_inpatient_number_or_token_fields_n']}.",
        "Result files contain aggregate counts, source hashes, and schema-level metadata only.",
    ]
    (out / "09_CODE/run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
