"""Tests for Pydantic schemas: validators, computed fields, edge cases.

Pure-Python tests — no DB, no embeddings, no network.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# ── CasePayload ─────────────────────────────────────────────────────

class TestCasePayload:
    def _make(self, **overrides):
        from schemas import CasePayload

        defaults = dict(
            case_id="MP-001",
            case_type="missing",
            sex="Male",
            age_low=30,
            age_high=40,
            state="TN",
            date_epoch=1571011200,
            date_iso="2019-10-14",
            physical_text="eagle tattoo",
            circumstances="last seen near highway",
            clothing="dark jeans",
            image_url=None,
        )
        return CasePayload.model_validate({**defaults, **overrides})

    def test_valid_case(self):
        c = self._make()
        assert c.case_id == "MP-001"
        assert c.case_type == "missing"

    def test_age_order_violation(self):
        with pytest.raises(ValidationError, match="age_low.*must be ≤ age_high"):
            self._make(age_low=50, age_high=30)

    def test_age_equal_is_valid(self):
        c = self._make(age_low=35, age_high=35)
        assert c.age_low == c.age_high == 35

    def test_age_boundary_zero(self):
        c = self._make(age_low=0, age_high=0)
        assert c.age_low == 0

    def test_age_boundary_120(self):
        c = self._make(age_low=100, age_high=120)
        assert c.age_high == 120

    def test_age_exceeds_120(self):
        with pytest.raises(ValidationError):
            self._make(age_high=121)

    def test_negative_age(self):
        with pytest.raises(ValidationError):
            self._make(age_low=-1)

    def test_state_must_be_two_uppercase_letters(self):
        with pytest.raises(ValidationError):
            self._make(state="Tennessee")

    def test_state_lowercase_rejected(self):
        with pytest.raises(ValidationError):
            self._make(state="tn")

    def test_date_iso_format_enforced(self):
        with pytest.raises(ValidationError):
            self._make(date_iso="10/14/2019")

    def test_case_type_literal(self):
        with pytest.raises(ValidationError):
            self._make(case_type="unknown")

    def test_sex_literal(self):
        with pytest.raises(ValidationError):
            self._make(sex="Unknown")

    def test_image_url_optional(self):
        c = self._make(image_url=None)
        assert c.image_url is None

    def test_image_url_present(self):
        c = self._make(image_url="https://example.com/photo.jpg")
        assert c.image_url == "https://example.com/photo.jpg"

    def test_model_dump_roundtrip(self):
        from schemas import CasePayload

        c = self._make()
        d = c.model_dump()
        c2 = CasePayload.model_validate(d)
        assert c == c2


# ── SearchFilters ────────────────────────────────────────────────────

class TestSearchFilters:
    def _make(self, **overrides):
        from schemas import SearchFilters

        return SearchFilters.model_validate(overrides)

    def test_all_none_is_valid(self):
        f = self._make()
        assert f.sex is None
        assert f.state is None

    def test_sex_allows_unknown(self):
        f = self._make(sex="Unknown")
        assert f.sex == "Unknown"

    def test_age_range_violation(self):
        with pytest.raises(ValidationError, match="age_low.*must be ≤ age_high"):
            self._make(age_low=50, age_high=30)

    def test_date_range_violation(self):
        with pytest.raises(ValidationError, match="date_from.*must be ≤ date_to"):
            self._make(date_from="2020-12-31", date_to="2020-01-01")

    def test_partial_age_no_cross_validation(self):
        f = self._make(age_low=50)
        assert f.age_low == 50
        assert f.age_high is None

    def test_partial_date_no_cross_validation(self):
        f = self._make(date_from="2020-01-01")
        assert f.date_from == "2020-01-01"
        assert f.date_to is None

    def test_state_pattern(self):
        with pytest.raises(ValidationError):
            self._make(state="California")

    def test_date_format(self):
        with pytest.raises(ValidationError):
            self._make(date_from="2020/01/01")


# ── SearchRequest ────────────────────────────────────────────────────

class TestSearchRequest:
    def test_min_query(self):
        from schemas import SearchRequest

        r = SearchRequest(query="x")
        assert r.query == "x"
        assert r.limit == 10
        assert r.filters is None

    def test_empty_query_rejected(self):
        from schemas import SearchRequest

        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_limit_bounds(self):
        from schemas import SearchRequest

        with pytest.raises(ValidationError):
            SearchRequest(query="x", limit=0)
        with pytest.raises(ValidationError):
            SearchRequest(query="x", limit=51)

    def test_limit_boundary_values(self):
        from schemas import SearchRequest

        r1 = SearchRequest(query="x", limit=1)
        assert r1.limit == 1
        r50 = SearchRequest(query="x", limit=50)
        assert r50.limit == 50

    def test_query_max_length(self):
        from schemas import SearchRequest

        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 2001)

    def test_query_at_max_length(self):
        from schemas import SearchRequest

        r = SearchRequest(query="x" * 2000)
        assert len(r.query) == 2000


# ── SearchResult + threshold computed field ──────────────────────────

class TestSearchResult:
    def _make(self, confidence: float):
        from schemas import SearchResult

        return SearchResult(
            caseId="MP-001",
            title="Test",
            confidence=confidence,
            stateFound="TN",
            genderEst="Male",
            ageRange="30-40",
            discoveryDate="2019-10-14",
            matchMappings=[],
        )

    def test_high_confidence_threshold(self):
        r = self._make(0.70)
        assert r.threshold == "HIGH CONFIDENCE"

    def test_high_confidence_above(self):
        r = self._make(0.99)
        assert r.threshold == "HIGH CONFIDENCE"

    def test_medium_confidence_threshold(self):
        r = self._make(0.45)
        assert r.threshold == "MEDIUM CONFIDENCE"

    def test_medium_confidence_mid(self):
        r = self._make(0.55)
        assert r.threshold == "MEDIUM CONFIDENCE"

    def test_low_confidence_below_45(self):
        r = self._make(0.44)
        assert r.threshold == "LOW CONFIDENCE"

    def test_low_confidence_zero(self):
        r = self._make(0.0)
        assert r.threshold == "LOW CONFIDENCE"

    def test_boundary_069_is_medium(self):
        r = self._make(0.69)
        assert r.threshold == "MEDIUM CONFIDENCE"

    def test_threshold_in_serialized_output(self):
        r = self._make(0.90)
        d = r.model_dump()
        assert d["threshold"] == "HIGH CONFIDENCE"

    def test_confidence_out_of_range(self):
        from schemas import SearchResult

        with pytest.raises(ValidationError):
            SearchResult(
                caseId="X",
                title="X",
                confidence=1.5,
                stateFound="TN",
                genderEst="Male",
                ageRange="30-40",
                discoveryDate="2019-10-14",
            )

    def test_namus_link_optional(self):
        r = self._make(0.9)
        assert r.namusLink is None

    def test_namus_link_present(self):
        from schemas import SearchResult

        r = SearchResult(
            caseId="UP-001",
            title="Test",
            confidence=0.9,
            stateFound="TN",
            genderEst="Male",
            ageRange="30-40",
            discoveryDate="2019-10-14",
            namusLink="https://namus.nij.ojp.gov/case/UP10294",
        )
        assert r.namusLink == "https://namus.nij.ojp.gov/case/UP10294"


# ── MatchMapping ─────────────────────────────────────────────────────

class TestMatchMapping:
    def test_valid_mapping(self):
        from schemas import MatchMapping

        m = MatchMapping(
            queryTerm='"eagle tattoo"',
            forensicField="DISTINGUISHING_MARKS",
            forensicValue="avian motif dermagraphic",
            similarity=0.93,
        )
        assert m.similarity == 0.93

    def test_similarity_bounds(self):
        from schemas import MatchMapping

        with pytest.raises(ValidationError):
            MatchMapping(
                queryTerm="x",
                forensicField="x",
                forensicValue="x",
                similarity=1.1,
            )
        with pytest.raises(ValidationError):
            MatchMapping(
                queryTerm="x",
                forensicField="x",
                forensicValue="x",
                similarity=-0.1,
            )


# ── Response envelopes ──────────────────────────────────────────────

class TestSearchResponse:
    def test_empty_results(self):
        from schemas import SearchResponse

        r = SearchResponse(query="test", total_matches=0, latency_ms=42, results=[])
        assert r.total_matches == 0
        assert r.results == []

    def test_with_results(self):
        from schemas import MatchMapping, SearchResponse, SearchResult

        result = SearchResult(
            caseId="MP-001",
            title="Test",
            confidence=0.9,
            stateFound="TN",
            genderEst="Male",
            ageRange="30-40",
            discoveryDate="2019-10-14",
            matchMappings=[
                MatchMapping(
                    queryTerm='"eagle"',
                    forensicField="MARKS",
                    forensicValue="avian tattoo",
                    similarity=0.95,
                )
            ],
        )
        r = SearchResponse(
            query="eagle tattoo",
            total_matches=1,
            latency_ms=150,
            results=[result],
        )
        assert len(r.results) == 1
        assert r.results[0].threshold == "HIGH CONFIDENCE"


class TestIngestResponse:
    def test_basic(self):
        from schemas import IngestResponse

        r = IngestResponse(collection="cases", ingested=60, took_ms=5000)
        assert r.collection == "cases"
        assert r.ingested == 60


class TestHealthResponse:
    def test_defaults(self):
        from schemas import HealthResponse

        h = HealthResponse(vectorai_reachable=True, collection_exists=True, point_count=60)
        assert h.status == "ok"

    def test_degraded(self):
        from schemas import HealthResponse

        h = HealthResponse(
            status="degraded",
            vectorai_reachable=False,
            collection_exists=False,
        )
        assert h.status == "degraded"
        assert h.point_count is None
