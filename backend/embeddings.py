"""Embedding wrappers for Trace: SapBERT (768d), BGE-M3 (1024d), CLIP (512d).

Models load lazily on first call. All outputs are L2-normalized (PLAN.md D7).
"""
from __future__ import annotations

import functools
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
import torch
from PIL import Image

from config import BGE_M3_MODEL_ID, CLIP_MODEL_ID, SAPBERT_MODEL_ID

# ── Device ───────────────────────────────────────────────────────────

DEVICE = (
    "cuda" if torch.cuda.is_available()
    else "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    else "cpu"
)


# ── Internals ────────────────────────────────────────────────────────

def _l2(v: np.ndarray) -> list[float]:
    norm = np.linalg.norm(v)
    return (v / norm if norm > 0 else v).tolist()


def _fetch_image(source: str) -> Image.Image:
    if source.startswith(("http://", "https://")):
        r = requests.get(source, timeout=30)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    return Image.open(Path(source)).convert("RGB")


# ── SapBERT (768d) ──────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _sapbert():
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(SAPBERT_MODEL_ID)
    mdl = AutoModel.from_pretrained(SAPBERT_MODEL_ID).to(DEVICE).eval()
    return tok, mdl


def embed_text_sapbert(text: str) -> list[float]:
    """Medical/anatomical text → 768-dim vector (CLS pooling, L2-norm)."""
    tok, mdl = _sapbert()
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        cls = mdl(**inputs).last_hidden_state[:, 0, :].squeeze(0).cpu().numpy()
    return _l2(cls)


# ── BGE-M3 (1024d) ──────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _bge():
    from FlagEmbedding import BGEM3FlagModel
    return BGEM3FlagModel(BGE_M3_MODEL_ID, use_fp16=(DEVICE != "cpu"))


def embed_text_bge(text: str) -> list[float]:
    """Narrative text → 1024-dim dense vector (model-normalized)."""
    out = _bge().encode([text], return_dense=True, return_sparse=False, return_colbert_vecs=False)
    v = out["dense_vecs"][0]
    return v.tolist() if isinstance(v, np.ndarray) else list(v)


def embed_text_bge_batch(texts: list[str]) -> list[list[float]]:
    """Batch encode → list of 1024-dim dense vectors."""
    if not texts:
        return []
    out = _bge().encode(texts, return_dense=True, return_sparse=False, return_colbert_vecs=False)
    return [v.tolist() if isinstance(v, np.ndarray) else list(v) for v in out["dense_vecs"]]


# ── CLIP (512d) ──────────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _clip():
    from transformers import CLIPModel, CLIPProcessor
    proc = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
    mdl = CLIPModel.from_pretrained(CLIP_MODEL_ID).to(DEVICE).eval()
    return proc, mdl


def embed_text_clip(text: str) -> list[float]:
    """Text → 512-dim CLIP vector (cross-modal text→image search)."""
    proc, mdl = _clip()
    inputs = proc(text=[text], return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        vec = mdl.get_text_features(**inputs).squeeze(0).cpu().numpy()
    return _l2(vec)


def embed_image_clip(source: str) -> list[float]:
    """Image (local path or URL) → 512-dim CLIP vector."""
    proc, mdl = _clip()
    img = _fetch_image(source)
    inputs = proc(images=img, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        vec = mdl.get_image_features(**inputs).squeeze(0).cpu().numpy()
    return _l2(vec)
