"""Tests for config.py: constants, vector specs, environment handling.

Pure-Python tests — no DB needed.
"""
from __future__ import annotations


def test_collection_name():
    from config import COLLECTION_NAME

    assert COLLECTION_NAME == "cases"


def test_four_named_vectors():
    from config import VECTORS

    assert set(VECTORS.keys()) == {
        "physical_text",
        "physical_image",
        "circumstances",
        "clothing",
    }


def test_vector_dimensions():
    from config import VECTORS

    assert VECTORS["physical_text"].dim == 768
    assert VECTORS["physical_image"].dim == 512
    assert VECTORS["circumstances"].dim == 1024
    assert VECTORS["clothing"].dim == 1024


def test_model_ids_match_vector_specs():
    from config import (
        BGE_M3_MODEL_ID,
        CLIP_MODEL_ID,
        SAPBERT_MODEL_ID,
        VECTORS,
    )

    assert SAPBERT_MODEL_ID == VECTORS["physical_text"].model_id
    assert CLIP_MODEL_ID == VECTORS["physical_image"].model_id
    assert BGE_M3_MODEL_ID == VECTORS["circumstances"].model_id
    assert BGE_M3_MODEL_ID == VECTORS["clothing"].model_id


def test_sapbert_model_id():
    from config import SAPBERT_MODEL_ID

    assert SAPBERT_MODEL_ID == "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"


def test_clip_model_id():
    from config import CLIP_MODEL_ID

    assert CLIP_MODEL_ID == "openai/clip-vit-base-patch32"


def test_bge_m3_model_id():
    from config import BGE_M3_MODEL_ID

    assert BGE_M3_MODEL_ID == "BAAI/bge-m3"


def test_rrk_k_value():
    from config import RRF_K

    assert RRF_K == 60


def test_vectorai_addr_default():
    from config import VECTORAI_ADDR

    assert "50051" in VECTORAI_ADDR


def test_synthetic_cases_path_exists():
    from pathlib import Path

    from config import SYNTHETIC_CASES_PATH

    assert Path(SYNTHETIC_CASES_PATH).exists()


def test_frontend_origin_default():
    from config import FRONTEND_ORIGIN

    assert "8080" in FRONTEND_ORIGIN


def test_vector_spec_is_frozen():
    from config import VECTORS

    import pytest

    with pytest.raises(AttributeError):
        VECTORS["physical_text"].dim = 999
