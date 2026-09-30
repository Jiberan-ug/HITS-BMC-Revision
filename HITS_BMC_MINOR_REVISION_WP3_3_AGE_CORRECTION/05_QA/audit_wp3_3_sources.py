#!/usr/bin/env python3
"""Aggregate-only source audit for the WP3.3 age gate; no patient output."""

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

EXPECTED_HASHES = {
    "master": "f87691f5876ece3e70b2835284bf2412ed57edaf83ee7e198df6caa89669a660",
    "selector": "089924ec5a58d09c3e96bdedd2a9316690eebd3f70377a058760a90b267ad91a",
    "temporal_script": "480f3fb66ddd50ce09e8fb85ddf8edbfed834ff5f1b5d00e254c3a6f8b17e53d",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_selector(path):
    spec = importlib.util.spec_from_file_location("hits_wp33_selector", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--selector", type=Path, required=True)
    parser.add_argument("--temporal-script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for key, path in (("master", args.master), ("selector", args.selector), ("temporal_script", args.temporal_script)):
        if sha256(path) != EXPECTED_HASHES[key]:
            raise RuntimeError(f"{key} does not match the frozen source fingerprint.")

    selector = load_selector(args.selector)
    raw = pd.read_csv(args.master, low_memory=False)
    selected, _ = selector.select_one_row_per_patient(raw)
    frame = selector.build_patient_frame(selected)
    primary = frame.loc[frame["primary_analysis"]].copy()
    birth_primary = selector.parse_datetime(selected[selector.COL["birth"]]).reset_index(drop=True)
    if len(primary) != 1820 or int(primary["y_primary"].eq(1).sum()) != 453:
        raise RuntimeError("The source/selector does not reproduce the frozen cohort.")

    rows = []
    for group, sub in (
        ("overall", primary),
        ("AMI", primary.loc[primary["y_primary"].eq(1)]),
        ("non_AMI_CAD", primary.loc[primary["y_primary"].eq(0)]),
    ):
        years = sub["admission_datetime"].dt.year
        group_mask = frame["primary_analysis"]
        if group == "AMI":
            group_mask = group_mask & frame["y_primary"].eq(1)
        elif group == "non_AMI_CAD":
            group_mask = group_mask & frame["y_primary"].eq(0)
        rows.append({
            "group": group,
            "cohort_n": len(sub),
            "birth_primary_parseable_n": int(birth_primary.loc[group_mask].notna().sum()),
            "admission_date_parseable_n": int(years.notna().sum()),
            "admission_date_missing_n": int(years.isna().sum()),
            "admission_date_pre_2020_n": int(years.lt(2020).sum()),
            "admission_date_2020_2026_n": int(years.between(2020, 2026).sum()),
            "admission_date_post_2026_n": int(years.gt(2026).sum()),
            "source_confirmed_target_episode_date_n": 0,
            "valid_target_anchored_age_n": "NOT_ESTIMABLE",
            "status": "NO_SOURCE_CONFIRMED_TARGET_EPISODE_DATE",
        })

    temporal_text = args.temporal_script.read_text(encoding="utf-8")
    temporal_checks = [
        {"check": "frozen_master_hash", "result": sha256(args.master), "interpretation": "SOURCE_FINGERPRINT"},
        {"check": "historical_selector_hash", "result": sha256(args.selector), "interpretation": "SOURCE_FINGERPRINT"},
        {"check": "frozen_temporal_script_hash", "result": sha256(args.temporal_script), "interpretation": "SOURCE_FINGERPRINT"},
        {"check": "temporal_cut_literal", "result": str('cut = pd.Timestamp("2015-01-01")' in temporal_text), "interpretation": "CODE_LEVEL_CHECK"},
        {"check": "temporal_group_uses_cbc_datetime", "result": str('out["shifted_CBC_date"] = out["cbc_datetime"]' in temporal_text and 'has_date = out["cbc_datetime"].notna()' in temporal_text), "interpretation": "CODE_LEVEL_CHECK"},
    ]
    (args.output / "01_AGE").mkdir(parents=True, exist_ok=True)
    (args.output / "05_QA").mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "01_AGE" / "AGE_TARGET_HOSPITALIZATION_QC.csv", rows)
    write_csv(args.output / "05_QA" / "SOURCE_LINEAGE_CROSSCHECK.csv", temporal_checks)
    print(json.dumps({"cohort_n": len(primary), "ami_n": int(primary["y_primary"].eq(1).sum()), "admission_date_n": rows[0]["admission_date_parseable_n"], "target_date_status": rows[0]["status"], "temporal_cut_literal": temporal_checks[-2]["result"], "temporal_group_uses_cbc_datetime": temporal_checks[-1]["result"]}, indent=2))


if __name__ == "__main__":
    main()
