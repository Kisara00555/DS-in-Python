"""
chat.py
-------
Interactive CLI chat interface for the RAG assistant.

Usage:
    python chat.py
    python chat.py --no-trace          # hide retrieval trace
    python chat.py --top-k 8           # retrieve 8 chunks per query
"""

from __future__ import annotations

import argparse
import logging
import sys
import io

# ── Fix emoji/unicode output on Windows (cp1252 console) ────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.WARNING,          # Keep logs quiet during interactive chat
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   🚀  AI Startup Funding & Investment Intelligence Assistant  ║
║       Powered by RAG + Groq (Llama 3.1)                      ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:  'quit' / 'exit'  → exit                         ║
║             'reset'          → clear conversation history    ║
║             'corpus'         → show corpus size              ║
╚══════════════════════════════════════════════════════════════╝
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the AI Funding RAG assistant.")
    parser.add_argument("--no-trace", action="store_true", help="Hide retrieval trace")
    parser.add_argument("--top-k", type=int, default=None, help="Number of chunks to retrieve")
    args = parser.parse_args()

    from ai_funding_rag.config.settings import default_settings
    from ai_funding_rag.agent.rag_agent import RAGAgent

    settings = default_settings
    try:
        settings.validate()
    except EnvironmentError as e:
        print(f"❌  Configuration error: {e}")
        sys.exit(1)

    agent = RAGAgent(settings=settings)

    if agent.corpus_size == 0:
        print("⚠️   Vector store is empty. Run `python ingest.py` first.")
        sys.exit(1)

    print(BANNER)
    print(f"📦  Corpus: {agent.corpus_size} chunks loaded.\n")

    show_trace = not args.no_trace

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye! 👋")
            break
        elif user_input.lower() == "reset":
            agent.clear_history()
            print("✅  Conversation history cleared.\n")
            continue
        elif user_input.lower() == "corpus":
            print(f"📦  Corpus size: {agent.corpus_size} chunks\n")
            continue

        result = agent.ask(
            question=user_input,
            top_k=args.top_k,
            show_trace=show_trace,
        )

        print(f"\n🤖  Assistant:\n{result.answer}")
        print(f"\n   [Tokens used: {result.input_tokens} in / {result.output_tokens} out | "
              f"Model: {result.model_used}]\n")
        print("─" * 70 + "\n")


if __name__ == "__main__":
    main()
