"""
vectorstore/store.py
--------------------
Persistent ChromaDB vector store.
Implements BaseVectorStore ABC for full DI compliance.
Data persists to disk so it survives session restarts.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config.settings import Settings
from ..ingestion.chunker import TextChunk
from .embedder import BaseEmbedder

logger = logging.getLogger(__name__)


# ── Value Objects ──────────────────────────────────────────────────────────

class RetrievedChunk:
    """Holds a retrieved chunk plus its cosine similarity distance."""

    def __init__(self, chunk_id: str, text: str, metadata: Dict[str, Any],
                 distance: float) -> None:
        self.chunk_id = chunk_id
        self.text = text
        self.metadata = metadata
        self.distance = distance          # lower = more similar
        self.similarity = 1.0 - distance  # convenience property

    def __repr__(self) -> str:
        return (f"RetrievedChunk(id={self.chunk_id!r}, "
                f"similarity={self.similarity:.3f})")


# ── Abstract base ──────────────────────────────────────────────────────────

class BaseVectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def add_chunks(self, chunks: List[TextChunk], embedder: BaseEmbedder) -> int:
        """Embed and persist chunks. Returns count of added documents."""

    @abstractmethod
    def search(self, query: str, embedder: BaseEmbedder,
               top_k: int = 5) -> List[RetrievedChunk]:
        """Return top-k semantically similar chunks for query."""

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored chunks."""

    @abstractmethod
    def reset(self) -> None:
        """Delete all documents from the collection."""


# ── Concrete implementation ────────────────────────────────────────────────

class ChromaVectorStore(BaseVectorStore):
    """ 
    Persistent ChromaDB vector store.

    ChromaDB stores embeddings on disk at `settings.vector_store_path`,
    ensuring data is not lost between sessions (the PDF is NOT re-ingested
    on every run — only on first run or when explicitly reset).
    """

    def __init__(self, settings: Settings) -> None:
        persist_dir = str(settings.vector_store_path)
        settings.vector_store_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB ready — collection '%s' has %d documents",
            settings.collection_name,
            self._collection.count(),
        )

    # ── public ───────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: List[TextChunk], embedder: BaseEmbedder) -> int:
        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [c.metadata for c in chunks]

        logger.info("Embedding %d chunks …", len(chunks))
        vectors = embedder.embed_texts(texts)

        # Upsert so re-ingestion is idempotent
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
        )
        logger.info("Stored %d chunks in ChromaDB", len(chunks))
        return len(chunks)

    def search(self, query: str, embedder: BaseEmbedder,
               top_k: int = 5) -> List[RetrievedChunk]:
        query_vec = embedder.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_vec],
            n_results=min(top_k, self._collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[RetrievedChunk] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0],
        ):
            retrieved.append(
                RetrievedChunk(
                    chunk_id=meta.get("chunk_id", "unknown"),
                    text=doc,
                    metadata=meta,
                    distance=dist,
                )
            )
        return retrieved

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        # Delete the collection entirely and recreate it (safer than filtered delete)
        collection_name = self._collection.name
        self._client.delete_collection(collection_name)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("Vector store collection '%s' cleared and recreated.", collection_name)

# Data is persisted to the local directory defined in settings to ensure the corpus is maintained between runs.
