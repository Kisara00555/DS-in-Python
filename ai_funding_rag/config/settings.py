"""
config/settings.py
------------------
Centralised application configuration loaded from environment variables.
Uses dependency injection: every component receives a Settings instance.

Embedding strategy:
  - Default: LocalEmbedder  — sentence-transformers/all-MiniLM-L6-v2
    No API key required. No rate limits. Model is cached locally (~80 MB).
  - Legacy:  GeminiEmbedder — requires GOOGLE_API_KEY, subject to quota.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env once at import time
load_dotenv()


@dataclass
class Settings:
    """Immutable configuration object passed via dependency injection."""

    # ── LLM ─────────────────────────────────────────────────────────────────────
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.0-flash"))
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )

    # ── Embeddings ──────────────────────────────────────────────────────────────
    # Default: all-MiniLM-L6-v2 (local, offline, no API key needed)
    # To use Gemini instead, set EMBEDDING_MODEL=gemini-embedding-2 in .env
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        )
    )

    # ── Chunking ─────────────────────────────────────────────────────────────
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "800"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "150"))
    )

    # ── Vector store ─────────────────────────────────────────────────────────
    vector_store_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
        )
    )
    collection_name: str = field(
        default_factory=lambda: os.getenv(
            "COLLECTION_NAME", "ai_funding_corpus"
        )
    )

    # ── Retrieval ─────────────────────────────────────────────────────────────
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "5")))

    # ── Data paths ───────────────────────────────────────────────────────────
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", "./data/pdfs"))
    )
    eval_dataset_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("EVAL_DATASET_PATH", "./data/evaluation/ground_truth.json")
        )
    )
    eval_results_path: Path = field(
        default_factory=lambda: Path(
            os.getenv("EVAL_RESULTS_PATH", "./data/evaluation/results.json")
        )
    )

    def validate(self) -> None:
        """Raise if critical fields are missing."""
        # GOOGLE_API_KEY is required for the LLM (Gemini) and for GeminiEmbedder.
        # It is NOT required when using LocalEmbedder.
        if not self.google_api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY is not set. "
                "Get a free key at https://aistudio.google.com/app/apikey "
                "and add it to your .env file. "
                "(It is still needed for the LLM — only the embedding is local.)"
            )


# Singleton – import and use directly or override in tests
default_settings = Settings()
