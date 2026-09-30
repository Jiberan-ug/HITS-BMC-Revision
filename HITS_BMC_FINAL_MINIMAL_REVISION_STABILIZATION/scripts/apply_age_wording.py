#!/usr/bin/env python3
"""Apply two text-only age-wording edits to WP3.2 manuscript copies."""

import argparse
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX


REPLACEMENTS = (
    (
        "the prespecified baseline clinical model included age, sex, hypertension, and diabetes; smoking was not available.",
        "the prespecified baseline clinical model included age, sex, hypertension, and diabetes; smoking was not sufficiently available for inclusion.",
    ),
    (
        "Because admission dates were unavailable for many patients, age was derived using the available CBC/WBC timestamp as a fallback reference date and was therefore not uniformly anchored to the index angiography hospitalization.",
        "The retained deidentified dataset did not permit uniform reconstruction of a precise clinical index date for all demographic variables.",
    ),
)


def replace_in_runs(paragraph, old, new, mark=False):
    full = "".join(run.text for run in paragraph.runs)
    if full.count(old) != 1:
        return False
    start = full.index(old)
    end = start + len(old)
    position = 0
    first = True
    first_run = None
    trailing_text = ""
    for run in paragraph.runs:
        original = run.text
        run_start, run_end = position, position + len(original)
        position = run_end
        if run_end <= start or run_start >= end:
            continue
        prefix = original[: max(0, start - run_start)]
        suffix = original[max(0, end - run_start) :] if run_end >= end else ""
        if mark:
            if first:
                first_run = run
            run.text = prefix + suffix
            if first and run_end >= end:
                trailing_text = suffix
                run.text = prefix
        else:
            run.text = prefix + (new if first else "") + suffix
        first = False
    if mark:
        replacement = paragraph.add_run(new)
        if first_run._r.rPr is not None:
            replacement._r.insert(0, deepcopy(first_run._r.rPr))
        replacement.font.highlight_color = WD_COLOR_INDEX.YELLOW
        first_run._r.addnext(replacement._r)
        if trailing_text:
            suffix_run = paragraph.add_run(trailing_text)
            if first_run._r.rPr is not None:
                suffix_run._r.insert(0, deepcopy(first_run._r.rPr))
            replacement._r.addnext(suffix_run._r)
    assert "".join(run.text for run in paragraph.runs) == full.replace(old, new)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mark", action="store_true")
    args = parser.parse_args()
    document = Document(args.source)
    before = [paragraph.text for paragraph in document.paragraphs]
    for old, new in REPLACEMENTS:
        hits = [paragraph for paragraph in document.paragraphs if old in paragraph.text]
        if len(hits) != 1 or not replace_in_runs(hits[0], old, new, mark=args.mark):
            raise RuntimeError(f"Expected one exact source sentence, found {len(hits)}: {old[:60]}")
    after = [paragraph.text for paragraph in document.paragraphs]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if len(changed) != 2:
        raise RuntimeError(f"Unexpected paragraph change count: {changed}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(args.output)
    print(f"{args.output.name}: edited paragraphs {changed}")


if __name__ == "__main__":
    main()
