#!/usr/bin/env python3
"""Regenerate only the authorized HITS BMC WP2 analyses.

Patient-level predictions are written only to a private local directory passed
with --local-predictions-dir. Public outputs contain aggregates only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd


EXPECTED_SOURCE_SHA256 = "f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660"
EXPECTED_V031_SHA256 = "b1dcc686e2399c07c8125c373a16264dafbc7adf4b6703c809e4765fd7cf5922"
EXPECTED_V02_SHA256 = "089924ec5a58d09c3e96bdedd2a9316690eebd3f70377a058760a90b267ad91a"
EXPECTED_PRIMARY_N = 1820
EXPECTED_AMI_N = 453
EXPECTED_FBG_CC_N = 1705
EXPECTED_FBG_CC_AMI_N = 426
EXPECTED_BOOTSTRAP_N = 1000
EXPECTED_REPEATS = 10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load canonical module: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")


def safe_num(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return value if np.isfinite(value) else float("nan")


def fmt(value: Any, digits: int = 6) -> str:
    x = safe_num(value)
    return "NA" if not np.isfinite(x) else f"{x:.{digits}f}"


def add_log(path: Path, message: str) -> None:
    stamped = f"[{time.strftime('%Y-%m-%d %H:%M:%S %Z')}] {message}"
    print(stamped, flush=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(stamped + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--v02-script", type=Path, required=True)
    parser.add_argument("--v031-script", type=Path, required=True)
    parser.add_argument("--v031-output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--figure5-source", type=Path, required=True)
    parser.add_argument("--highspecific-flow-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--local-predictions-dir", type=Path, required=True)
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--render-existing-aggregates", action="store_true")
    return parser.parse_args()


def build_age_outputs(frame: pd.DataFrame, selected: pd.DataFrame, v02: Any, out: Path) -> str:
    primary = frame.loc[frame["primary_analysis"]].copy()
    admission = primary["admission_datetime"]
    cbc = primary["cbc_datetime"]
    reference = admission.fillna(cbc)
    source = np.where(admission.notna(), "admission_date", np.where(cbc.notna(), "CBC_WBC_test_time_fallback", "missing_reference_date"))
    source = pd.Series(source, index=primary.index)
    groups = {
        "overall": np.ones(len(primary), dtype=bool),
        "AMI": primary["y_primary"].eq(1).to_numpy(),
        "non_AMI_CAD": primary["y_primary"].eq(0).to_numpy(),
    }
    reported = {"overall": 1818, "AMI": 452, "non_AMI_CAD": 1366}
    rows: list[dict[str, Any]] = []
    for group, mask in groups.items():
        sub = primary.loc[mask]
        src = source.loc[mask]
        n = len(sub)
        available = int(sub["age"].notna().sum())
        rows.append(
            {
                "group": group,
                "analysis_n": n,
                "canonical_age_available_n": available,
                "canonical_age_missing_n": n - available,
                "canonical_age_missing_pct": 100 * (n - available) / n if n else np.nan,
                "admission_date_reference_n": int(src.eq("admission_date").sum()),
                "CBC_time_fallback_reference_n": int(src.eq("CBC_WBC_test_time_fallback").sum()),
                "missing_reference_date_n": int(src.eq("missing_reference_date").sum()),
                "submitted_table1_reported_available_n": reported[group],
                "reported_minus_canonical_available_n": reported[group] - available,
                "reported_derivation_status": "NOT_REPRODUCED_FROM_RECOVERED_EXECUTABLE_SOURCE",
            }
        )
    qc = pd.DataFrame(rows)
    write_csv(qc, out / "01_AGE" / "AGE_CANONICAL_QC.csv")

    v02_hash = sha256(Path(v02.__file__).resolve())
    lock_status = (
        "AGE_1820_CANONICAL_LOCKED"
        if len(primary) == EXPECTED_PRIMARY_N and int(primary["age"].notna().sum()) == EXPECTED_PRIMARY_N
        else "AGE_DEFINITION_INCONSISTENCY_HARD_STOP"
    )
    age_text = f"""# Canonical Age Definition Lock

**Status:** `{lock_status}`

The frozen V0.3.1 clinical models build their patient frame through the hash-verified V0.2 cohort script. The canonical derivation is: primary `birth_date`, then `基线_birth_date` only as fallback; reference date is `admission_date`, with `lab_blood_routine_examination_WBC_test_time` as fallback; age is elapsed days divided by 365.2425; values outside the inclusive 18–120 year range are set missing. The input is the previously audited master cohort (SHA-256 `{EXPECTED_SOURCE_SHA256}`), and the executed V0.2 script SHA-256 is `{v02_hash}`.

The canonical primary cohort contains {len(primary)} patients: {int(primary['y_primary'].sum())} AMI and {int((primary['y_primary'] == 0).sum())} non-AMI CAD. Age is available for {int(primary['age'].notna().sum())}/{len(primary)} ({int(primary.loc[primary['y_primary'] == 1, 'age'].notna().sum())} AMI; {int(primary.loc[primary['y_primary'] == 0, 'age'].notna().sum())} non-AMI). The recovered V0.3.1 script uses this vector in the 4-variable clinical baseline and clinical-incremental models; those models retain all eligible patients and use the canonical fold-local median preprocessing for missing clinical predictors.

The submitted Table 1 reports 1,818/1,820 (AMI 452/453; non-AMI 1,366/1,367). No executable correction reproducing that two-person difference was recovered. The reported line is therefore retained only as a separate, unverified reporting branch; it is not the canonical clinical-model age vector. Its exact two records and cause remain unresolved. WP3 should rebuild the Table 1 age row from the locked vector and report the correction. This WP2 task does not edit the manuscript.

Reference-date use is not equivalent to a validated index-admission time anchor. CBC-date fallback counts and the unresolved encounter-linkage limitation are reported in `AGE_CANONICAL_QC.csv` and remain subject to the locked timing claim boundary.
"""
    (out / "01_AGE" / "AGE_CANONICAL_LOCK.md").write_text(age_text, encoding="utf-8")
    return lock_status


def run_group(v031: Any, frame: pd.DataFrame, analysis: str, target: str, specs: list[Any], log_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    add_log(log_path, f"Starting canonical nested OOF block: {analysis}; N={len(frame)}; models={len(specs)}")
    records, tuning, _ = v031.run_nested_oof(frame.reset_index(drop=True), analysis, target, specs, EXPECTED_REPEATS)
    add_log(log_path, f"Completed canonical nested OOF block: {analysis}; records={len(records)}")
    return records, tuning


def performance_row(performance: pd.DataFrame, analysis: str, model: str) -> pd.Series:
    rows = performance.loc[(performance["analysis"] == analysis) & (performance["model"] == model)]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one performance row for {analysis}/{model}; found {len(rows)}")
    return rows.iloc[0]


def fold_identity_matches(records_a: pd.DataFrame, records_b: pd.DataFrame) -> bool:
    cols = ["research_patient_id", "repeat", "fold"]
    a = records_a[cols].drop_duplicates().sort_values(cols).reset_index(drop=True)
    b = records_b[cols].drop_duplicates().sort_values(cols).reset_index(drop=True)
    return a.equals(b)


def model_records(records: pd.DataFrame, analysis: str, model: str) -> pd.DataFrame:
    sub = records.loc[(records["analysis"] == analysis) & (records["model"] == model)].copy()
    if sub.empty:
        raise RuntimeError(f"Missing regenerated predictions for {analysis}/{model}")
    return sub


def build_primary_tables(performance: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_map = [
        ("PIV", "primary_core", "PIV", "primary_full_1820", "no missing fibrinogen"),
        ("Core-7", "primary_core", "Continuous_HITS_Core", "primary_full_1820", "Core complete case"),
        ("Enhanced", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "primary_full_1820", "historical canonical training-fold median imputation"),
        ("Core-7", "primary_fbg_complete_case", "Continuous_HITS_Core", "fibrinogen_complete_case_1705", "same patients and folds as Enhanced complete-case"),
        ("Enhanced", "primary_fbg_complete_case", "Continuous_HITS_Enhanced", "fibrinogen_complete_case_1705", "complete case; no fibrinogen imputation"),
    ]
    rows = []
    for label, analysis, model, cohort, missingness in model_map:
        metric = performance_row(performance, analysis, model)
        rows.append(
            {
                "model": label,
                "analysis_id": analysis,
                "model_id": model,
                "cohort_version": cohort,
                "N": int(metric["n"]),
                "AMI_n": int(metric["event_n"]),
                "non_AMI_n": int(metric["n"] - metric["event_n"]),
                "AUC": metric["oof_auc"],
                "AUC_CI_lower": metric["oof_auc_ci_lower"],
                "AUC_CI_upper": metric["oof_auc_ci_upper"],
                "Brier": metric["brier_score"],
                "calibration_intercept": metric["calibration_intercept"],
                "calibration_slope": metric["calibration_slope"],
                "valid_metric_bootstrap_replicates": metric["metric_bootstrap_valid"],
                "OOF_aggregation": "arithmetic mean of 10 patient-level out-of-fold probabilities",
                "fibrinogen_handling": missingness,
            }
        )
    table = pd.DataFrame(rows)
    write_csv(table, out / "03_PRIMARY_PERFORMANCE" / "PRIMARY_MODEL_PERFORMANCE_CANONICAL.csv")
    return table, pd.DataFrame()


def make_paired_delta(v031: Any, records: pd.DataFrame, analysis_a: str, model_a: str, analysis_b: str, model_b: str, label: str) -> dict[str, Any]:
    ra = model_records(records, analysis_a, model_a)
    rb = model_records(records, analysis_b, model_b)
    same_folds = fold_identity_matches(ra, rb)
    if not same_folds:
        raise RuntimeError(f"Paired comparison has non-identical outer fold identities: {label}")
    result = v031.paired_delta(ra, rb, label, EXPECTED_BOOTSTRAP_N)
    result.update(
        {
            "model_a": model_a,
            "analysis_a": analysis_a,
            "model_b": model_b,
            "analysis_b": analysis_b,
            "AMI_n_common": int(round(result["n_common"] * np.nanmean(ra["y"]))),
            "outer_fold_identity": "IDENTICAL",
            "paired_predictions": True,
            "bootstrap_unit": "patient; both prediction vectors resampled jointly",
            "bootstrap_scope": "fixed patient-level mean OOF probabilities; no model refits",
        }
    )
    return result


def make_deltas(v031: Any, records: pd.DataFrame, out: Path) -> pd.DataFrame:
    specs = [
        ("primary_core", "Continuous_HITS_Core", "primary_core", "PIV", "Primary Core minus PIV"),
        ("primary_enhanced_imputed", "Continuous_HITS_Enhanced", "primary_core", "Continuous_HITS_Core", "Primary imputed Enhanced minus Core"),
        ("primary_fbg_complete_case", "Continuous_HITS_Enhanced", "primary_fbg_complete_case", "Continuous_HITS_Core", "Primary Fibrinogen complete-case Enhanced minus Core"),
    ]
    clinical_names = [
        ("Clinical_Plus_PIV", "Clinical"),
        ("Clinical_Plus_Core", "Clinical"),
        ("Clinical_Plus_Enhanced", "Clinical"),
        ("Clinical_Plus_Core", "Clinical_Plus_PIV"),
        ("Clinical_Plus_Enhanced", "Clinical_Plus_PIV"),
        ("Clinical_Plus_Enhanced", "Clinical_Plus_Core"),
    ]
    for a, b in clinical_names:
        specs.append(("primary_clinical", a, "primary_clinical", b, f"Full cohort {a} minus {b}"))
        specs.append(("primary_clinical_fbg_complete_case", a, "primary_clinical_fbg_complete_case", b, f"Fibrinogen-complete cohort {a} minus {b}"))
    rows = [make_paired_delta(v031, records, *spec) for spec in specs]
    result = pd.DataFrame(rows)
    write_csv(result, out / "03_PRIMARY_PERFORMANCE" / "PRIMARY_PAIRED_DELTAS_CANONICAL.csv")
    return result


def make_reconciliation(
    performance: pd.DataFrame,
    deltas: pd.DataFrame,
    registry: pd.DataFrame,
    historical_fbg: pd.DataFrame,
    historical_deltas: pd.DataFrame,
    out: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add(metric: str, frozen: Any, regenerated: Any, source: str, tolerance: float = 0.005) -> None:
        f = safe_num(frozen)
        r = safe_num(regenerated)
        if not np.isfinite(f) or not np.isfinite(r):
            diff = np.nan
            status = "MATERIAL_MISMATCH"
        else:
            diff = abs(f - r)
            status = "MATCH" if diff <= 1e-8 else "ROUNDING_ONLY" if diff <= 0.0005 else "MINOR_NUMERIC_DIFFERENCE" if diff <= tolerance else "MATERIAL_MISMATCH"
        rows.append({"metric": metric, "frozen_value": f, "regenerated_value": r, "absolute_difference": diff, "tolerance": tolerance, "status": status, "frozen_source": source})

    def registry_value(analysis: str, model: str, field: str) -> Any:
        sub = registry.loc[(registry.analysis_id == analysis) & (registry.model == model), field]
        if len(sub) != 1:
            raise RuntimeError(f"Frozen registry row missing or duplicated: {analysis}/{model}/{field}")
        return sub.iloc[0]

    checks = [
        ("Core AUC", "V031_PRIMARY_OOF", "Core", "AUC", "primary_core", "Continuous_HITS_Core", "oof_auc"),
        ("Core AUC CI lower", "V031_PRIMARY_OOF", "Core", "CI_lower", "primary_core", "Continuous_HITS_Core", "oof_auc_ci_lower"),
        ("Core AUC CI upper", "V031_PRIMARY_OOF", "Core", "CI_upper", "primary_core", "Continuous_HITS_Core", "oof_auc_ci_upper"),
        ("Core Brier", "V031_PRIMARY_OOF", "Core", "Brier", "primary_core", "Continuous_HITS_Core", "brier_score"),
        ("Core calibration intercept", "V031_PRIMARY_OOF", "Core", "calibration_intercept", "primary_core", "Continuous_HITS_Core", "calibration_intercept"),
        ("Core calibration slope", "V031_PRIMARY_OOF", "Core", "calibration_slope", "primary_core", "Continuous_HITS_Core", "calibration_slope"),
        ("PIV AUC", "V031_PRIMARY_OOF", "PIV", "AUC", "primary_core", "PIV", "oof_auc"),
        ("PIV AUC CI lower", "V031_PRIMARY_OOF", "PIV", "CI_lower", "primary_core", "PIV", "oof_auc_ci_lower"),
        ("PIV AUC CI upper", "V031_PRIMARY_OOF", "PIV", "CI_upper", "primary_core", "PIV", "oof_auc_ci_upper"),
        ("Enhanced full-cohort AUC", "V031_PRIMARY_OOF", "Enhanced", "AUC", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "oof_auc"),
        ("Enhanced full-cohort AUC CI lower", "V031_PRIMARY_OOF", "Enhanced", "CI_lower", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "oof_auc_ci_lower"),
        ("Enhanced full-cohort AUC CI upper", "V031_PRIMARY_OOF", "Enhanced", "CI_upper", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "oof_auc_ci_upper"),
        ("Enhanced full-cohort Brier", "V031_PRIMARY_OOF", "Enhanced", "Brier", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "brier_score"),
        ("Enhanced full-cohort calibration intercept", "V031_PRIMARY_OOF", "Enhanced", "calibration_intercept", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "calibration_intercept"),
        ("Enhanced full-cohort calibration slope", "V031_PRIMARY_OOF", "Enhanced", "calibration_slope", "primary_enhanced_imputed", "Continuous_HITS_Enhanced", "calibration_slope"),
    ]
    for metric, reg_analysis, reg_model, reg_field, analysis, model, perf_field in checks:
        add(metric, registry_value(reg_analysis, reg_model, reg_field), performance_row(performance, analysis, model)[perf_field], "V0.5.2 Publication Freeze canonical result registry")

    frozen_core_piv = registry_value("V031_PRIMARY_OOF_DELTA", "Core-PIV", "delta_AUC")
    frozen_core_piv_lo = registry_value("V031_PRIMARY_OOF_DELTA", "Core-PIV", "delta_CI_lower")
    frozen_core_piv_hi = registry_value("V031_PRIMARY_OOF_DELTA", "Core-PIV", "delta_CI_upper")
    row = deltas.loc[deltas.comparison == "Primary Core minus PIV"].iloc[0]
    for metric, frozen, regenerated in [
        ("Core-PIV paired delta AUC", frozen_core_piv, row.delta_auc_a_minus_b),
        ("Core-PIV paired delta CI lower", frozen_core_piv_lo, row.delta_auc_ci_lower),
        ("Core-PIV paired delta CI upper", frozen_core_piv_hi, row.delta_auc_ci_upper),
    ]:
        add(metric, frozen, regenerated, "V0.5.2 Publication Freeze canonical result registry")

    for cohort, analysis in [("Fibrinogen-complete Core", "primary_fbg_complete_case"), ("Fibrinogen-complete Enhanced", "primary_fbg_complete_case")]:
        model = "Continuous_HITS_Core" if cohort.endswith("Core") else "Continuous_HITS_Enhanced"
        old = historical_fbg.loc[(historical_fbg.analysis == analysis) & (historical_fbg.model == model)]
        if len(old) != 1:
            raise RuntimeError(f"Historical complete-case frozen row missing: {analysis}/{model}")
        current = performance_row(performance, analysis, model)
        for label, field_old, field_new in [
            ("AUC", "oof_auc", "oof_auc"),
            ("AUC CI lower", "oof_auc_ci_lower", "oof_auc_ci_lower"),
            ("AUC CI upper", "oof_auc_ci_upper", "oof_auc_ci_upper"),
            ("Brier", "brier_score", "brier_score"),
            ("calibration intercept", "calibration_intercept", "calibration_intercept"),
            ("calibration slope", "calibration_slope", "calibration_slope"),
        ]:
            add(f"{cohort} {label}", old.iloc[0][field_old], current[field_new], "V0.3.1 frozen same-sample fibrinogen complete-case output")
    hist_pair = historical_deltas.loc[historical_deltas.comparison == "Primary Fibrinogen complete-case Enhanced minus Core"]
    if len(hist_pair) != 1:
        raise RuntimeError("Historical fibrinogen complete-case paired delta missing")
    new_pair = deltas.loc[deltas.comparison == "Primary Fibrinogen complete-case Enhanced minus Core"].iloc[0]
    for metric, field in [("Fibrinogen complete-case paired delta AUC", "delta_auc_a_minus_b"), ("Fibrinogen complete-case paired delta CI lower", "delta_auc_ci_lower"), ("Fibrinogen complete-case paired delta CI upper", "delta_auc_ci_upper")]:
        old_field = {"delta_auc_a_minus_b": "delta_auc_a_minus_b", "delta_auc_ci_lower": "delta_auc_ci_lower", "delta_auc_ci_upper": "delta_auc_ci_upper"}[field]
        add(metric, hist_pair.iloc[0][old_field], new_pair[field], "V0.3.1 frozen same-sample fibrinogen paired comparison")

    for model, model_id in [("Clinical", "Clinical"), ("Clinical+PIV", "Clinical_Plus_PIV"), ("Clinical+Core", "Clinical_Plus_Core"), ("Clinical+Enhanced", "Clinical_Plus_Enhanced")]:
        current = performance_row(performance, "primary_clinical", model_id)
        for label, field_registry, field_performance in [
            ("AUC", "AUC", "oof_auc"),
            ("AUC CI lower", "CI_lower", "oof_auc_ci_lower"),
            ("AUC CI upper", "CI_upper", "oof_auc_ci_upper"),
            ("Brier", "Brier", "brier_score"),
            ("calibration intercept", "calibration_intercept", "calibration_intercept"),
            ("calibration slope", "calibration_slope", "calibration_slope"),
        ]:
            add(f"{model} {label}", registry_value("V031_CLINICAL_OOF", model_id, field_registry), current[field_performance], "V0.5.2 Publication Freeze canonical result registry")

    result = pd.DataFrame(rows)
    write_csv(result, out / "00_EXECUTIVE" / "CANONICAL_REGENERATION_RECONCILIATION.csv")
    return result


def clinical_tables(performance: pd.DataFrame, deltas: pd.DataFrame, frame: pd.DataFrame, out: Path) -> None:
    model_ids = ["Clinical", "Clinical_Plus_PIV", "Clinical_Plus_Core", "Clinical_Plus_Enhanced"]
    labels = {"Clinical": "Clinical only", "Clinical_Plus_PIV": "Clinical + PIV", "Clinical_Plus_Core": "Clinical + Core-7", "Clinical_Plus_Enhanced": "Clinical + Enhanced"}
    analyses = ["primary_clinical", "primary_clinical_fbg_complete_case"]
    rows: list[dict[str, Any]] = []
    for analysis in analyses:
        for model_id in model_ids:
            metric = performance_row(performance, analysis, model_id)
            rows.append(
                {
                    "record_type": "model_performance",
                    "cohort_version": "fibrinogen_complete_case_1705" if analysis.endswith("complete_case") else "primary_full_1820",
                    "model": labels[model_id],
                    "N": int(metric.n),
                    "AMI_n": int(metric.event_n),
                    "non_AMI_n": int(metric.n - metric.event_n),
                    "AUC": metric.oof_auc,
                    "AUC_CI_lower": metric.oof_auc_ci_lower,
                    "AUC_CI_upper": metric.oof_auc_ci_upper,
                    "Brier": metric.brier_score,
                    "calibration_intercept": metric.calibration_intercept,
                    "calibration_slope": metric.calibration_slope,
                    "comparison": "",
                    "delta_AUC": np.nan,
                    "delta_CI_lower": np.nan,
                    "delta_CI_upper": np.nan,
                    "paired_N": np.nan,
                    "paired_outer_folds": "",
                    "bootstrap_scope": "1000 patient resamples of fixed mean OOF predictions; no model refits",
                }
            )
    for _, delta in deltas.iterrows():
        if not str(delta.comparison).startswith(("Full cohort Clinical", "Fibrinogen-complete cohort Clinical")):
            continue
        rows.append(
            {
                "record_type": "paired_delta_auc",
                "cohort_version": "fibrinogen_complete_case_1705" if str(delta.comparison).startswith("Fibrinogen-complete") else "primary_full_1820",
                "model": "",
                "N": np.nan,
                "AMI_n": np.nan,
                "non_AMI_n": np.nan,
                "AUC": np.nan,
                "AUC_CI_lower": np.nan,
                "AUC_CI_upper": np.nan,
                "Brier": np.nan,
                "calibration_intercept": np.nan,
                "calibration_slope": np.nan,
                "comparison": delta.comparison,
                "delta_AUC": delta.delta_auc_a_minus_b,
                "delta_CI_lower": delta.delta_auc_ci_lower,
                "delta_CI_upper": delta.delta_auc_ci_upper,
                "paired_N": delta.n_common,
                "paired_outer_folds": delta.outer_fold_identity,
                "bootstrap_scope": delta.bootstrap_scope,
            }
        )
    write_csv(pd.DataFrame(rows), out / "04_CLINICAL_INCREMENTAL" / "CLINICAL_INCREMENTAL_PERFORMANCE_CANONICAL.csv")

    clinical_vars = ["age", "male", "hypertension", "diabetes"]
    missing_rows = []
    for group, mask in {
        "overall": np.ones(len(frame), dtype=bool),
        "AMI": frame["y_primary"].eq(1).to_numpy(),
        "non_AMI": frame["y_primary"].eq(0).to_numpy(),
    }.items():
        sub = frame.loc[mask]
        for variable in clinical_vars:
            n = len(sub)
            missing = int(sub[variable].isna().sum())
            missing_rows.append(
                {
                    "group": group,
                    "variable": variable,
                    "analysis_n": n,
                    "available_n": n - missing,
                    "missing_n": missing,
                    "missing_pct": 100 * missing / n if n else np.nan,
                    "CV_handling": "numeric/binary coding; training-fold median imputation; fold-local standardization",
                }
            )
    write_csv(pd.DataFrame(missing_rows), out / "04_CLINICAL_INCREMENTAL" / "CLINICAL_COVARIATE_MISSINGNESS_FINAL.csv")


def fibrinogen_outputs(primary: pd.DataFrame, cc: pd.DataFrame, out: Path) -> None:
    rows = []
    for group, mask in {
        "overall": np.ones(len(primary), dtype=bool),
        "AMI": primary["y_primary"].eq(1).to_numpy(),
        "non_AMI": primary["y_primary"].eq(0).to_numpy(),
    }.items():
        sub = primary.loc[mask]
        n = len(sub)
        available = int(sub["fbg"].notna().sum())
        rows.append({"group": group, "analysis_n": n, "available_n": available, "missing_n": n - available, "missing_pct": 100 * (n - available) / n if n else np.nan})
    rows.append({"group": "complete_case", "analysis_n": len(primary), "available_n": len(cc), "missing_n": len(primary) - len(cc), "missing_pct": 100 * (len(primary) - len(cc)) / len(primary), "AMI_n": int(cc.y_primary.sum()), "non_AMI_n": int(len(cc) - cc.y_primary.sum())})
    write_csv(pd.DataFrame(rows), out / "05_FIBRINOGEN" / "FIBRINOGEN_MISSINGNESS_FINAL.csv")
    text = f"""# Fibrinogen Complete-Case QC

The frozen primary cohort has N={len(primary)} (AMI={int(primary.y_primary.sum())}). Fibrinogen is available in N={int(primary.fbg.notna().sum())}; {int(primary.fbg.isna().sum())} values are missing. The complete-case sample has N={len(cc)}, AMI={int(cc.y_primary.sum())}, and non-AMI={int(len(cc) - cc.y_primary.sum())}.

Enhanced full-cohort reproduction follows the exact historical V0.3.1 canonical fold-local median-imputation pipeline solely to reconcile the frozen 0.735135 result. This is not a new imputation method. The distinct complete-case Enhanced comparison applies no fibrinogen imputation and pairs Enhanced with Core on the same patients and identical outer folds. Clinical incremental comparisons and reviewer-facing DCA involving Enhanced are additionally repeated on that same complete-case sample; clinical missing values continue to use the frozen fold-local median procedure.

The complete-case patient set is defined by the frozen Core-7 + fibrinogen availability rule. Patient-level membership checks are performed in memory only; IDs are not exported.
"""
    (out / "05_FIBRINOGEN" / "FIBRINOGEN_COMPLETE_CASE_QC.md").write_text(text, encoding="utf-8")


def traditional_table(performance: pd.DataFrame, out: Path) -> None:
    formulas = {
        "NLR": "neutrophil / lymphocyte",
        "PLR": "platelet / lymphocyte",
        "MLR": "monocyte / lymphocyte",
        "SII": "platelet * neutrophil / lymphocyte",
        "SIRI": "neutrophil * monocyte / lymphocyte",
        "PIV": "platelet * neutrophil * monocyte / lymphocyte",
        "HRR": "hemoglobin / RDW",
    }
    rows = []
    for model, formula in formulas.items():
        metric = performance_row(performance, "primary_core", model)
        rows.append(
            {
                "index": model,
                "formula": formula,
                "transformation": "log1p where prespecified by canonical V0.3.1 pipeline; training-fold standardization",
                "model": "unpenalized logistic regression in the canonical repeated nested-OOF framework",
                "N": int(metric.n),
                "AMI_n": int(metric.event_n),
                "AUC": metric.oof_auc,
                "AUC_CI_lower": metric.oof_auc_ci_lower,
                "AUC_CI_upper": metric.oof_auc_ci_upper,
                "Brier": metric.brier_score,
                "role": "PIV prespecified primary conventional comparator; remaining indices supplementary benchmarks",
            }
        )
    write_csv(pd.DataFrame(rows), out / "06_TRADITIONAL_INDICES" / "TRADITIONAL_INDEX_CANONICAL_PERFORMANCE.csv")


def collinearity_outputs(primary: pd.DataFrame, v031_output: Path, out: Path) -> None:
    core = ["neut", "lymph", "mono", "plt", "mpv", "rdw", "hb"]
    matrix = primary[core].corr(method="spearman")
    matrix.index.name = "variable"
    write_csv(matrix.reset_index(), out / "07_COLLINEARITY" / "CORE7_SPEARMAN_MATRIX.csv")
    long = matrix.stack().rename("spearman_rho").reset_index()
    long.columns = ["variable_x", "variable_y", "spearman_rho"]
    write_csv(long, out / "07_COLLINEARITY" / "CORE7_CORRELATION_HEATMAP_SOURCE.csv")
    stability = pd.read_csv(v031_output / "16_variable_stability.csv")
    stability = stability.loc[stability.bootstrap_model == "Continuous_HITS_Core_primary"].copy()
    if set(stability.variable) != set(core):
        raise RuntimeError("Frozen 300-bootstrap Core stability rows do not match Core-7")
    write_csv(stability, out / "07_COLLINEARITY" / "VARIABLE_STABILITY_300_BOOTSTRAP.csv")
    offdiag = matrix.to_numpy()[~np.eye(len(core), dtype=bool)]
    max_idx = np.unravel_index(np.argmax(np.abs(matrix.to_numpy() - np.diag(np.diag(matrix.to_numpy())))), matrix.shape)
    var_a, var_b = matrix.index[max_idx[0]], matrix.columns[max_idx[1]]
    text = f"""# Core-7 Collinearity Summary

Spearman correlations were calculated descriptively among the frozen seven Core predictors in the primary cohort (N={len(primary)}). The largest absolute off-diagonal correlation is {abs(matrix.loc[var_a, var_b]):.4f} for {var_a} and {var_b}. No variable was removed or reselected. VIF was not used to change the architecture.

The separate `VARIABLE_STABILITY_300_BOOTSTRAP.csv` is the existing V0.3.1 300 full-development bootstrap evidence, not repeated-CV selection frequency. It includes selection frequency, sign stability when selected, and standardized coefficient summaries. It is reproduced as a frozen aggregate and is not refitted in WP2.
"""
    (out / "07_COLLINEARITY" / "CORE7_COLLINEARITY_SUMMARY.md").write_text(text, encoding="utf-8")


def mean_predictions(v031: Any, records: pd.DataFrame) -> pd.DataFrame:
    return v031.patient_mean_predictions(records)


def calibration_outputs(v031: Any, records: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = [
        ("primary_core", "PIV", "PIV"),
        ("primary_core", "Continuous_HITS_Core", "Core-7"),
        ("primary_enhanced_imputed", "Continuous_HITS_Enhanced", "Enhanced (full cohort)"),
        ("primary_fbg_complete_case", "Continuous_HITS_Enhanced", "Enhanced (complete case)"),
        ("primary_clinical", "Clinical", "Clinical only"),
        ("primary_clinical", "Clinical_Plus_PIV", "Clinical + PIV"),
        ("primary_clinical", "Clinical_Plus_Core", "Clinical + Core-7"),
        ("primary_clinical", "Clinical_Plus_Enhanced", "Clinical + Enhanced (full cohort)"),
        ("primary_clinical_fbg_complete_case", "Clinical", "Clinical only (complete case)"),
        ("primary_clinical_fbg_complete_case", "Clinical_Plus_PIV", "Clinical + PIV (complete case)"),
        ("primary_clinical_fbg_complete_case", "Clinical_Plus_Core", "Clinical + Core-7 (complete case)"),
        ("primary_clinical_fbg_complete_case", "Clinical_Plus_Enhanced", "Clinical + Enhanced (complete case)"),
    ]
    curve_rows, summary_rows = [], []
    for analysis, model, label in selected:
        sub = mean_predictions(v031, model_records(records, analysis, model))
        y = sub.y.to_numpy(dtype=int)
        p = sub.prediction.to_numpy(dtype=float)
        probabilities = np.quantile(p, np.linspace(0, 1, 11), method="median_unbiased")
        breaks = np.unique(probabilities)
        if len(breaks) < 2:
            bin_id = np.ones(len(p), dtype=int)
        else:
            bin_id = pd.cut(p, bins=breaks, include_lowest=True, labels=False, duplicates="drop")
            bin_id = np.asarray(bin_id, dtype=float)
        tmp = pd.DataFrame({"bin": bin_id, "y": y, "prediction": p}).dropna(subset=["bin"])
        grouped = tmp.groupby("bin", as_index=False).agg(N=("y", "size"), AMI_n=("y", "sum"), mean_predicted=("prediction", "mean"), observed_rate=("y", "mean"))
        grouped["model"] = label
        grouped["analysis_id"] = analysis
        grouped["bin_method"] = "10 target quantile groups; R quantile type 8 equivalent; duplicate breaks removed"
        grouped["bin"] = grouped["bin"].astype(int) + 1
        curve_rows.append(grouped[["model", "analysis_id", "bin", "N", "AMI_n", "mean_predicted", "observed_rate", "bin_method"]])
        summary_rows.append(
            {
                "model": label,
                "analysis_id": analysis,
                "N": len(sub),
                "AMI_n": int(y.sum()),
                "mean_probability": float(np.mean(p)),
                "sd_probability": float(np.std(p, ddof=1)),
                "min_probability": float(np.min(p)),
                "p25_probability": float(np.quantile(p, 0.25)),
                "median_probability": float(np.quantile(p, 0.50)),
                "p75_probability": float(np.quantile(p, 0.75)),
                "max_probability": float(np.max(p)),
            }
        )
    curves = pd.concat(curve_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    write_csv(curves, out / "08_CALIBRATION" / "CALIBRATION_CANONICAL_SOURCE.csv")
    write_csv(curves[["model", "analysis_id", "bin", "N", "AMI_n", "bin_method"]], out / "08_CALIBRATION" / "CALIBRATION_GROUP_COUNTS.csv")
    write_csv(summary, out / "08_CALIBRATION" / "PREDICTED_PROBABILITY_SUMMARY.csv")
    return curves, summary


def roc_source(v031: Any, records: pd.DataFrame, out: Path) -> None:
    models = [
        ("PIV", "primary_core", "PIV"),
        ("Core-7", "primary_core", "Continuous_HITS_Core"),
        ("Enhanced (full cohort)", "primary_enhanced_imputed", "Continuous_HITS_Enhanced"),
        ("Enhanced (complete case)", "primary_fbg_complete_case", "Continuous_HITS_Enhanced"),
    ]
    grid = np.linspace(0, 1, 101)
    rows = []
    for label, analysis, model in models:
        sub = mean_predictions(v031, model_records(records, analysis, model))
        fpr, tpr, _ = v031.roc_curve(sub.y.to_numpy(dtype=int), sub.prediction.to_numpy(dtype=float))
        unique_fpr = np.unique(fpr)
        unique_tpr = np.asarray([np.max(tpr[fpr == x]) for x in unique_fpr])
        interpolated = np.interp(grid, unique_fpr, unique_tpr)
        for x, y in zip(grid, interpolated):
            rows.append({"model": label, "false_positive_rate": x, "true_positive_rate": y, "curve_source": "canonical 5x10 patient-mean OOF"})
    write_csv(pd.DataFrame(rows), out / "13_FIGURE_SOURCES" / "ROC_CANONICAL_SOURCE.csv")


def dca_outputs(v031: Any, records: pd.DataFrame, out: Path) -> pd.DataFrame:
    analysis = "primary_clinical_fbg_complete_case"
    model_specs = [
        ("Clinical only", "Clinical"),
        ("Clinical + PIV", "Clinical_Plus_PIV"),
        ("Clinical + Core-7", "Clinical_Plus_Core"),
        ("Clinical + Enhanced", "Clinical_Plus_Enhanced"),
    ]
    means = {label: mean_predictions(v031, model_records(records, analysis, model)) for label, model in model_specs}
    reference = means["Clinical only"]["research_patient_id"].astype(str).tolist()
    ref_y = means["Clinical only"]["y"].to_numpy(dtype=int)
    for label, sub in means.items():
        if sub.research_patient_id.astype(str).tolist() != reference or not np.array_equal(sub.y.to_numpy(dtype=int), ref_y):
            raise RuntimeError(f"Clinical DCA model does not use the same patient sample: {label}")
    thresholds = np.arange(0.05, 0.501, 0.01)
    n = len(ref_y)
    prevalence = float(np.mean(ref_y))
    rows = []
    for label, sub in means.items():
        p = sub.prediction.to_numpy(dtype=float)
        for threshold in thresholds:
            positive = p >= threshold
            nb = np.sum(positive & (ref_y == 1)) / n - np.sum(positive & (ref_y == 0)) / n * threshold / (1 - threshold)
            rows.append({"model": label, "threshold_probability": threshold, "net_benefit": float(nb), "N": n, "AMI_n": int(ref_y.sum()), "decision_curve_scope": "exploratory phenotype discrimination; not clinical utility"})
    for threshold in thresholds:
        rows.append({"model": "Treat all", "threshold_probability": threshold, "net_benefit": prevalence - (1 - prevalence) * threshold / (1 - threshold), "N": n, "AMI_n": int(ref_y.sum()), "decision_curve_scope": "reference strategy"})
        rows.append({"model": "Treat none", "threshold_probability": threshold, "net_benefit": 0.0, "N": n, "AMI_n": int(ref_y.sum()), "decision_curve_scope": "reference strategy"})
    table = pd.DataFrame(rows)
    write_csv(table, out / "09_DCA" / "DCA_CANONICAL_SOURCE.csv")
    methods = f"""# Decision-Curve Analysis Methods

The reviewer-facing DCA uses only canonical 5-fold × 10-repeat patient-level mean OOF probabilities from the fibrinogen-complete primary sample (N={n}, AMI={int(ref_y.sum())}). Clinical-only, Clinical+PIV, Clinical+Core-7, and Clinical+Enhanced predictions are matched to the same patients and validation partitions; no fibrinogen values are missing in this sample. The full-cohort Enhanced historical reproduction is not mixed into this paired DCA.

Net benefit is calculated as TP/N − FP/N × pt/(1−pt). Thresholds are prespecified at 0.05–0.50 in 0.01 increments, matching the historical exploratory range; no threshold is optimized. Treat-all and treat-none are included. This retrospective phenotype-discrimination DCA is exploratory and does not establish clinical utility or treatment benefit.

Uncertainty is not represented as full model-development uncertainty. The input predictions are fixed mean OOF probabilities; the DCA is descriptive.
"""
    (out / "09_DCA" / "DCA_METHODS.md").write_text(methods, encoding="utf-8")
    return table


def high_specificity_outputs(flow_source: Path, out: Path) -> pd.DataFrame:
    source = pd.read_csv(flow_source)
    required = {"stage", "primary_n", "primary_ami_n", "highspecific_ami_n", "strict_control_n", "highspecific_total_n"}
    if not required.issubset(source.columns):
        raise RuntimeError("Frozen high-specificity flow source schema mismatch")
    expected = {"development_guaranteed_early": (1001, 196, 162, 634, 796), "guard_band_excluded": (271, 79, 62, 142, 204), "validation_guaranteed_late": (548, 178, 138, 288, 426)}
    for stage, vals in expected.items():
        row = source.loc[source.stage == stage]
        if len(row) != 1 or tuple(int(row.iloc[0][c]) for c in ["primary_n", "primary_ami_n", "highspecific_ami_n", "strict_control_n", "highspecific_total_n"]) != vals:
            raise RuntimeError(f"Frozen high-specificity flow count mismatch: {stage}")
    rows = [
        {"stage": "primary_AMI", "N": 453, "AMI_n": 453, "non_AMI_n": 0, "rule": "frozen primary diagnosis-text phenotype"},
        {"stage": "date_axis_early", "N": 196, "AMI_n": 196, "non_AMI_n": 0, "rule": "frozen deidentified date-axis allocation; no temporal re-analysis"},
        {"stage": "date_axis_buffer", "N": 79, "AMI_n": 79, "non_AMI_n": 0, "rule": "frozen deidentified date-axis allocation; excluded from boundary comparison"},
        {"stage": "date_axis_later", "N": 178, "AMI_n": 178, "non_AMI_n": 0, "rule": "frozen deidentified date-axis allocation"},
        {"stage": "later_high_specificity_AMI", "N": 138, "AMI_n": 138, "non_AMI_n": 0, "rule": "definite AMI plus MI keyword and acute marker; excludes subacute and uncertain wording; requires STEMI/NSTEMI/ST segment subtype or explicit acute MI phrase/site"},
        {"stage": "later_AMI_not_meeting_strict_text_rule", "N": 40, "AMI_n": 40, "non_AMI_n": 0, "rule": "difference between frozen later primary AMI (178) and high-specificity subset (138); not adjudicated misclassification"},
        {"stage": "later_broad_CAD_angina_controls", "N": 370, "AMI_n": 0, "non_AMI_n": 370, "rule": "frozen broad late non-AMI control pool before strict-control restriction"},
        {"stage": "later_strict_CAD_angina_controls", "N": 288, "AMI_n": 0, "non_AMI_n": 288, "rule": "frozen strict-control rule; 370 broad late controls less 82 excluded"},
        {"stage": "later_broad_controls_excluded", "N": 82, "AMI_n": 0, "non_AMI_n": 82, "rule": "does not meet frozen strict CAD/angina control definition"},
        {"stage": "later_high_specificity_comparison", "N": 426, "AMI_n": 138, "non_AMI_n": 288, "rule": "high-specificity late AMI plus strict CAD/angina controls"},
    ]
    result = pd.DataFrame(rows)
    write_csv(result, out / "10_HIGH_SPECIFICITY" / "HIGH_SPECIFICITY_FLOW_FINAL.csv")
    return result


def temporal_context(registry: pd.DataFrame, flow_source: Path, out: Path) -> None:
    flow = pd.read_csv(flow_source)
    specs = [
        ("V05_PRIMARY_GUARDBAND", "Core-7", "Core"),
        ("V05_PRIMARY_GUARDBAND", "PIV", "PIV"),
        ("V05_PRIMARY_GUARDBAND", "Enhanced", "Enhanced"),
    ]
    values = {}
    for analysis, model, label in specs:
        row = registry.loc[(registry.analysis_id == analysis) & (registry.model == model)]
        if len(row) != 1:
            raise RuntimeError(f"Temporal frozen registry row missing: {analysis}/{model}")
        values[label] = float(row.iloc[0].AUC)
    delta = registry.loc[(registry.analysis_id == "V05_PRIMARY_GUARDBAND_DELTA") & (registry.model == "Core7_minus_PIV")]
    if len(delta) != 1:
        raise RuntimeError("Frozen date-axis Core-PIV delta missing")
    d = delta.iloc[0]
    rows = []
    for _, row in flow.iterrows():
        label = {"development_guaranteed_early": "development", "guard_band_excluded": "buffer", "validation_guaranteed_late": "later"}[row.stage]
        rows.append({"stage": label, "N": int(row.primary_n), "AMI_n": int(row.primary_ami_n), "Core_AUC": values["Core"], "PIV_AUC": values["PIV"], "Core_minus_PIV_delta_AUC": d.delta_AUC, "delta_CI_lower": d.delta_CI_lower, "delta_CI_upper": d.delta_CI_upper, "Enhanced_AUC": values["Enhanced"], "analysis_label": "EXPLORATORY DEIDENTIFIED DATE-AXIS SENSITIVITY ANALYSIS"})
    write_csv(pd.DataFrame(rows), out / "12_TEMPORAL_CONTEXT" / "DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv")
    text = f"""# Date-Axis Sensitivity Context for WP3

This frozen analysis is retained only as **EXPLORATORY DEIDENTIFIED DATE-AXIS SENSITIVITY ANALYSIS**. No temporal analysis was rerun in WP2. The available date axis could not be uniformly linked to the index coronary-angiography hospitalization and therefore does not constitute formal temporal validation or evidence of transportability.

| Frozen allocation | N | AMI |
|---|---:|---:|
| Development | {int(flow.loc[flow.stage == 'development_guaranteed_early', 'primary_n'].iloc[0])} | {int(flow.loc[flow.stage == 'development_guaranteed_early', 'primary_ami_n'].iloc[0])} |
| Buffer | {int(flow.loc[flow.stage == 'guard_band_excluded', 'primary_n'].iloc[0])} | {int(flow.loc[flow.stage == 'guard_band_excluded', 'primary_ami_n'].iloc[0])} |
| Later | {int(flow.loc[flow.stage == 'validation_guaranteed_late', 'primary_n'].iloc[0])} | {int(flow.loc[flow.stage == 'validation_guaranteed_late', 'primary_ami_n'].iloc[0])} |

Frozen later-sample AUCs: Core {values['Core']:.6f}; PIV {values['PIV']:.6f}; Enhanced {values['Enhanced']:.6f}. Core−PIV ΔAUC {float(d.delta_AUC):+.6f} (95% CI {float(d.delta_CI_lower):+.6f} to {float(d.delta_CI_upper):+.6f}); the interval crosses zero. Values are read from the Publication Freeze registry; no temporal fitting or refitting was performed.
"""
    (out / "12_TEMPORAL_CONTEXT" / "DATE_AXIS_SENSITIVITY_FINAL_FACTS.md").write_text(text, encoding="utf-8")


def figure5_ci_audit(source_path: Path, registry: pd.DataFrame, out: Path) -> pd.DataFrame:
    source = pd.read_csv(source_path)
    analysis_map = {
        "Symmetric +/-182-day guard-band": "V05_PRIMARY_GUARDBAND",
        "High-specificity phenotype": "V05_HIGH_SPECIFICITY",
        "Conservative +/-365-day buffer": "V05_CONSERVATIVE_365D",
    }
    rows = []
    for _, item in source.iterrows():
        reg_analysis = analysis_map.get(str(item.analysis))
        model = str(item.model)
        frozen = registry.loc[(registry.analysis_id == reg_analysis) & (registry.model == model)] if reg_analysis else pd.DataFrame()
        ci_present = pd.notna(item.ci_lower) and pd.notna(item.ci_upper)
        if len(frozen) != 1:
            status = "SOURCE_ROW_NOT_FOUND_IN_FROZEN_REGISTRY"
            n = np.nan
        elif not ci_present:
            status = "CI_MISSING_NOT_REGENERATED"
            n = frozen.iloc[0].N
        else:
            f = frozen.iloc[0]
            equal = np.allclose([item.auc, item.ci_lower, item.ci_upper], [f.AUC, f.CI_lower, f.CI_upper], rtol=0, atol=1e-8)
            status = "CI_AVAILABLE_MATCHES_FROZEN_REGISTRY" if equal else "SOURCE_REGISTRY_NUMERIC_DISCREPANCY"
            n = f.N
        rows.append({"analysis": item.analysis, "model": model, "N": n, "AUC": item.auc, "CI_lower": item.ci_lower, "CI_upper": item.ci_upper, "CI_present": bool(ci_present), "CI_status": status, "source": source_path.name, "recalculated": False})
    result = pd.DataFrame(rows)
    write_csv(result, out / "11_FIGURE5" / "FIGURE5_FINAL_CI_TABLE.csv")
    return result


def source_and_environment_hashes(paths: dict[str, Path], out: Path, v031: Any) -> None:
    rows = [{"source_name": name, "sha256": sha256(path), "bytes": path.stat().st_size} for name, path in paths.items()]
    write_csv(pd.DataFrame(rows), out / "14_CODE" / "source_hashes.csv")
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": v031.scipy.__version__,
        "scikit_learn": v031.sklearn.__version__,
        "statsmodels": v031.sm.__version__,
        "matplotlib": v031.matplotlib.__version__,
        "seed": v031.SEED,
        "outer_cv": "5-fold x 10 repeats; RepeatedStratifiedKFold; random_state=20260825",
        "inner_cv": "5-fold StratifiedKFold; per-fold stable seed",
        "elastic_net_C_grid": v031.C_GRID,
        "elastic_net_l1_ratio_grid": v031.ALPHA_GRID,
        "metric_and_paired_bootstrap_n": EXPECTED_BOOTSTRAP_N,
        "bootstrap_method": "1000 patient resamples of fixed patient-mean OOF predictions; percentile 2.5th/97.5th; no model refits",
        "patient_level_prediction_exports": "private local directory only; not part of repository",
        "figure_backend": "R with ggplot2/ragg",
    }
    (out / "14_CODE" / "sessionInfo.json").write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")


def record_analysis_code_hashes(out: Path) -> None:
    manifest_path = out / "14_CODE" / "source_hashes.csv"
    manifest = pd.read_csv(manifest_path)
    code_paths = [Path(__file__).resolve(), *sorted((out / "13_FIGURE_SOURCES" / "R").glob("*.R"))]
    code_rows = pd.DataFrame(
        [
            {"source_name": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in code_paths
        ]
    )
    manifest = manifest.loc[~manifest.source_name.isin(code_rows.source_name)]
    write_csv(pd.concat([manifest, code_rows], ignore_index=True), manifest_path)


def write_pipeline_lock(out: Path, source_hash: str, v02_hash: str, v031_hash: str, registry_hash: str) -> None:
    text = f"""# Canonical Pipeline Lock

This is targeted reproduction, not model redevelopment. The executed source cohort SHA-256 is `{source_hash}`; the exact V0.2 cohort/phenotype script SHA-256 is `{v02_hash}`; the V0.3.1 canonical fitting script SHA-256 is `{v031_hash}`; the V0.5.2 canonical result registry SHA-256 is `{registry_hash}`.

Frozen settings: outcome and row-selection logic from V0.2; Core-7 and Enhanced predictor sets unchanged; outer 5-fold × 10 repeats, stratified; inner 5-fold; seed 20260825; elastic-net C grid {0.1, 1.0, 10.0}; l1 ratio grid {0.25, 0.5, 0.75}; no grid expansion; no new algorithm or feature selection. Transformations, imputation, scaling, and tuning remain inside the relevant training folds.

The model blocks are the original canonical analysis IDs: `primary_core`, `primary_enhanced_imputed`, `primary_fbg_complete_case`, and `primary_clinical`. A separate, explicitly labeled `primary_clinical_fbg_complete_case` block evaluates the four clinical models on one shared fibrinogen-complete sample for paired reviewer comparisons and DCA. The full-cohort Enhanced block reproduces the exact historical fold-local median method to reconcile its frozen result; the 1705-person complete-case block performs no fibrinogen imputation.

Each patient has one held-out prediction in each outer repeat. The canonical patient-level prediction is the arithmetic mean across the 10 held-out probabilities. Patient-level data are saved only outside this repository with restrictive filesystem permissions. Public artifacts contain aggregate results only.
"""
    (out / "02_CANONICAL_OOF" / "CANONICAL_PIPELINE_LOCK.md").write_text(text, encoding="utf-8")


def write_prediction_qc(v031: Any, records: pd.DataFrame, local_dir: Path, out: Path) -> None:
    resolved_out = out.resolve()
    resolved_local = local_dir.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    if resolved_local == repository_root or repository_root in resolved_local.parents:
        raise RuntimeError("Private prediction directory must be outside the public repository")
    resolved_local.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(resolved_local, 0o700)
    old_umask = os.umask(0o077)
    try:
        repeated_path = resolved_local / "canonical_oof_repeated_predictions_LOCAL_ONLY.csv"
        mean_path = resolved_local / "canonical_oof_patient_mean_predictions_LOCAL_ONLY.csv"
        records.to_csv(repeated_path, index=False, lineterminator="\n")
        means = v031.patient_mean_predictions(records)
        means.to_csv(mean_path, index=False, lineterminator="\n")
    finally:
        os.umask(old_umask)
    os.chmod(repeated_path, stat.S_IRUSR | stat.S_IWUSR)
    os.chmod(mean_path, stat.S_IRUSR | stat.S_IWUSR)
    qc = []
    for (analysis, model), sub in records.groupby(["analysis", "model"], sort=False):
        patient_n = int(sub.research_patient_id.nunique())
        repeat_counts = sub.groupby("repeat").research_patient_id.nunique()
        fold_counts = sub.groupby("repeat").fold.nunique()
        qc.append({"analysis_id": analysis, "model": model, "patient_n": patient_n, "record_n": int(len(sub)), "repeat_n": int(sub.repeat.nunique()), "outer_fold_n_per_repeat": int(fold_counts.min()), "min_patients_per_repeat": int(repeat_counts.min()), "max_patients_per_repeat": int(repeat_counts.max()), "missing_prediction_n": int(sub.prediction.isna().sum()), "probability_min": float(sub.prediction.min()), "probability_max": float(sub.prediction.max()), "patient_level_prediction_file_committed": False})
    write_csv(pd.DataFrame(qc), out / "02_CANONICAL_OOF" / "OOF_PREDICTION_QC_AGGREGATE.csv")
    text = f"""# Prediction Regeneration QC

Canonical out-of-fold predictions were regenerated using the locked V0.3.1 code and 5×10 split design. There is one held-out prediction per eligible patient in each repeat, followed by arithmetic-mean aggregation across 10 repeats. The aggregate QC table records per-model patient counts, repeat/fold counts, missing predictions, and probability ranges.

Two patient-level CSVs were saved outside the repository under a mode-0700 directory, with files chmod 0600. They contain pseudonymous patient tokens, phenotype labels, repeat/fold assignment, and OOF predictions; they are excluded from Git, ZIP, and the public package. This report intentionally omits their local path and hashes.
"""
    (out / "02_CANONICAL_OOF" / "PREDICTION_REGENERATION_QC.md").write_text(text, encoding="utf-8")


def write_cohort_flow(raw: pd.DataFrame, selected: pd.DataFrame, all_frame: pd.DataFrame, primary: pd.DataFrame, cc: pd.DataFrame, out: Path) -> None:
    diagnosis = all_frame["diagnosis_text"].fillna("").astype(str).str.strip().ne("")
    rows = [
        {"stage": "raw_source_rows", "N": len(raw), "AMI_n": np.nan, "non_AMI_n": np.nan, "definition": "raw master rows; count only"},
        {"stage": "unique_patients_after_frozen_row_selection", "N": int(all_frame.research_patient_id.nunique()), "AMI_n": np.nan, "non_AMI_n": np.nan, "definition": "one source row per patient using frozen V0.2 selection rule"},
        {"stage": "discharge_diagnosis_available", "N": int(diagnosis.sum()), "AMI_n": np.nan, "non_AMI_n": np.nan, "definition": "nonempty discharge diagnosis"},
        {"stage": "definite_AMI_phenotype_before_core_filter", "N": int(all_frame.phenotype_class.eq("A_definite_AMI").sum()), "AMI_n": int(all_frame.phenotype_class.eq("A_definite_AMI").sum()), "non_AMI_n": 0, "definition": "frozen diagnosis-text rule"},
        {"stage": "definite_non_AMI_CAD_before_core_filter", "N": int(all_frame.phenotype_class.eq("B_definite_nonAMI_CAD").sum()), "AMI_n": 0, "non_AMI_n": int(all_frame.phenotype_class.eq("B_definite_nonAMI_CAD").sum()), "definition": "frozen diagnosis-text rule"},
        {"stage": "core_CBC_available", "N": int(all_frame.core_required_available.sum()), "AMI_n": np.nan, "non_AMI_n": np.nan, "definition": "absolute Neut, Lymph, Mono, and PLT available"},
        {"stage": "primary_analysis", "N": len(primary), "AMI_n": int(primary.y_primary.sum()), "non_AMI_n": int(len(primary) - primary.y_primary.sum()), "definition": "definite AMI vs definite non-AMI CAD with required Core CBC"},
        {"stage": "fibrinogen_complete_case", "N": len(cc), "AMI_n": int(cc.y_primary.sum()), "non_AMI_n": int(len(cc) - cc.y_primary.sum()), "definition": "Core-7 + fibrinogen complete; no fibrinogen imputation"},
    ]
    write_csv(pd.DataFrame(rows), out / "00_EXECUTIVE" / "COHORT_FLOW_FINAL.csv")


def render_figures(out: Path, rscript: str, log_path: Path) -> None:
    scripts = [
        "draw_canonical_roc.R",
        "draw_calibration.R",
        "draw_dca.R",
        "draw_core7_correlation.R",
        "draw_high_specificity_flow.R",
    ]
    r_dir = out / "13_FIGURE_SOURCES" / "R"
    for name in scripts:
        script = r_dir / name
        if not script.exists():
            raise FileNotFoundError(f"Required R figure script missing: {name}")
        add_log(log_path, f"Rendering aggregate figure with R: {name}")
        subprocess.run([rscript, str(script), str(out)], check=True)


def write_executive_and_gate(
    out: Path,
    age_gate: str,
    reconciliation: pd.DataFrame,
    primary_table: pd.DataFrame,
    deltas: pd.DataFrame,
    clinical: pd.DataFrame,
    dca: pd.DataFrame,
    figure5: pd.DataFrame,
    render_ok: bool,
) -> str:
    material = bool((reconciliation.status == "MATERIAL_MISMATCH").any())
    minor = bool(reconciliation.status.isin(["MINOR_NUMERIC_DIFFERENCE"]).any())
    dca_ok = not dca.empty and dca.N.nunique() == 1 and len(dca.model.unique()) == 6
    figure5_ok = bool(not figure5.empty and figure5.CI_present.all() and figure5.CI_status.eq("CI_AVAILABLE_MATCHES_FROZEN_REGISTRY").all())
    if age_gate != "AGE_1820_CANONICAL_LOCKED":
        gate = "WP2_HOLD_AGE_DEFINITION_UNRESOLVED"
    elif material:
        gate = "WP2_HARD_STOP_CANONICAL_REGENERATION_MISMATCH"
    elif minor or not dca_ok or not figure5_ok or not render_ok:
        gate = "WP2_CONDITIONAL_PASS_MINOR_REPORTING_GAPS"
    else:
        gate = "WP2_PASS_READY_FOR_MANUSCRIPT_REVISION"
    gate_text = f"""# WP2 Gate

**Gate:** `{gate}`

- Age: `{age_gate}`
- Canonical numeric reconciliation material mismatch: `{material}`
- Minor numeric differences: `{minor}`
- Same-sample clinical DCA generated: `{dca_ok}`
- Figure 5 confidence-interval audit complete: `{figure5_ok}`
- R figure source/render checks completed: `{render_ok}`
- Manuscript edited: `NO`
- Point-by-point response drafted: `NO`
- PR merged: `NO`

Patient-level OOF predictions remain local-only and are not committed.
"""
    (out / "00_EXECUTIVE" / "WP2_GATE.md").write_text(gate_text, encoding="utf-8")

    def get_model(label: str, cohort: str) -> pd.Series:
        q = primary_table.loc[(primary_table.model == label) & (primary_table.cohort_version == cohort)]
        if len(q) != 1:
            raise RuntimeError(f"Missing primary result row: {label}/{cohort}")
        return q.iloc[0]
    core = get_model("Core-7", "primary_full_1820")
    piv = get_model("PIV", "primary_full_1820")
    enh = get_model("Enhanced", "primary_full_1820")
    enh_cc = get_model("Enhanced", "fibrinogen_complete_case_1705")
    key_delta = deltas.loc[deltas.comparison == "Primary Core minus PIV"].iloc[0]
    fbg_delta = deltas.loc[deltas.comparison == "Primary Fibrinogen complete-case Enhanced minus Core"].iloc[0]
    clinical_full = clinical.loc[
        (clinical.record_type == "model_performance")
        & (clinical.cohort_version == "primary_full_1820")
        & (clinical.model != "Clinical + Enhanced")
    ]
    clinical_cc = clinical.loc[
        (clinical.record_type == "model_performance")
        & (clinical.cohort_version == "fibrinogen_complete_case_1705")
    ]
    clinical_cc_deltas = clinical.loc[
        (clinical.record_type == "paired_delta_auc")
        & (clinical.cohort_version == "fibrinogen_complete_case_1705")
    ]
    paragraphs = []
    for _, row in clinical_full.iterrows():
        paragraphs.append(f"- {row.model}: N={int(row.N)}, AUC={fmt(row.AUC)}, 95% CI {fmt(row.AUC_CI_lower)}–{fmt(row.AUC_CI_upper)}, Brier={fmt(row.Brier)}.")
    cc_paragraphs = []
    for _, row in clinical_cc.iterrows():
        cc_paragraphs.append(f"- {row.model}: N={int(row.N)}, AUC={fmt(row.AUC)}, 95% CI {fmt(row.AUC_CI_lower)}–{fmt(row.AUC_CI_upper)}, Brier={fmt(row.Brier)}.")
    cc_delta_paragraphs = []
    for _, row in clinical_cc_deltas.iterrows():
        cc_delta_paragraphs.append(f"- {row.comparison}: ΔAUC={fmt(row.delta_AUC)}, 95% CI {fmt(row.delta_CI_lower)}–{fmt(row.delta_CI_upper)}.")
    clinical_enhanced_historical = clinical.loc[
        (clinical.record_type == "model_performance")
        & (clinical.cohort_version == "primary_full_1820")
        & (clinical.model == "Clinical + Enhanced")
    ].iloc[0]
    summary = f"""# WP2 Executive Summary

## Decision

`{gate}`. This is an analysis-repair package for retrospective single-center AMI phenotype discrimination among CAD patients. It is not future-event prediction, temporal transportability, clinical diagnosis, triage, or external validation.

## Cohort and canonical models

- Primary cohort: N={int(core.N)}; AMI={int(core.AMI_n)} ({100*core.AMI_n/core.N:.1f}%); non-AMI CAD={int(core.non_AMI_n)}.
- Fibrinogen complete-case cohort: N={int(enh_cc.N)}; AMI={int(enh_cc.AMI_n)}; non-AMI={int(enh_cc.non_AMI_n)}.
- Age gate: `{age_gate}`. Canonical model vector has 1820/1820 ages; the submitted Table 1 1818 count is not reproduced and remains a separate reporting discrepancy for WP3.
- Core-7: AUC={fmt(core.AUC)}, 95% CI {fmt(core.AUC_CI_lower)}–{fmt(core.AUC_CI_upper)}, Brier={fmt(core.Brier)}, calibration intercept={fmt(core.calibration_intercept)}, slope={fmt(core.calibration_slope)}.
- PIV: AUC={fmt(piv.AUC)}, 95% CI {fmt(piv.AUC_CI_lower)}–{fmt(piv.AUC_CI_upper)}.
- Core−PIV: ΔAUC={fmt(key_delta.delta_auc_a_minus_b)}, 95% CI {fmt(key_delta.delta_auc_ci_lower)}–{fmt(key_delta.delta_auc_ci_upper)}; N={int(key_delta.n_common)}, paired on identical patients/folds.
- Enhanced, historical full-cohort canonical imputation branch: AUC={fmt(enh.AUC)}, 95% CI {fmt(enh.AUC_CI_lower)}–{fmt(enh.AUC_CI_upper)}, N={int(enh.N)}. This exact existing fold-local median pipeline is reproduced only for freeze reconciliation.
- Enhanced complete case: AUC={fmt(enh_cc.AUC)}, 95% CI {fmt(enh_cc.AUC_CI_lower)}–{fmt(enh_cc.AUC_CI_upper)}, N={int(enh_cc.N)}. Enhanced−Core paired complete-case ΔAUC={fmt(fbg_delta.delta_auc_a_minus_b)}, 95% CI {fmt(fbg_delta.delta_auc_ci_lower)}–{fmt(fbg_delta.delta_auc_ci_upper)}.

## Clinical increment and DCA

Full-cohort OOF results not requiring fibrinogen:
{chr(10).join(paragraphs)}

The full-cohort Clinical + Enhanced result (AUC={fmt(clinical_enhanced_historical.AUC)}) reproduces the historical fold-local fibrinogen-imputation branch for freeze reconciliation only. No new fibrinogen imputation is used for reviewer-facing Enhanced comparisons. Those comparisons use the shared complete-case cohort:
{chr(10).join(cc_paragraphs)}

Paired complete-case comparisons:
{chr(10).join(cc_delta_paragraphs)}

The reviewer-facing DCA uses the fibrinogen-complete sample N={int(dca.N.iloc[0]) if not dca.empty else 0}, with all four clinical models, treat-all, and treat-none on identical patients. It is exploratory and is not evidence of clinical utility.

## Other required analyses

- Canonical result reconciliation: {int(reconciliation.status.eq('MATCH').sum())} MATCH, {int(reconciliation.status.eq('ROUNDING_ONLY').sum())} ROUNDING_ONLY, {int(reconciliation.status.eq('MINOR_NUMERIC_DIFFERENCE').sum())} MINOR_NUMERIC_DIFFERENCE, {int(reconciliation.status.eq('MATERIAL_MISMATCH').sum())} MATERIAL_MISMATCH.
- Traditional indices: NLR, PLR, MLR, SII, SIRI, PIV, and HRR; PIV remains the prespecified comparator.
- Core-7: Spearman matrix and frozen 300-development-bootstrap stability summary provided; no variable removed.
- Calibration and ROC source data use regenerated 5×10 OOF predictions. The legacy 20-repeat figure branch is superseded in this review package.
- Figure 5: {int(figure5.CI_present.sum())}/{len(figure5)} displayed AUCs have a 95% CI in the frozen source; no new temporal models were fit.
- Date-axis numbers are preserved and relabeled for WP3 as `EXPLORATORY DEIDENTIFIED DATE-AXIS SENSITIVITY ANALYSIS`; they do not establish temporal validation or transportability.
- Troponin pooled comparator: not performed; unified assay, ULN, and timing are invalid/incomplete.
- Patient-level OOF files: saved locally with restrictive permissions; absent from repository and public ZIP.

## Scope and risks

- The two-person Table 1 age discrepancy is not resolved at the individual-record cause level; WP3 must rebuild that descriptive row from the locked age vector.
- The frozen CBC-to-index-angiography encounter link remains unverified, so no admission-first, pre-diagnosis, pre-angiography, or treatment-naive claim is supported.
- Discharge-diagnosis phenotypes are not independently adjudicated; the high-specificity subset is a strict text-rule sensitivity only.
- Bootstrap intervals resample fixed patient-level mean OOF predictions and do not include full model-development uncertainty.

Manuscript rewriting, response-letter drafting, and PR merge were not performed.
"""
    (out / "00_EXECUTIVE" / "WP2_EXECUTIVE_SUMMARY.md").write_text(summary, encoding="utf-8")
    return gate


def main() -> int:
    args = parse_args()
    out = args.out.resolve()
    for name in ["00_EXECUTIVE", "01_AGE", "02_CANONICAL_OOF", "03_PRIMARY_PERFORMANCE", "04_CLINICAL_INCREMENTAL", "05_FIBRINOGEN", "06_TRADITIONAL_INDICES", "07_COLLINEARITY", "08_CALIBRATION", "09_DCA", "10_HIGH_SPECIFICITY", "11_FIGURE5", "12_TEMPORAL_CONTEXT", "13_FIGURE_SOURCES", "13_FIGURE_SOURCES/R", "14_CODE"]:
        (out / name).mkdir(parents=True, exist_ok=True)
    log_path = out / "14_CODE" / "run.log"
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")

    if args.render_existing_aggregates:
        add_log(log_path, "Resuming from existing aggregate outputs; model fitting skipped")
        age_lock = (out / "01_AGE" / "AGE_CANONICAL_LOCK.md").read_text(encoding="utf-8")
        if "AGE_1820_CANONICAL_LOCKED" not in age_lock:
            raise RuntimeError("Existing age lock is absent or not canonical; cannot finalize WP2")
        reconciliation = pd.read_csv(out / "00_EXECUTIVE" / "CANONICAL_REGENERATION_RECONCILIATION.csv")
        primary_table = pd.read_csv(out / "03_PRIMARY_PERFORMANCE" / "PRIMARY_MODEL_PERFORMANCE_CANONICAL.csv")
        deltas = pd.read_csv(out / "03_PRIMARY_PERFORMANCE" / "PRIMARY_PAIRED_DELTAS_CANONICAL.csv")
        clinical = pd.read_csv(out / "04_CLINICAL_INCREMENTAL" / "CLINICAL_INCREMENTAL_PERFORMANCE_CANONICAL.csv")
        dca = pd.read_csv(out / "09_DCA" / "DCA_CANONICAL_SOURCE.csv")
        figure5 = pd.read_csv(out / "11_FIGURE5" / "FIGURE5_FINAL_CI_TABLE.csv")
        if (reconciliation.status == "MATERIAL_MISMATCH").any():
            raise RuntimeError("Existing reconciliation contains a material mismatch; preserve hard stop")
        render_figures(out, args.rscript, log_path)
        record_analysis_code_hashes(out)
        render_ok = all(
            (out / "13_FIGURE_SOURCES" / f"{stem}.{ext}").is_file()
            for stem in ["Figure_ROC_Canonical_OOF", "Figure_Calibration_Canonical_OOF", "Figure_DCA_Canonical_OOF", "Figure_Core7_Spearman_Correlation", "Figure_HighSpecificity_Flow"]
            for ext in ["pdf", "tiff", "png"]
        )
        gate = write_executive_and_gate(out, "AGE_1820_CANONICAL_LOCKED", reconciliation, primary_table, deltas, clinical, dca, figure5, render_ok)
        add_log(log_path, f"WP2 render-only finalization finished with gate={gate}; figures_ok={render_ok}")
        return 0 if gate == "WP2_PASS_READY_FOR_MANUSCRIPT_REVISION" else 4

    log_path.write_text("", encoding="utf-8")
    add_log(log_path, "WP2 targeted analysis run started")

    expected = {
        "source": (args.source.resolve(), EXPECTED_SOURCE_SHA256),
        "v02_script": (args.v02_script.resolve(), EXPECTED_V02_SHA256),
        "v031_script": (args.v031_script.resolve(), EXPECTED_V031_SHA256),
    }
    observed = {}
    for label, (path, wanted) in expected.items():
        actual = sha256(path)
        observed[label] = actual
        if actual != wanted:
            raise RuntimeError(f"Frozen source hash mismatch for {label}; stop without fitting")
    registry = pd.read_csv(args.registry)
    registry_hash = sha256(args.registry.resolve())

    v02 = load_module(args.v02_script.resolve(), "hits_wp2_v02_frozen")
    v031 = load_module(args.v031_script.resolve(), "hits_wp2_v031_frozen")
    v031.LOG_PATH = log_path
    raw = pd.read_csv(args.source, low_memory=False)
    selected, _ = v02.select_one_row_per_patient(raw)
    full_frame = v02.benchmark_indices(v02.build_patient_frame(selected))
    primary = full_frame.loc[full_frame.primary_analysis].reset_index(drop=True)
    cc = primary.loc[primary[v031.ENHANCED].notna().all(axis=1)].reset_index(drop=True)
    if len(primary) != EXPECTED_PRIMARY_N or int(primary.y_primary.sum()) != EXPECTED_AMI_N:
        raise RuntimeError("Frozen primary cohort count mismatch; stop before model fitting")
    if len(cc) != EXPECTED_FBG_CC_N or int(cc.y_primary.sum()) != EXPECTED_FBG_CC_AMI_N:
        raise RuntimeError("Frozen fibrinogen complete-case count mismatch; stop before model fitting")
    add_log(log_path, f"Verified source and cohort: raw_rows={len(raw)} selected_patients={full_frame.research_patient_id.nunique()} primary_N={len(primary)} AMI={int(primary.y_primary.sum())} fbg_CC_N={len(cc)}")

    age_gate = build_age_outputs(full_frame, selected, v02, out)
    write_cohort_flow(raw, selected, full_frame, primary, cc, out)
    fibrinogen_outputs(primary, cc, out)
    high_flow = high_specificity_outputs(args.highspecific_flow_source.resolve(), out)
    figure5 = figure5_ci_audit(args.figure5_source.resolve(), registry, out)
    if age_gate != "AGE_1820_CANONICAL_LOCKED":
        (out / "00_EXECUTIVE" / "WP2_GATE.md").write_text("# WP2 Gate\n\n**WP2_HOLD_AGE_DEFINITION_UNRESOLVED**\n\nAge could not be locked to the canonical 1820 vector; no clinical-model regeneration was started.\n", encoding="utf-8")
        add_log(log_path, f"Stopped at age gate: {age_gate}")
        return 2

    primary_specs = [v031.ModelSpec("Continuous_HITS_Core", tuple(v031.CORE), "elastic", False)] + [v031.ModelSpec(marker, (marker,), "ordinary", True) for marker in v031.BENCHMARKS]
    enhanced_specs = [v031.ModelSpec("Continuous_HITS_Enhanced", tuple(v031.ENHANCED), "elastic", True)]
    fbg_cc_specs = [
        v031.ModelSpec("Continuous_HITS_Core", tuple(v031.CORE), "elastic", False),
        v031.ModelSpec("Continuous_HITS_Enhanced", tuple(v031.ENHANCED), "elastic", False),
    ]
    clinical_specs = [
        v031.ModelSpec("Clinical", tuple(v031.CLINICAL), "elastic", True),
        v031.ModelSpec("Clinical_Plus_PIV", tuple(v031.CLINICAL + ["PIV"]), "elastic", True),
        v031.ModelSpec("Clinical_Plus_Core", tuple(v031.CLINICAL + v031.CORE), "elastic", True),
        v031.ModelSpec("Clinical_Plus_Enhanced", tuple(v031.CLINICAL + v031.ENHANCED), "elastic", True),
    ]
    record_parts, tuning_parts = [], []
    for frame, analysis, target, specs in [
        (primary, "primary_core", "y_primary", primary_specs),
        (primary, "primary_enhanced_imputed", "y_primary", enhanced_specs),
        (cc, "primary_fbg_complete_case", "y_primary", fbg_cc_specs),
        (primary, "primary_clinical", "y_primary", clinical_specs),
        (cc, "primary_clinical_fbg_complete_case", "y_primary", clinical_specs),
    ]:
        rec, tune = run_group(v031, frame, analysis, target, specs, log_path)
        record_parts.append(rec)
        tuning_parts.append(tune)
    records = pd.concat(record_parts, ignore_index=True)
    tuning = pd.concat(tuning_parts, ignore_index=True)
    performance = v031.performance_table(records, EXPECTED_BOOTSTRAP_N)
    write_csv(performance, out / "14_CODE" / "canonical_performance_all_models.csv")
    write_csv(tuning, out / "14_CODE" / "canonical_tuning_records_aggregate.csv")
    primary_table, _ = build_primary_tables(performance, out)
    deltas = make_deltas(v031, records, out)
    clinical_tables(performance, deltas, primary, out)
    traditional_table(performance, out)
    collinearity_outputs(primary, args.v031_output.resolve(), out)

    historical_fbg = pd.read_csv(args.v031_output / "10_fibrinogen_complete_case_sensitivity.csv")
    historical_deltas = pd.read_csv(args.v031_output / "07_paired_delta_auc_bootstrap.csv")
    reconciliation = make_reconciliation(performance, deltas, registry, historical_fbg, historical_deltas, out)
    write_prediction_qc(v031, records, args.local_predictions_dir, out)
    write_pipeline_lock(out, observed["source"], observed["v02_script"], observed["v031_script"], registry_hash)
    source_paths = {
        "master_cohort_cleaned.csv": args.source.resolve(),
        "V0.2_cohort_script.py": args.v02_script.resolve(),
        "V0.3.1_canonical_pipeline.py": args.v031_script.resolve(),
        "V0.5.2_canonical_result_registry.csv": args.registry.resolve(),
        "V0.3.1_frozen_fibrinogen_outputs.csv": (args.v031_output / "10_fibrinogen_complete_case_sensitivity.csv").resolve(),
        "V0.3.1_frozen_paired_deltas.csv": (args.v031_output / "07_paired_delta_auc_bootstrap.csv").resolve(),
        "V0.3.1_frozen_stability.csv": (args.v031_output / "16_variable_stability.csv").resolve(),
        "Figure5_frozen_source.csv": args.figure5_source.resolve(),
        "high_specificity_flow_source.csv": args.highspecific_flow_source.resolve(),
    }
    source_and_environment_hashes(source_paths, out, v031)
    record_analysis_code_hashes(out)

    if (reconciliation.status == "MATERIAL_MISMATCH").any():
        gate_text = "# WP2 Gate\n\n**WP2_HARD_STOP_CANONICAL_REGENERATION_MISMATCH**\n\nA material discrepancy was found against the frozen results. Per WP2 authorization, no DCA or further reviewer analysis was run. See `CANONICAL_REGENERATION_RECONCILIATION.csv`.\n"
        (out / "00_EXECUTIVE" / "WP2_GATE.md").write_text(gate_text, encoding="utf-8")
        add_log(log_path, "Hard stop: material canonical regeneration mismatch")
        return 3

    clinical_table = pd.read_csv(out / "04_CLINICAL_INCREMENTAL" / "CLINICAL_INCREMENTAL_PERFORMANCE_CANONICAL.csv")
    calib, prob_summary = calibration_outputs(v031, records, out)
    roc_source(v031, records, out)
    dca = dca_outputs(v031, records, out)
    temporal_context(registry, args.highspecific_flow_source.resolve(), out)
    dca_gate_ok = not dca.empty and dca.N.nunique() == 1 and len(dca.model.unique()) == 6
    date_values = pd.read_csv(out / "12_TEMPORAL_CONTEXT" / "DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv")
    if date_values.analysis_label.nunique() != 1:
        raise RuntimeError("Frozen date-axis label unexpectedly varies")
    (out / "02_CANONICAL_OOF" / "OOF_PREDICTION_METADATA.csv").write_text(
        "source,aggregation,outer_cv,inner_cv,patient_level_rows_public\n"
        "canonical V0.3.1 pipeline,arithmetic mean of 10 held-out probabilities,5-fold x 10 repeats,5-fold,NO\n",
        encoding="utf-8",
    )
    render_figures(out, args.rscript, log_path)
    render_ok = all(any((out / "13_FIGURE_SOURCES").glob(f"{stem}.{ext}")) for stem in ["Figure_ROC_Canonical_OOF", "Figure_Calibration_Canonical_OOF", "Figure_DCA_Canonical_OOF", "Figure_Core7_Spearman_Correlation", "Figure_HighSpecificity_Flow"] for ext in ["pdf", "tiff", "png"])
    gate = write_executive_and_gate(out, age_gate, reconciliation, primary_table, deltas, clinical_table, dca, figure5, render_ok)
    add_log(log_path, f"WP2 finished with gate={gate}; dca_N={dca.N.nunique() and int(dca.N.iloc[0]) if not dca.empty else 0}; figures_ok={render_ok}")
    return 0 if gate == "WP2_PASS_READY_FOR_MANUSCRIPT_REVISION" else 4


if __name__ == "__main__":
    raise SystemExit(main())
