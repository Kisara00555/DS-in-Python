"""
ingestion/chunker.py
--------------------
Splits raw document pages into overlapping text chunks.
Implements a BaseChunker ABC so chunking strategies are interchangeable.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from .pdf_loader import DocumentPage

MIN_CHUNK_LENGTH = 50  # Characters — shorter chunks are noise


@dataclass
class TextChunk:
    """Value object representing a single text chunk ready for embedding."""

    chunk_id: str           # Unique ID: "{source}_p{page}_{idx}"
    source: str
    page_number: int
    text: str
    metadata: dict = field(default_factory=dict)


class BaseChunker(ABC):
    """Abstract chunker interface."""

    @abstractmethod
    def chunk(self, pages: List[DocumentPage]) -> List[TextChunk]:
        """Split pages into chunks."""


class SlidingWindowChunker(BaseChunker):
    """
    Sliding-window chunker with configurable size and overlap.
    Uses character-level splitting with sentence boundary awareness.

    Strategy rationale:
      - chunk_size=800 chars  → fits ~200 tokens, ideal for embedding models
      - overlap=150 chars     → preserves cross-boundary context for retrieval
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        """
        Initialise the chunker with sliding window parameters.

        Args:
            chunk_size:    Maximum character length of each chunk.
            chunk_overlap: Number of characters to overlap between consecutive chunks
                           to preserve cross-boundary context.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ── public ───────────────────────────────────────────────────────────────

    def chunk(self, pages: List[DocumentPage]) -> List[TextChunk]:
        """
        Split a list of document pages into overlapping TextChunks.

        Chunks shorter than MIN_CHUNK_LENGTH (50 chars) are discarded to
        avoid storing noisy fragments such as headers or stray punctuation.

        Args:
            pages: List of DocumentPage objects from the loader.

        Returns:
            Flat list of TextChunk objects ordered by source and page.
        """
        chunks: List[TextChunk] = []
        for page in pages:
            page_chunks = self._split_text(page.raw_text)
            idx = 0
            for text in page_chunks:
                if len(text) < MIN_CHUNK_LENGTH:
                    continue  # Skip noise chunks
                chunk_id = f"{page.source}_p{page.page_number}_{idx}"
                chunks.append(
                    TextChunk( 
                        chunk_id=chunk_id,
                        source=page.source,
                        page_number=page.page_number,
                        text=text,
                        metadata={
                            **page.metadata,
                            "chunk_index": idx,
                            "chunk_id": chunk_id,
                        },
                    )
                )
                idx += 1
        return chunks

    def chunk_count(self, pages: List[DocumentPage]) -> int:
        """
        Preview the total number of chunks that would be produced without storing them.

        Useful for estimating ingestion cost before committing.

        Args:
            pages: List of DocumentPage objects from the loader.

        Returns:
            Integer count of chunks that would be created (after noise filtering).
        """
        count = 0
        for page in pages:
            for text in self._split_text(page.raw_text):
                if len(text) >= MIN_CHUNK_LENGTH:
                    count += 1
        return count

    # ── private ──────────────────────────────────────────────────────────────

    def _split_text(self, text: str) -> List[str]:
        """Split text using sentence-aware sliding window."""
        # Normalise whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []

        sentences = self._sentence_split(text)
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for sentence in sentences:
            s_len = len(sentence)
            if current_len + s_len > self.chunk_size and current:
                chunks.append(" ".join(current))
                # Overlap: keep last sentences that fit within overlap window
                overlap_buf: List[str] = []
                overlap_len = 0
                for sent in reversed(current):
                    if overlap_len + len(sent) <= self.chunk_overlap:
                        overlap_buf.insert(0, sent)
                        overlap_len += len(sent)
                    else:
                        break
                current = overlap_buf
                current_len = overlap_len
            current.append(sentence)
            current_len += s_len

        if current:
            chunks.append(" ".join(current))

        return chunks

    @staticmethod
    def _sentence_split(text: str) -> List[str]:
        """Simple regex sentence splitter."""
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

# The overlap ensures that context spanning across chunk boundaries is not lost, maintaining semantic integrity for retrieval.
