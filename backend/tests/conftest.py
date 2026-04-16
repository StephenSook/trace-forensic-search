"""Shared pytest fixtures.

Makes `backend/` importable under `from config import ...` etc. when
tests run from the repo root via `pytest backend/tests`, and provides a
skip-if-DB-down hook so CI without Actian up stays green.
"""
from __future__ import annotations

import hashlib
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
    from actian_vectorai import VectorAIClient, VectorAIConnectionError, VectorAITimeoutError

    from config import VECTORAI_ADDR

    # Only skip on *connection*-shaped failures. Anything else (import
    # errors, SDK signature drift, TypeError from bad args, auth) should
    # fail loudly so a broken setup can't masquerade as "DB down."
    try:
        client = VectorAIClient(VECTORAI_ADDR)
        client.connect()
        client.health_check()
    except (VectorAIConnectionError, VectorAITimeoutError, ConnectionError, OSError, TimeoutError) as exc:
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
        # hashlib (not `hash(text)`) so seeds are stable across Python
        # processes — otherwise PYTHONHASHSEED randomizes vectors per run
        # and any future similarity assertion flakes.
        seed = int.from_bytes(hashlib.md5(text.encode()).digest()[:8], "little")
        rng = random.Random(seed)
        return [rng.gauss(0.0, 1.0) for _ in range(dim)]

    return Embedders(
        sapbert=lambda t: _vec(t, 768),
        bge=lambda t: _vec(t, 1024),
        clip_image=lambda p: _vec(p, 512),
    )
