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

  2. GeminiEmbedder  (optional / legacy)
     Calls the Google AI Studio REST batchEmbedContents endpoint.
     Requires GOOGLE_API_KEY and is subject to free-tier quota limits.
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

# Gemini REST API (legacy / optional)
_GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/{model}:batchEmbedContents"
)
_BATCH_SIZE = 100  # Gemini API limit


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


# ── Gemini Embedder (legacy / optional) ──────────────────────────────────────

class GeminiEmbedder(BaseEmbedder):
    """
    Google Gemini embedder via AI Studio REST API (optional / legacy).

    Batches requests (max 100 texts per call).
    Automatically retries on 429 quota errors using the API-provided delay.

    NOTE: The free tier quota is often exhausted during large ingestion runs.
    Consider using LocalEmbedder instead for unlimited, offline embedding.
    """

    def __init__(self, settings: Settings) -> None:
        import requests as _requests  # noqa: F401 — verify installed
        self._requests = _requests

        raw = settings.embedding_model or "gemini-embedding-2"
        self._model = raw.removeprefix("models/")
        self._api_key = settings.google_api_key
        self._url = _GEMINI_EMBED_URL.format(model=self._model)

        if not self._api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY is required for GeminiEmbedder. "
                "Set it in your .env file or switch to LocalEmbedder."
            )

    # ── public ───────────────────────────────────────────────────────────────

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed texts using the Gemini REST batchEmbedContents API."""
        embeddings: List[List[float]] = []
        total = len(texts)
        for i in range(0, total, _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            logger.info(
                "Embedding batch %d/%d (%d texts) …",
                i // _BATCH_SIZE + 1,
                -(-total // _BATCH_SIZE),
                len(batch),
            )
            embeddings.extend(self._call_batch(batch, task_type="RETRIEVAL_DOCUMENT"))
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        return self._call_batch([query], task_type="RETRIEVAL_QUERY")[0]

    # ── private ──────────────────────────────────────────────────────────────

    def _call_batch(self, texts: List[str], task_type: str) -> List[List[float]]:
        """Call batchEmbedContents with automatic retry on 429 quota errors."""
        model_id = f"models/{self._model}"
        payload = {
            "requests": [
                {
                    "model": model_id,
                    "content": {"parts": [{"text": t}]},
                    "taskType": task_type,
                }
                for t in texts
            ]
        }

        max_retries = 20
        for attempt in range(max_retries):
            try:
                resp = self._requests.post(
                    self._url,
                    json=payload,
                    params={"key": self._api_key},
                    timeout=120,
                )
            except Exception as exc:
                wait_secs = 30
                logger.warning(
                    "Network error (attempt %d/%d): %s. Retrying in %ds …",
                    attempt + 1, max_retries, exc, wait_secs,
                )
                time.sleep(wait_secs)
                continue

            if resp.ok:
                data = resp.json()
                return [item["values"] for item in data["embeddings"]]

            if resp.status_code == 429:
                wait_secs = 65
                try:
                    body = resp.json()
                    for detail in body.get("error", {}).get("details", []):
                        rd = detail.get("retryDelay", "")
                        if rd:
                            wait_secs = int(float(re.sub(r"[^\d.]", "", rd))) + 5
                            break
                except Exception:
                    pass
                logger.warning(
                    "Rate limit hit (attempt %d/%d). Waiting %ds …",
                    attempt + 1, max_retries, wait_secs,
                )
                time.sleep(wait_secs)
                continue

            raise RuntimeError(
                f"Gemini embedContent error {resp.status_code}: {resp.text}"
            )

        raise RuntimeError(
            f"Gemini embedContent failed after {max_retries} retries (rate limit)."
        )
