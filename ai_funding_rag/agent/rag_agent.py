"""
agent/rag_agent.py
------------------
The central Agentic Loop: orchestrates Retrieval → Generation → Traceability.

The loop:
  1. User sends a question
  2. Retriever expands and searches vector store
  3. Retrieved chunks are printed (traceability)
  4. Generator produces a grounded answer
  5. Result is returned with full trace

This class is the single entry-point for the RAG pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..ingestion.chunker import BaseChunker, SlidingWindowChunker
from ..ingestion.pdf_loader import BaseLoader, PyMuPDFLoader
from ..vectorstore.embedder import BaseEmbedder, LocalEmbedder
from ..vectorstore.store import BaseVectorStore, ChromaVectorStore
from .generator import GenerationResult, Generator
from .retriever import RetrievalTrace, Retriever

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    Top-level orchestrator implementing the Agentic Loop.

    All dependencies are injected via constructor, making the class
    fully testable and extensible (e.g., swap ChromaDB for Pinecone).
    """

    def __init__(
        self,
        settings: Settings,
        loader: Optional[BaseLoader] = None,
        chunker: Optional[BaseChunker] = None,
        embedder: Optional[BaseEmbedder] = None,
        vector_store: Optional[BaseVectorStore] = None,
        use_query_expansion: bool = True,
    ) -> None:
        """
        Initialise the RAGAgent with all pipeline components.

        Args:
            settings:            Configuration object (API keys, paths, model names).
            loader:              PDF loader; defaults to PyMuPDFLoader.
            chunker:             Text chunker; defaults to SlidingWindowChunker.
            embedder:            Embedding model; defaults to LocalEmbedder.
            vector_store:        Vector DB; defaults to ChromaVectorStore.
            use_query_expansion: If True, the Retriever expands the query using LLM.
        """
        self._settings = settings

        # Dependency injection with sensible defaults
        self._loader: BaseLoader = loader or PyMuPDFLoader()
        self._chunker: BaseChunker = chunker or SlidingWindowChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._embedder: BaseEmbedder = embedder or LocalEmbedder(settings)
        self._vector_store: BaseVectorStore = vector_store or ChromaVectorStore(settings)

        self._retriever = Retriever(
            settings=settings,
            embedder=self._embedder,
            vector_store=self._vector_store,
            use_query_expansion=use_query_expansion,
        )
        self._generator = Generator(settings=settings)

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, source: Path, force: bool = False) -> int:
        """
        Ingest PDFs from a file or directory into the vector store.

        Args:
            source: Path to a PDF file or directory of PDFs.
            force:  If True, re-ingests even if documents already exist.

        Returns:
            Number of chunks stored.
        """
        if not force and self._vector_store.count() > 0:
            logger.info(
                "Vector store already contains %d chunks. "
                "Skipping ingestion. Use force=True to re-ingest.",
                self._vector_store.count(),
            )
            return 0

        logger.info("Starting ingestion from: %s", source)
        if source.is_dir():
            pages = self._loader.load_directory(source)
        else:
            pages = self._loader.load(source)

        if not pages:
            logger.warning("No pages extracted from %s", source)
            return 0

        chunks = self._chunker.chunk(pages)
        logger.info("Created %d chunks from %d pages", len(chunks), len(pages))

        count = self._vector_store.add_chunks(chunks, self._embedder)
        return count

    # ── Agentic Loop ──────────────────────────────────────────────────────────

    def ask(
        self,
        question: str,
        top_k: Optional[int] = None,
        show_trace: bool = True,
    ) -> GenerationResult:
        """
        The core Agentic Loop:
          Retrieve → (optionally print trace) → Generate → Return

        Args:
            question:   Natural-language question from the user.
            top_k:      Override number of retrieved chunks.
            show_trace: Print retrieved chunks to stdout for traceability.

        Returns:
            GenerationResult with answer and full trace.
        """
        logger.info("Processing question: %r", question)

        # Step 1: Retrieve
        trace: RetrievalTrace = self._retriever.retrieve(question, top_k=top_k)

        # Step 2: Traceability — print retrieved chunks
        if show_trace:
            self._print_trace(trace)

        # Step 3: Generate
        result: GenerationResult = self._generator.generate(trace)

        return result

    def reset_conversation(self) -> None:
        """Reset the generator's conversation history."""
        self._generator.reset_history()

    # ── Utilities ─────────────────────────────────────────────────────────────

    @property
    def corpus_size(self) -> int:
        """Number of chunks currently in the vector store."""
        return self._vector_store.count()

    @property
    def history_length(self) -> int:
        """Number of conversation turns stored in the generator's history."""
        # Each turn = 2 messages (user + model), so divide by 2
        return len(self._generator._history) // 2

    @staticmethod
    def _print_trace(trace: RetrievalTrace) -> None:
        """Print retrieval trace to stdout (required for assessment traceability)."""
        print("\n" + "=" * 70)
        print("📡  RETRIEVAL TRACE")
        print("=" * 70)
        print(f"Original query : {trace.original_query}")
        if len(trace.expanded_queries) > 1:
            print(f"Expanded queries: {trace.expanded_queries[1:]}")
        print(f"Chunks retrieved: {len(trace.retrieved_chunks)}")
        print("-" * 70)
        for i, chunk in enumerate(trace.retrieved_chunks, start=1):
            src = chunk.metadata.get("filename", chunk.source)
            pg = chunk.metadata.get("page_number", "?")
            print(f"\n[Chunk {i}] {src}  |  Page {pg}  |  Similarity: {chunk.similarity:.3f}")
            print(chunk.text[:300] + ("…" if len(chunk.text) > 300 else ""))
        print("=" * 70 + "\n")
