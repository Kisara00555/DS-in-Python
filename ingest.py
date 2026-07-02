"""
ingest.py
---------
CLI script to ingest PDFs into the vector store.

Usage:
    python ingest.py --source ./data/pdfs
    python ingest.py --source ./data/pdfs --force
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
from pathlib import Path

# ── Fix emoji output on Windows (cp1252 console) ────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest PDFs into the AI Funding RAG vector store."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("./data/pdfs"),
        help="Path to a PDF file or directory of PDFs (default: ./data/pdfs)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion even if vector store already has data",
    )
    args = parser.parse_args()

    # ── Import here to avoid circular imports at module level ────────────────
    from ai_funding_rag.config.settings import default_settings
    from ai_funding_rag.agent.rag_agent import RAGAgent

    settings = default_settings
    settings.validate()

    if not args.source.exists():
        logger.error("Source path does not exist: %s", args.source)
        sys.exit(1)

    agent = RAGAgent(settings=settings)
    print(f"\n🔄  Ingesting from: {args.source}")
    count = agent.ingest(source=args.source, force=args.force)

    if count > 0:
        print(f"✅  Successfully stored {count} chunks.")
    else:
        print(f"ℹ️   Vector store already populated ({agent.corpus_size} chunks). "
              f"Use --force to re-ingest.")
    print(f"📦  Total corpus size: {agent.corpus_size} chunks\n")


if __name__ == "__main__":
    main()
