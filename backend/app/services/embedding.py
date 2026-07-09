"""Semantic embedding service wrapping sentence-transformers.

Provides lazy-loaded multilingual embeddings for the RAG pipeline.
When the model is unavailable (e.g. CI), falls back to zero vectors so
existing tests pass without a GPU or model download.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_EMBEDDING_DIM = 384  # known for MiniLM-L12-v2

_model: object | None = None
_model_unavailable = False


def _load_model() -> object | None:
    global _model, _model_unavailable
    if _model is not None or _model_unavailable:
        return _model
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("Embedding model loaded: %s (dim=%d)", _MODEL_NAME, _EMBEDDING_DIM)
    except Exception:
        logger.warning("Embedding model unavailable, using fallback", exc_info=True)
        _model_unavailable = True
        _model = None
    return _model


def embedding_dim() -> int:
    return _EMBEDDING_DIM


def embed_query(text: str) -> "NDArray[np.float32]":
    """Return a single embedding vector for a query string."""
    model = _load_model()
    if model is None:
        return np.zeros(_EMBEDDING_DIM, dtype=np.float32)
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype(np.float32)


def embed_documents(texts: list[str]) -> "NDArray[np.float32]":
    """Return a (N, dim) array of embeddings for a batch of texts."""
    if not texts:
        return np.zeros((0, _EMBEDDING_DIM), dtype=np.float32)
    model = _load_model()
    if model is None:
        return np.zeros((len(texts), _EMBEDDING_DIM), dtype=np.float32)
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vecs.astype(np.float32).reshape(len(texts), _EMBEDDING_DIM)
