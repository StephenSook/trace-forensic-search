"""Shared pytest fixtures.

Makes `backend/` importable under `from config import ...` etc. when
tests run from the repo root via `pytest backend/tests`, and provides a
skip-if-DB-down hook so CI without Actian up stays green.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

# Put backend/ on sys.path so `from config import ...` works from tests.
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


@pytest.fixture(scope="session")
def actian_client():
    """Yield a connected VectorAIClient, or skip the session if DB is down."""
    from actian_vectorai import VectorAIClient

    from config import VECTORAI_ADDR

    try:
        client = VectorAIClient(VECTORAI_ADDR)
        client.connect()
        client.health_check()
    except Exception as exc:
        pytest.skip(f"Actian VectorAI DB not reachable at {VECTORAI_ADDR}: {exc}")

    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def fake_embedders():
    """Deterministic fake `Embedders` with correct dims for every vector space.

    Uses a per-text seeded RNG so each distinct text produces distinct
    vectors — enough diversity for cosine distance to be defined but
    zero external dependencies.
    """
    from ingest import Embedders

    def _vec(text: str, dim: int) -> list[float]:
        rng = random.Random(hash(text) & 0xFFFFFFFF)
        return [rng.gauss(0.0, 1.0) for _ in range(dim)]

    return Embedders(
        sapbert=lambda t: _vec(t, 768),
        bge=lambda t: _vec(t, 1024),
        clip_image=lambda p: _vec(p, 512),
    )
