"""Unit tests for backend/search.py — pure Python, no DB, no models.

Tests cover formatting helpers, query chunking, field classification,
score clamping, and the integration-light path with a stubbed client.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from search import (
    _chunk_query,
    _clamp01,
    _classify_field,
    _compose_title,
    _cosine,
    _first_sentence,
    _format_age,
    _format_date,
    _split_source,
    run_search,
)


# ── _compose_title ────────────────────────────────────────────────────


class TestComposeTitle:
    def test_unidentified_male(self):
        p = {"case_type": "unidentified", "sex": "Male", "date_iso": "2020-06-02"}
        assert _compose_title(p) == "Unidentified Male (Found 2020)"

    def test_missing_female(self):
        p = {"case_type": "missing", "sex": "Female", "date_iso": "2019-10-14"}
        assert _compose_title(p) == "Missing Female (Reported 2019)"

    def test_missing_default(self):
        p = {"case_type": "missing", "date_iso": "2021-01-01"}
        assert _compose_title(p) == "Missing Person (Reported 2021)"

    def test_empty_date(self):
        p = {"case_type": "unidentified", "sex": "Male", "date_iso": ""}
        assert "Unknown" in _compose_title(p)


# ── _format_age ───────────────────────────────────────────────────────


class TestFormatAge:
    def test_normal(self):
        assert _format_age({"age_low": 30, "age_high": 38}) == "30 - 38 Years"

    def test_equal(self):
        assert _format_age({"age_low": 25, "age_high": 25}) == "25 - 25 Years"

    def test_missing_keys(self):
        assert _format_age({}) == "? - ? Years"


# ── _format_date ──────────────────────────────────────────────────────


class TestFormatDate:
    def test_normal(self):
        assert _format_date("2020-06-02") == "Jun 02, 2020"

    def test_jan(self):
        assert _format_date("2019-01-15") == "Jan 15, 2019"

    def test_dec(self):
        assert _format_date("2023-12-25") == "Dec 25, 2023"

    def test_bad_format_passthrough(self):
        assert _format_date("not-a-date") == "not-a-date"

    def test_empty_string(self):
        assert _format_date("") == ""


# ── _chunk_query ──────────────────────────────────────────────────────


class TestChunkQuery:
    def test_comma_split(self):
        chunks = _chunk_query("eagle tattoo, right forearm, tall person")
        assert chunks == ["eagle tattoo", "right forearm", "tall person"]

    def test_and_split(self):
        chunks = _chunk_query("he was 34 and had a tattoo")
        assert chunks == ["he was 34", "had a tattoo"]

    def test_semicolon_split(self):
        chunks = _chunk_query("tattoo on arm; scar on face")
        assert chunks == ["tattoo on arm", "scar on face"]

    def test_drops_short_chunks(self):
        chunks = _chunk_query("a, bb, ccc, dddd, eeeee")
        assert chunks == ["eeeee"]

    def test_caps_at_six(self):
        q = "alpha, bravo, charlie, delta, echo foxtrot, golf hotel, india juliet, kilo lima"
        assert len(_chunk_query(q)) == 6

    def test_single_phrase(self):
        chunks = _chunk_query("eagle tattoo on right forearm")
        assert chunks == ["eagle tattoo on right forearm"]

    def test_empty_after_filter(self):
        assert _chunk_query("a, bb") == []

    def test_demo_query(self):
        q = (
            "My brother went missing in 2019 in Tennessee. He was 34, "
            "about 6 feet tall, had a distinctive tattoo of an eagle on "
            "his right forearm, and was last seen near a highway."
        )
        chunks = _chunk_query(q)
        assert len(chunks) <= 6
        assert all(len(c) >= 5 for c in chunks)


# ── _split_source ────────────────────────────────────────────────────


class TestSplitSource:
    def test_period_split(self):
        text = "Recovered along I-40. Found near the highway."
        assert _split_source(text) == ["Recovered along I-40", "Found near the highway"]

    def test_comma_split(self):
        text = "Male, mid-30s, avian motif dermagraphic on right arm"
        result = _split_source(text)
        assert "mid-30s" in result
        assert "avian motif dermagraphic on right arm" in result

    def test_semicolon_split(self):
        text = "Denim trousers; leather boots"
        assert _split_source(text) == ["Denim trousers", "leather boots"]

    def test_drops_short_clauses(self):
        text = "Male, 5ft, avian motif on arm"
        result = _split_source(text)
        assert not any(len(c) < 5 for c in result)

    def test_single_clause_no_delimiters(self):
        assert _split_source("avian motif dermagraphic") == ["avian motif dermagraphic"]

    def test_fallback_when_all_clauses_short(self):
        assert _split_source("N/A, none") == ["N/A, none"]

    def test_empty_string(self):
        assert _split_source("") == []

    def test_short_string(self):
        assert _split_source("hi") == []


class TestChunkQueryConjunctions:
    def test_strips_leading_and(self):
        chunks = _chunk_query("he was tall and had a scar")
        assert any("had a scar" in c for c in chunks)
        assert not any(c.startswith("and ") for c in chunks)

    def test_strips_leading_but(self):
        chunks = _chunk_query("tall person, but very thin build")
        assert not any(c.startswith("but ") for c in chunks)


# ── _classify_field ───────────────────────────────────────────────────


class TestClassifyField:
    def test_tattoo_in_physical(self):
        assert _classify_field("eagle tattoo", "", "physical_text") == "DISTINGUISHING_MARKS"

    def test_scar_in_physical(self):
        assert _classify_field("scar on face", "", "physical_text") == "DISTINGUISHING_MARKS"

    def test_forearm_in_physical(self):
        assert _classify_field("right forearm", "", "physical_text") == "MARK_LOCATION"

    def test_age_in_physical(self):
        assert _classify_field("34 years old", "", "physical_text") == "BIOLOGICAL_RELATION / AGE_EST"

    def test_height_in_physical(self):
        assert _classify_field("6 feet tall", "", "physical_text") == "BIOLOGICAL_RELATION / AGE_EST"

    def test_generic_physical(self):
        assert _classify_field("brown hair", "", "physical_text") == "PHYSICAL_DESCRIPTION"

    def test_highway_in_circumstances(self):
        assert _classify_field("near a highway", "", "circumstances") == "RECOVERY_LOCATION"

    def test_interstate_in_circumstances(self):
        assert _classify_field("I-40 corridor", "", "circumstances") == "RECOVERY_LOCATION"

    def test_date_in_circumstances(self):
        assert _classify_field("in 2019", "", "circumstances") == "DISCOVERY_DATE"

    def test_generic_circumstances(self):
        assert _classify_field("went missing", "", "circumstances") == "CIRCUMSTANCES"

    def test_clothing(self):
        assert _classify_field("dark jeans", "", "clothing") == "CLOTHING_EFFECTS"

    def test_source_text_contributes(self):
        assert _classify_field("", "tattoo of an eagle", "physical_text") == "DISTINGUISHING_MARKS"

    def test_unknown_vector(self):
        assert _classify_field("test", "", "something_else") == "SOMETHING_ELSE"


# ── _first_sentence ──────────────────────────────────────────────────


class TestFirstSentence:
    def test_single_sentence(self):
        assert _first_sentence("Hello world.") == "Hello world."

    def test_multi_sentence(self):
        assert _first_sentence("First. Second. Third.") == "First."

    def test_truncation(self):
        long_text = "A" * 100
        result = _first_sentence(long_text, max_len=20)
        assert len(result) == 20
        assert result.endswith("\u2026")

    def test_no_period(self):
        assert _first_sentence("no period here") == "no period here"

    def test_exclamation(self):
        assert _first_sentence("Stop! Don't go.") == "Stop!"


# ── _cosine ───────────────────────────────────────────────────────────


class TestCosine:
    def test_identical(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine(v, v) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert _cosine([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_opposite(self):
        assert _cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector(self):
        assert _cosine([0, 0, 0], [1, 2, 3]) == 0.0


# ── _clamp01 ──────────────────────────────────────────────────────────


class TestClamp01:
    def test_normal(self):
        assert _clamp01(0.5) == 0.5

    def test_over(self):
        assert _clamp01(1.0000001) == 1.0

    def test_under(self):
        assert _clamp01(-0.001) == 0.0

    def test_exact_bounds(self):
        assert _clamp01(0.0) == 0.0
        assert _clamp01(1.0) == 1.0


# ── Integration-light: run_search with stubbed client ─────────────────


def _make_scored_point(id_: str, score: float, payload: dict) -> MagicMock:
    sp = MagicMock(spec=["id", "score", "payload"])
    sp.id = id_
    sp.score = score
    sp.payload = payload
    return sp


_STUB_PAYLOAD = {
    "case_id": "UP-001",
    "case_type": "unidentified",
    "sex": "Male",
    "age_low": 30,
    "age_high": 38,
    "state": "TN",
    "date_iso": "2020-06-02",
    "date_epoch": 1591056000,
    "physical_text": "avian motif dermagraphic right ventral antebrachium",
    "circumstances": "Remains recovered along I-40 corridor near mile marker 234",
    "clothing": "dark denim trousers, black cotton t-shirt",
}


class TestRunSearchIntegration:
    """Stub the VectorAIClient and embedding functions to test wiring."""

    def _mock_client(self, points: list | None = None):
        if points is None:
            points = [_make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)]
        client = MagicMock()
        client.points.search.return_value = points
        return client

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_calls_search_four_times(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        run_search(req, client)

        assert client.points.search.call_count == 4
        using_args = [
            call.kwargs["using"] for call in client.points.search.call_args_list
        ]
        assert set(using_args) == {
            "physical_text",
            "physical_image",
            "circumstances",
            "clothing",
        }

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_filter_passed_to_all_searches(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchFilters, SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(
            query="eagle tattoo",
            filters=SearchFilters(state="TN"),
        )
        run_search(req, client)

        for call in client.points.search.call_args_list:
            assert call.kwargs["filter"] is not None

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_no_filter_passes_none(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        run_search(req, client)

        for call in client.points.search.call_args_list:
            assert call.kwargs["filter"] is None

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_rrf_receives_four_lists(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        client = self._mock_client([])
        mock_rrf.return_value = []

        req = SearchRequest(query="eagle tattoo")
        run_search(req, client)

        responses_arg = mock_rrf.call_args[0][0]
        assert len(responses_arg) == 4

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_result_fields_match_frontend_contract(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        resp = run_search(req, client)

        assert resp.total_matches == 1
        r = resp.results[0]
        assert r.caseId == "UP-001"
        assert r.title == "Unidentified Male (Found 2020)"
        assert r.confidence >= 0.82
        assert r.threshold == "HIGH CONFIDENCE"
        assert r.stateFound == "Tennessee"
        assert r.genderEst == "Male"
        assert r.ageRange == "30 - 38 Years"
        assert r.discoveryDate == "Jun 02, 2020"
        assert r.namusLink is None

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_empty_results(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        client = self._mock_client([])
        mock_rrf.return_value = []

        req = SearchRequest(query="something obscure")
        resp = run_search(req, client)

        assert resp.total_matches == 0
        assert resp.results == []
        assert resp.latency_ms >= 0

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_confidence_clamped(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        """Floating-point cosine can round to >1.0; Pydantic rejects that."""
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 1.0000001, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="test")
        resp = run_search(req, client)

        assert resp.results[0].confidence == 1.0

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_state_name_lookup(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        payload = {**_STUB_PAYLOAD, "state": "CA"}
        point = _make_scored_point("uuid-002", 0.75, payload)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="test")
        resp = run_search(req, client)

        assert resp.results[0].stateFound == "California"

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_unknown_state_falls_back(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        payload = {**_STUB_PAYLOAD, "state": "XX"}
        point = _make_scored_point("uuid-003", 0.5, payload)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="test")
        resp = run_search(req, client)

        assert resp.results[0].stateFound == "XX"

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_serialized_output_is_json_safe(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        """SearchResponse.model_dump() should produce a dict that
        matches the frontend SearchResponse interface exactly."""
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        resp = run_search(req, client)
        d = resp.model_dump()

        assert "query" in d
        assert "total_matches" in d
        assert "latency_ms" in d
        assert "results" in d
        r = d["results"][0]
        assert "caseId" in r
        assert "threshold" in r
        assert "matchMappings" in r
        # No snake_case result keys leaking
        assert "case_id" not in r
        assert "match_mappings" not in r

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_image_vec_used_for_physical_image(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        custom_vec = [0.5] * 512
        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        run_search(req, client, image_vec=custom_vec)

        calls = client.points.search.call_args_list
        image_call = [c for c in calls if c.kwargs["using"] == "physical_image"][0]
        assert image_call.kwargs["vector"] == custom_vec

    @patch("search.embed_text_sapbert", return_value=[0.1] * 768)
    @patch("search.embed_text_bge", return_value=[0.2] * 1024)
    @patch("search.embed_text_bge_batch", return_value=[[0.2] * 1024])
    @patch("search.embed_text_clip", return_value=[0.3] * 512)
    @patch("search.reciprocal_rank_fusion")
    def test_no_image_vec_uses_clip_text(
        self, mock_rrf, mock_clip, mock_bge_batch, mock_bge, mock_sap
    ):
        from schemas import SearchRequest

        point = _make_scored_point("uuid-001", 0.82, _STUB_PAYLOAD)
        client = self._mock_client([point])
        mock_rrf.return_value = [point]

        req = SearchRequest(query="eagle tattoo")
        run_search(req, client)

        calls = client.points.search.call_args_list
        image_call = [c for c in calls if c.kwargs["using"] == "physical_image"][0]
        assert image_call.kwargs["vector"] == [0.3] * 512
