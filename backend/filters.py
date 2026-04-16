"""Hard metadata pre-filter for Actian VectorAI DB searches.

Converts a ``SearchFilters`` request into an Actian ``Filter`` that is
passed to every named-vector fan-out search call, narrowing candidates
*before* vector similarity is computed.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone

from actian_vectorai import Field, FilterBuilder

from schemas import SearchFilters


def _iso_to_epoch(date_str: str) -> int:
    """Convert an ISO date string (``'2019-10-14'``) to a UTC unix epoch."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(calendar.timegm(dt.timetuple()))


def build_filter(filters: SearchFilters | None) -> object | None:
    """Build an Actian Filter from *filters*. Returns ``None`` when empty."""
    if filters is None:
        return None

    fb = FilterBuilder()
    has_clause = False

    if filters.case_type is not None:
        fb.must(Field("case_type").eq(filters.case_type))
        has_clause = True

    if filters.state is not None:
        fb.must(Field("state").eq(filters.state.upper()))
        has_clause = True

    if filters.sex is not None:
        fb.must(Field("sex").any_of([filters.sex, "Unknown"]))
        has_clause = True

    if filters.age_low is not None:
        fb.must(Field("age_high").gte(filters.age_low))
        has_clause = True

    if filters.age_high is not None:
        fb.must(Field("age_low").lte(filters.age_high))
        has_clause = True

    if filters.date_from is not None:
        fb.must(Field("date_epoch").gte(_iso_to_epoch(filters.date_from)))
        has_clause = True

    if filters.date_to is not None:
        # End of day: add 86399s (23:59:59) so "2020-06-02" includes the full day
        fb.must(Field("date_epoch").lte(_iso_to_epoch(filters.date_to) + 86399))
        has_clause = True

    if not has_clause:
        return None

    return fb.build()
