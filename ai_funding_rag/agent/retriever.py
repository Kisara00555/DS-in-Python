"""
agent/retriever.py
------------------
Retriever component: takes a user query, expands it (optional),
searches the vector store, and returns ranked chunks with full traceability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai
from google.genai import types as genai_types

from ..config.settings import Settings
from ..vectorstore.embedder import BaseEmbedder
from ..vectorstore.store import BaseVectorStore, RetrievedChunk
from .prompts import QUERY_EXPANSION_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class RetrievalTrace:
    """Full traceability record for a single retrieval operation."""

    original_query: str
    expanded_queries: List[str]
    retrieved_chunks: List[RetrievedChunk]
    context_text: str          # Formatted context fed to the LLM


class Retriever:
    """
    Orchestrates query expansion + vector search + deduplication.

    Traceability: every retrieval produces a RetrievalTrace object
    that records exactly which chunks were retrieved and from which source,
    so the user can audit what context influenced the LLM's answer.
    """

    def __init__(
        self,
        settings: Settings,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        use_query_expansion: bool = True,
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._vector_store = vector_store
        self._use_query_expansion = use_query_expansion
        self._client = genai.Client(api_key=settings.google_api_key)

    # ── public ───────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: Optional[int] = None) -> RetrievalTrace:
        k = top_k or self._settings.top_k
        expanded_queries = [query]

        if self._use_query_expansion:
            expanded_queries = self._expand_query(query)
            logger.info("Expanded queries: %s", expanded_queries)

        # Retrieve for each expanded query and merge
        all_chunks: List[RetrievedChunk] = []
        for q in expanded_queries:
            chunks = self._vector_store.search(
                query=q, embedder=self._embedder, top_k=k
            )
            all_chunks.extend(chunks)

        # Deduplicate by chunk_id, keeping best (lowest) distance
        seen: dict[str, RetrievedChunk] = {}
        for chunk in all_chunks:
            if chunk.chunk_id not in seen or chunk.distance < seen[chunk.chunk_id].distance:
                seen[chunk.chunk_id] = chunk

        # Sort by similarity descending and trim
        top_chunks = sorted(seen.values(), key=lambda c: c.distance)[:k]

        context_text = self._format_context(top_chunks)

        logger.info(
            "Retrieved %d unique chunks for query: %r", len(top_chunks), query
        )

        return RetrievalTrace(
            original_query=query,
            expanded_queries=expanded_queries,
            retrieved_chunks=top_chunks,
            context_text=context_text,
        )

    # ── private ──────────────────────────────────────────────────────────────

    def _expand_query(self, query: str) -> List[str]:
        """Use LLM to generate semantically diverse search queries."""
        try:
            prompt = QUERY_EXPANSION_TEMPLATE.format(question=query)
            response = self._client.models.generate_content(
                model=self._settings.llm_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=200,
                ),
            )
            raw = response.text or ""
            queries = [q.strip() for q in raw.strip().split("\n") if q.strip()]
            return [query] + queries[:3]   # Original + up to 3 expansions
        except Exception as exc:
            logger.warning("Query expansion failed (%s); using original query.", exc)
            return [query]

    @staticmethod
    def _format_context(chunks: List[RetrievedChunk]) -> str:
        """Format chunks into a numbered context block for the LLM."""
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("filename", chunk.chunk_id)
            page = chunk.metadata.get("page_number", "?")  # Note: stored as int
            # page_number may be stored under different keys depending on chunker
            page = chunk.metadata.get("page_number", page)
            parts.append(
                f"[{i}] Source: {source}, Page {page} "
                f"(similarity={chunk.similarity:.3f})\n"
                f"{chunk.text}"
            )
        return "\n\n---\n\n".join(parts)
