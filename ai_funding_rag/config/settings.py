"""
config/settings.py
------------------
Centralised application configuration loaded from environment variables.
Uses dependency injection: every component receives a Settings instance.

Embedding strategy:
  - Default: LocalEmbedder (sentence-transformers) — no API key needed, offline.
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
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.1-8b-instant"))
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )

    # ── Embeddings ──────────────────────────────────────────────────────────────
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
        # GROQ_API_KEY is required for the LLM.
        if not self.groq_api_key: 
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com/keys "
                "and add it to your .env file."
            )


# Singleton – import and use directly or override in tests
default_settings = Settings()
