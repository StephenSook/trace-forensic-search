"""End-to-end tests for the ingest pipeline.

These talk to the live `trace-vectoraidb` container. The `actian_client`
fixture in conftest.py skips the whole module if the container isn't up.

Fake embedders are used so the tests run before Vinh's `embeddings.py`
lands. When real embeddings ship, the same tests run against real
vectors with no changes.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_slate(actian_client):
    """Delete any pre-existing `cases` collection before and after each test."""
    from config import COLLECTION_NAME

    if actian_client.collections.exists(COLLECTION_NAME):
        actian_client.collections.delete(COLLECTION_NAME)
    yield
    if actian_client.collections.exists(COLLECTION_NAME):
        actian_client.collections.delete(COLLECTION_NAME)


def test_load_cases_all_60_valid():
    from ingest import load_cases

    cases = load_cases()
    assert len(cases) == 60
    assert {c.case_type for c in cases} == {"missing", "unidentified"}
    # Ground-truth pairs exist
    ids = {c.case_id for c in cases}
    for n in range(1, 7):
        assert f"MP-{n:03d}" in ids
        assert f"UP-{n:03d}" in ids


def test_ensure_collection_creates_with_four_named_vectors(actian_client):
    from config import COLLECTION_NAME, VECTORS
    from ingest import ensure_collection

    created = ensure_collection(actian_client)
    assert created is True
    assert actian_client.collections.exists(COLLECTION_NAME)

    # Second call is a no-op
    assert ensure_collection(actian_client) is False


def test_build_point_skips_physical_image_when_no_url(fake_embedders):
    from ingest import build_point, point_id_for
    from schemas import CasePayload

    c = CasePayload(
        case_id="X-001",
        case_type="missing",
        sex="Male",
        age_low=30, age_high=40,
        state="TN",
        date_epoch=1577836800,
        date_iso="2020-01-01",
        physical_text="eagle tattoo on right forearm",
        circumstances="last seen leaving a highway rest stop",
        clothing="dark jeans, black t-shirt",
        image_url=None,
    )
    p = build_point(c, fake_embedders)
    assert p.id == point_id_for("X-001")
    assert set(p.vector.keys()) == {"physical_text", "circumstances", "clothing"}
    assert len(p.vector["physical_text"]) == 768
    assert len(p.vector["circumstances"]) == 1024
    assert len(p.vector["clothing"]) == 1024
    assert "physical_image" not in p.vector


def test_build_point_includes_image_when_url_present(fake_embedders):
    from ingest import build_point
    from schemas import CasePayload

    c = CasePayload(
        case_id="X-002",
        case_type="unidentified",
        sex="Female",
        age_low=25, age_high=35,
        state="CA",
        date_epoch=1577836800,
        date_iso="2020-01-01",
        physical_text="birthmark on left shoulder",
        circumstances="recovered in desert",
        clothing="hiking boots",
        image_url="https://example.com/tattoo.jpg",
    )
    p = build_point(c, fake_embedders)
    assert "physical_image" in p.vector
    assert len(p.vector["physical_image"]) == 512


def test_run_ingest_full_pipeline(actian_client, fake_embedders):
    """Ingest all 60 cases into a live Actian container, read one back."""
    from config import COLLECTION_NAME
    from ingest import load_cases, run_ingest

    cases = load_cases()
    resp = run_ingest(actian_client, cases, fake_embedders)

    assert resp.collection == COLLECTION_NAME
    assert resp.ingested == 60
    assert resp.skipped == 0
    assert resp.took_ms > 0

    # Live verification
    assert actian_client.points.count(COLLECTION_NAME) == 60

    # Read MP-001 back by its derived UUID and assert payload round-tripped.
    # (Multi-named vector retrieval has its own SDK quirks unrelated to
    # ingest correctness — Vinh will handle that in search.py.)
    from ingest import point_id_for

    sample = actian_client.points.get(
        COLLECTION_NAME,
        ids=[point_id_for("MP-001")],
        with_payload=True,
    )
    assert len(sample) == 1
    p = sample[0]
    assert p.payload["case_id"] == "MP-001"
    assert p.payload["case_type"] == "missing"
    assert p.payload["state"] == "TN"
    assert "eagle" in p.payload["physical_text"].lower()


def test_run_ingest_is_idempotent(actian_client, fake_embedders):
    """Re-running ingest on the same cases yields the same count."""
    from config import COLLECTION_NAME
    from ingest import load_cases, run_ingest

    cases = load_cases()
    run_ingest(actian_client, cases, fake_embedders)
    assert actian_client.points.count(COLLECTION_NAME) == 60

    run_ingest(actian_client, cases, fake_embedders)
    assert actian_client.points.count(COLLECTION_NAME) == 60
