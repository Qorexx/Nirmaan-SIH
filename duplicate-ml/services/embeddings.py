"""
Text embedding and semantic similarity using Sentence Transformers.

Model: paraphrase-multilingual-MiniLM-L12-v2
  - Multilingual, compact (118M params), strong for short paragraphs
  - Downloads once to HuggingFace cache (~480 MB)

All similarity values are genuine cosine similarities computed from
real embeddings — no hardcoded scores.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Module-level singleton — loaded once at startup via lifespan
_model = None


def load_model() -> None:
    """Load the Sentence Transformer model into memory (called once at startup)."""
    global _model
    if _model is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading Sentence Transformer model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Sentence Transformer model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Sentence Transformer model: {e}")
        raise


def get_model():
    if _model is None:
        load_model()
    return _model


def build_text(title: str, description: Optional[str]) -> str:
    """Concatenate title and description into a single embedding input."""
    parts = [title.strip()]
    if description and description.strip():
        parts.append(description.strip())
    return " ".join(parts)


def embed(text: str) -> np.ndarray:
    """Return a normalised L2 unit-vector embedding for one text string."""
    model = get_model()
    emb = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return emb.astype(np.float32)


def embed_batch(texts: list[str]) -> np.ndarray:
    """Return a 2-D float32 matrix of normalised embeddings (N × D)."""
    model = get_model()
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return embs.astype(np.float32)


def cosine_similarity(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    """
    Cosine similarity between two L2-normalised vectors.
    Because both are unit vectors: similarity = dot product.
    Returns a float in [-1, 1], clipped to [0, 1] for practical use.
    """
    sim = float(np.dot(emb_a, emb_b))
    return max(0.0, min(1.0, sim))
