"""Unit tests for backend/filters.py — pure, no DB required.

Tests go beyond None-vs-not-None: they introspect the Filter's must
conditions to verify the correct field keys, match values, range bounds,
and clause counts are produced by build_filter().
"""
from __future__ import annotations

import pytest

from filters import _iso_to_epoch, build_filter
from schemas import SearchFilters


# ── Helpers ──────────────────────────────────────────────────────────────

def _must_conditions(f):
    """Return list of FieldCondition objects from a Filter's must clauses."""
    return [c.field for c in f.must]


def _find_condition(f, key: str):
    """Find the FieldCondition targeting a specific payload key."""
    for cond in _must_conditions(f):
        if cond.key == key:
            return cond
    return None


# ── Guard: empty / None ─────────────────────────────────────────────────

def test_no_filters_returns_none():
    assert build_filter(SearchFilters()) is None


def test_none_input_returns_none():
    assert build_filter(None) is None


# ── case_type ────────────────────────────────────────────────────────────

def test_case_type_missing():
    f = build_filter(SearchFilters(case_type="missing"))
    cond = _find_condition(f, "case_type")
    assert cond is not None
    assert cond.match.keyword == "missing"


def test_case_type_unidentified():
    f = build_filter(SearchFilters(case_type="unidentified"))
    cond = _find_condition(f, "case_type")
    assert cond.match.keyword == "unidentified"


# ── state ────────────────────────────────────────────────────────────────

def test_state_exact_match():
    f = build_filter(SearchFilters(state="TN"))
    cond = _find_condition(f, "state")
    assert cond is not None
    assert cond.match.keyword == "TN"


def test_state_uppercased_defensive():
    """filters.py uppercases state defensively even though the schema
    validator already rejects lowercase. model_construct bypasses
    validation to exercise the belt-and-suspenders path."""
    raw = SearchFilters.model_construct(state="tn")
    f = build_filter(raw)
    cond = _find_condition(f, "state")
    assert cond.match.keyword == "TN"


# ── sex ──────────────────────────────────────────────────────────────────

def test_sex_male_includes_unknown():
    f = build_filter(SearchFilters(sex="Male"))
    cond = _find_condition(f, "sex")
    assert cond is not None
    assert set(cond.match.keywords) == {"Male", "Unknown"}


def test_sex_female_includes_unknown():
    f = build_filter(SearchFilters(sex="Female"))
    cond = _find_condition(f, "sex")
    assert set(cond.match.keywords) == {"Female", "Unknown"}


# ── age overlap ──────────────────────────────────────────────────────────

def test_age_both_bounds():
    """age_low=30, age_high=40 → age_high>=30 AND age_low<=40."""
    f = build_filter(SearchFilters(age_low=30, age_high=40))
    high_cond = _find_condition(f, "age_high")
    low_cond = _find_condition(f, "age_low")
    assert high_cond is not None
    assert high_cond.range.gte == 30.0
    assert low_cond is not None
    assert low_cond.range.lte == 40.0


def test_age_low_only():
    f = build_filter(SearchFilters(age_low=25))
    high_cond = _find_condition(f, "age_high")
    assert high_cond.range.gte == 25.0
    # No age_low clause when age_high filter is not set
    assert _find_condition(f, "age_low") is None


def test_age_high_only():
    f = build_filter(SearchFilters(age_high=50))
    low_cond = _find_condition(f, "age_low")
    assert low_cond.range.lte == 50.0
    assert _find_condition(f, "age_high") is None


def test_age_boundary_zero():
    """age_low=0 is valid (newborns)."""
    f = build_filter(SearchFilters(age_low=0))
    high_cond = _find_condition(f, "age_high")
    assert high_cond.range.gte == 0.0


def test_age_boundary_120():
    """age_high=120 is the schema max."""
    f = build_filter(SearchFilters(age_high=120))
    low_cond = _find_condition(f, "age_low")
    assert low_cond.range.lte == 120.0


# ── date range ───────────────────────────────────────────────────────────

def test_date_range_both():
    f = build_filter(SearchFilters(date_from="2019-01-01", date_to="2020-12-31"))
    conditions = _must_conditions(f)
    epoch_conds = [c for c in conditions if c.key == "date_epoch"]
    assert len(epoch_conds) == 2
    gtes = [c.range.gte for c in epoch_conds if c.range.gte is not None]
    ltes = [c.range.lte for c in epoch_conds if c.range.lte is not None]
    assert len(gtes) == 1
    assert len(ltes) == 1
    assert gtes[0] == float(_iso_to_epoch("2019-01-01"))
    assert ltes[0] == float(_iso_to_epoch("2020-12-31"))


def test_date_from_only():
    f = build_filter(SearchFilters(date_from="2019-06-15"))
    epoch_conds = [c for c in _must_conditions(f) if c.key == "date_epoch"]
    assert len(epoch_conds) == 1
    assert epoch_conds[0].range.gte == float(_iso_to_epoch("2019-06-15"))


def test_date_to_only():
    f = build_filter(SearchFilters(date_to="2022-03-01"))
    epoch_conds = [c for c in _must_conditions(f) if c.key == "date_epoch"]
    assert len(epoch_conds) == 1
    assert epoch_conds[0].range.lte == float(_iso_to_epoch("2022-03-01"))


# ── full filter ──────────────────────────────────────────────────────────

def test_full_filter_clause_count():
    """All 7 fields set → 7 must conditions (age produces 2, date produces 2,
    case_type/state/sex each produce 1)."""
    f = build_filter(SearchFilters(
        case_type="missing",
        state="TN",
        sex="Male",
        age_low=30,
        age_high=40,
        date_from="2019-01-01",
        date_to="2020-12-31",
    ))
    assert len(f.must) == 7
    assert len(f.must_not) == 0
    assert len(f.should) == 0


def test_full_filter_all_keys_present():
    f = build_filter(SearchFilters(
        case_type="missing",
        state="TN",
        sex="Male",
        age_low=30,
        age_high=40,
        date_from="2019-01-01",
        date_to="2020-12-31",
    ))
    keys = {c.key for c in _must_conditions(f)}
    assert keys == {"case_type", "state", "sex", "age_high", "age_low", "date_epoch"}


# ── _iso_to_epoch ────────────────────────────────────────────────────────

def test_iso_to_epoch_known_date():
    assert _iso_to_epoch("2019-10-14") == 1571011200


def test_iso_to_epoch_y2k():
    assert _iso_to_epoch("2000-01-01") == 946684800


def test_iso_to_epoch_unix_epoch():
    assert _iso_to_epoch("1970-01-01") == 0


def test_iso_to_epoch_leap_day():
    # 2024-02-29 00:00:00 UTC
    assert _iso_to_epoch("2024-02-29") == 1709164800


def test_iso_to_epoch_invalid_format():
    with pytest.raises(ValueError):
        _iso_to_epoch("10-14-2019")


def test_iso_to_epoch_garbage():
    with pytest.raises(ValueError):
        _iso_to_epoch("not-a-date")


# ── single-field isolation ───────────────────────────────────────────────

@pytest.mark.parametrize("field,value,expected_clauses", [
    ("case_type", "missing", 1),
    ("state", "CA", 1),
    ("sex", "Female", 1),
    ("age_low", 20, 1),
    ("age_high", 60, 1),
    ("date_from", "2020-01-01", 1),
    ("date_to", "2023-12-31", 1),
])
def test_single_field_produces_one_clause(field, value, expected_clauses):
    """Each individual filter field should produce exactly one must clause."""
    f = build_filter(SearchFilters(**{field: value}))
    assert f is not None
    assert len(f.must) == expected_clauses
