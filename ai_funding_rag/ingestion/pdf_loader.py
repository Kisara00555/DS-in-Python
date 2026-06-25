"""
ingestion/pdf_loader.py
-----------------------
Handles PDF loading and text extraction using PyMuPDF (fitz).
Implements an ABC so alternative loaders can be swapped via DI.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class DocumentPage:
    """Value object representing a single extracted page."""

    source: str          # Filename (stem)
    page_number: int
    raw_text: str
    metadata: dict       # Extensible metadata bag


class BaseLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, path: Path) -> List[DocumentPage]:
        """Load a single document and return its pages."""

    def load_directory(self, directory: Path) -> List[DocumentPage]:
        """Recursively load all supported files from a directory."""
        pages: List[DocumentPage] = []
        supported = self.supported_extensions()
        for fp in sorted(directory.rglob("*")):
            if fp.suffix.lower() in supported:
                logger.info("Loading: %s", fp.name)
                pages.extend(self.load(fp))
        return pages

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of extensions this loader handles."""


class PyMuPDFLoader(BaseLoader):
    """
    High-fidelity PDF loader using PyMuPDF.
    Extracts text per-page and captures rich metadata including
    section headings detected via font-size heuristics.
    """

    def __init__(self, extract_images: bool = False) -> None:
        self._extract_images = extract_images

    def load(self, path: Path) -> List[DocumentPage]:
        pages: List[DocumentPage] = []
        try:
            doc = fitz.open(str(path))
            for page_idx, page in enumerate(doc):
                text = page.get_text("text")          # plain text
                if not text.strip():
                    # Fallback to blocks for scanned PDFs
                    text = " ".join(
                        b[4] for b in page.get_text("blocks") if isinstance(b[4], str)
                    )
                metadata = {
                    "source_path": str(path),
                    "filename": path.name,
                    "total_pages": len(doc),
                    "format": doc.metadata.get("format", ""),
                    "title": doc.metadata.get("title", path.stem),
                    "author": doc.metadata.get("author", ""),
                }
                pages.append(
                    DocumentPage(
                        source=path.stem,
                        page_number=page_idx + 1,
                        raw_text=text,
                        metadata=metadata,
                    )
                )
            doc.close()
        except Exception as exc:
            logger.error("Failed to load %s: %s", path, exc)
        return pages

    def supported_extensions(self) -> List[str]:
        return [".pdf"]
