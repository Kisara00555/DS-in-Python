"""
vectorstore/embedder.py
-----------------------
Wraps the embedding backend behind an ABC so the embedding model
can be swapped without touching retrieval logic.

Two implementations are provided:

   1. LocalEmbedder  (DEFAULT)
      Uses sentence-transformers running entirely on the local CPU/GPU.
      Model: all-MiniLM-L6-v2  — 384-dim, fast, high-quality for RAG.
      No API key needed. No rate limits. No quota.
"""

from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from typing import List

from ..config.settings import Settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Default local model — lightweight, high-quality, runs on CPU
_LOCAL_MODEL_DEFAULT = "all-MiniLM-L6-v2" 

# ── Abstract interface ────────────────────────────────────────────────────────

class BaseEmbedder(ABC):
    """Abstract embedder interface — all embedders must implement this."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Return list of embedding vectors, one per text."""

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Return a single embedding vector for a query string."""


# ── Local Embedder (DEFAULT) ──────────────────────────────────────────────────

class LocalEmbedder(BaseEmbedder):
    """
    Local CPU/GPU embedder using sentence-transformers.

    Uses 'all-MiniLM-L6-v2' by default:
      - 384-dimensional vectors
      - ~80 MB model size
      - Excellent retrieval quality (designed for semantic search)
      - Runs fully offline — zero API calls, zero rate limits

    The model is downloaded once on first use and cached locally by
    sentence-transformers in ~/.cache/huggingface/hub/.
    """

    def __init__(self, settings: Settings) -> None:
        model_name = settings.embedding_model or _LOCAL_MODEL_DEFAULT
        logger.info("Loading local embedding model: %s …", model_name)
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(model_name)
        try:
            dim = self._model.get_embedding_dimension()
        except AttributeError:
            dim = self._model.get_sentence_embedding_dimension() 
        logger.info(
            "Local embedder ready — model '%s', dim=%d",
            model_name,
            dim,
        )

    # ── public ───────────────────────────────────────────────────────────────

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed documents. All texts are embedded in one local call."""
        logger.info("Embedding %d texts locally …", len(texts))
        vectors = self._model.encode(
            texts,
            show_progress_bar=len(texts) > 50, 
            convert_to_numpy=True,
            batch_size=64,
        )
        return [v.tolist() for v in vectors]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        vector = self._model.encode(query, convert_to_numpy=True)
        return vector.tolist()


