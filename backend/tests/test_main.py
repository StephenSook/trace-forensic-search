"""Unit tests for backend/main.py — no DB, no models, no lifespan.

TestClient is created *without* entering a `with` block so the lifespan
never fires. Tests monkeypatch `main._client` directly to a stub.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def _reset_client():
    """Ensure _client is None before and after each test."""
    main._client = None
    yield
    main._client = None


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


def _stub_client(*, exists=True, count=60):
    c = MagicMock()
    c.collections.exists.return_value = exists
    c.points.count.return_value = count
    return c


def _stub_point(payload: dict | None):
    p = MagicMock()
    p.payload = payload
    return p


_VALID_PAYLOAD = {
    "case_id": "UP-001",
    "case_type": "unidentified",
    "sex": "Male",
    "age_low": 30,
    "age_high": 38,
    "state": "TN",
    "date_iso": "2020-06-02",
    "date_epoch": 1591056000,
    "physical_text": "avian motif dermagraphic",
    "circumstances": "Remains recovered along I-40 corridor",
    "clothing": "dark denim trousers",
}


# ── /health ──────────────────────────────────────────────────────────


class TestHealth:
    def test_degraded_when_no_client(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["vectorai_reachable"] is False

    def test_ok_when_client_connected(self, client):
        main._client = _stub_client()
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "ok"
        assert body["vectorai_reachable"] is True
        assert body["collection_exists"] is True
        assert body["point_count"] == 60

    def test_degraded_when_collection_missing(self, client):
        main._client = _stub_client(exists=False)
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["vectorai_reachable"] is True
        assert body["collection_exists"] is False
        assert body["point_count"] is None

    def test_degraded_when_client_raises(self, client):
        stub = _stub_client()
        stub.collections.exists.side_effect = ConnectionError("gRPC down")
        main._client = stub
        resp = client.get("/health")
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["vectorai_reachable"] is False


# ── /search ──────────────────────────────────────────────────────────


class TestSearch:
    def test_503_when_no_client(self, client):
        resp = client.post("/search", json={"query": "eagle tattoo"})
        assert resp.status_code == 503
        assert "not available" in resp.json()["detail"]

    def test_422_on_empty_query(self, client):
        main._client = _stub_client()
        resp = client.post("/search", json={"query": ""})
        assert resp.status_code == 422

    @patch("main.run_search")
    def test_delegates_to_run_search(self, mock_run, client):
        from schemas import SearchResponse

        mock_run.return_value = SearchResponse(
            query="eagle tattoo", total_matches=0, latency_ms=5, results=[]
        )
        main._client = _stub_client()
        resp = client.post("/search", json={"query": "eagle tattoo"})
        assert resp.status_code == 200
        assert mock_run.call_count == 1
        body = resp.json()
        assert body["query"] == "eagle tattoo"
        assert body["total_matches"] == 0


# ── /case/{case_id} ──────────────────────────────────────────────────


class TestGetCase:
    def test_503_when_no_client(self, client):
        resp = client.get("/case/MP-001")
        assert resp.status_code == 503

    def test_404_when_scroll_empty(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = ([], None)
        main._client = stub
        resp = client.get("/case/MP-001")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_404_on_empty_payload(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = ([_stub_point(None)], None)
        main._client = stub
        resp = client.get("/case/UP-001")
        assert resp.status_code == 404
        assert "no payload" in resp.json()["detail"]

    def test_404_on_empty_dict_payload(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = ([_stub_point({})], None)
        main._client = stub
        resp = client.get("/case/UP-001")
        assert resp.status_code == 404
        assert "no payload" in resp.json()["detail"]

    def test_500_on_bad_payload(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = ([_stub_point({"case_id": "X"})], None)
        main._client = stub
        resp = client.get("/case/X")
        assert resp.status_code == 500
        assert "validation" in resp.json()["detail"].lower()

    def test_success(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = ([_stub_point(_VALID_PAYLOAD)], None)
        main._client = stub
        resp = client.get("/case/UP-001")
        assert resp.status_code == 200
        case = resp.json()["case"]
        assert case["case_id"] == "UP-001"
        assert case["state"] == "TN"

    def test_scroll_plain_list_fallback(self, client):
        stub = _stub_client()
        stub.points.scroll.return_value = [_stub_point(_VALID_PAYLOAD)]
        main._client = stub
        resp = client.get("/case/UP-001")
        assert resp.status_code == 200


# ── CORS ─────────────────────────────────────────────────────────────


class TestCORS:
    def test_preflight_from_frontend_origin(self, client):
        resp = client.options(
            "/search",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"

    def test_disallowed_origin_blocked(self, client):
        resp = client.options(
            "/search",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in resp.headers
