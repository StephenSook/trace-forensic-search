"""Tests for the synthetic cases dataset quality.

Validates structure, constraints, and ground-truth pair integrity.
Pure-Python — no DB needed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def raw_cases():
    from config import SYNTHETIC_CASES_PATH

    with open(SYNTHETIC_CASES_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validated_cases():
    from ingest import load_cases

    return load_cases()


def test_exactly_60_cases(raw_cases):
    assert len(raw_cases) == 60


def test_all_cases_validate_against_schema(validated_cases):
    assert len(validated_cases) == 60


def test_no_duplicate_case_ids(validated_cases):
    ids = [c.case_id for c in validated_cases]
    assert len(ids) == len(set(ids))


def test_all_required_fields_non_empty(validated_cases):
    for c in validated_cases:
        assert c.physical_text.strip(), f"{c.case_id}: empty physical_text"
        assert c.circumstances.strip(), f"{c.case_id}: empty circumstances"
        assert c.clothing.strip(), f"{c.case_id}: empty clothing"


def test_case_types_balanced(validated_cases):
    types = {c.case_type for c in validated_cases}
    assert types == {"missing", "unidentified"}
    missing = [c for c in validated_cases if c.case_type == "missing"]
    unidentified = [c for c in validated_cases if c.case_type == "unidentified"]
    assert len(missing) == 30
    assert len(unidentified) == 30


def test_ground_truth_pairs_exist(validated_cases):
    ids = {c.case_id for c in validated_cases}
    for n in range(1, 7):
        mp = f"MP-{n:03d}"
        up = f"UP-{n:03d}"
        assert mp in ids, f"Ground-truth pair missing: {mp}"
        assert up in ids, f"Ground-truth pair missing: {up}"


def test_ground_truth_pair_states_match(validated_cases):
    by_id = {c.case_id: c for c in validated_cases}
    for n in range(1, 7):
        mp = by_id[f"MP-{n:03d}"]
        up = by_id[f"UP-{n:03d}"]
        assert mp.state == up.state, (
            f"Pair {n}: MP state={mp.state}, UP state={up.state}"
        )


def test_ground_truth_pair_sex_match(validated_cases):
    by_id = {c.case_id: c for c in validated_cases}
    for n in range(1, 7):
        mp = by_id[f"MP-{n:03d}"]
        up = by_id[f"UP-{n:03d}"]
        assert mp.sex == up.sex, (
            f"Pair {n}: MP sex={mp.sex}, UP sex={up.sex}"
        )


def test_ground_truth_pair_types(validated_cases):
    by_id = {c.case_id: c for c in validated_cases}
    for n in range(1, 7):
        assert by_id[f"MP-{n:03d}"].case_type == "missing"
        assert by_id[f"UP-{n:03d}"].case_type == "unidentified"


def test_demo_pair_content(validated_cases):
    """The demo pair (MP-001/UP-001) must have the Tennessee eagle-tattoo content."""
    by_id = {c.case_id: c for c in validated_cases}

    mp = by_id["MP-001"]
    assert mp.state == "TN"
    assert "eagle" in mp.physical_text.lower()
    assert "tattoo" in mp.physical_text.lower()
    assert "tennessee" in mp.circumstances.lower() or mp.state == "TN"

    up = by_id["UP-001"]
    assert up.state == "TN"
    assert "avian" in up.physical_text.lower() or "tattoo" in up.physical_text.lower()


def test_all_states_are_valid_codes(validated_cases):
    import re

    for c in validated_cases:
        assert re.match(r"^[A-Z]{2}$", c.state), f"{c.case_id}: bad state {c.state}"


def test_age_ranges_reasonable(validated_cases):
    for c in validated_cases:
        assert 0 <= c.age_low <= c.age_high <= 120, (
            f"{c.case_id}: age range {c.age_low}-{c.age_high}"
        )


def test_date_epochs_in_range(validated_cases):
    """Dates should fall between 2015 and 2025."""
    min_epoch = 1420070400   # 2015-01-01
    max_epoch = 1735689600   # 2025-01-01
    for c in validated_cases:
        assert min_epoch <= c.date_epoch <= max_epoch, (
            f"{c.case_id}: date_epoch {c.date_epoch} out of range"
        )


def test_date_iso_matches_epoch(validated_cases):
    """date_iso and date_epoch should refer to the same date."""
    from datetime import datetime, timezone

    for c in validated_cases:
        dt = datetime.fromtimestamp(c.date_epoch, tz=timezone.utc)
        expected_iso = dt.strftime("%Y-%m-%d")
        assert c.date_iso == expected_iso, (
            f"{c.case_id}: date_iso={c.date_iso} vs epoch→{expected_iso}"
        )


def test_point_ids_are_unique(validated_cases):
    from ingest import point_id_for

    pids = [point_id_for(c.case_id) for c in validated_cases]
    assert len(pids) == len(set(pids))
