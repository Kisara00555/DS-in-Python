"""
evaluate.py
-----------
CLI entry point: run the full RAG Triad evaluation suite.

RAG Triad dimensions scored (TruEra framework):
  1. Context Relevance  – retrieved chunks relevant to the question?
  2. Faithfulness       – answer grounded in the retrieved context?
  3. Answer Relevance   – answer addresses the question?

Usage:
    python evaluate.py
    python evaluate.py --dataset ./data/evaluation/ground_truth.json
    python evaluate.py --output ./data/evaluation/my_results.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run RAG Triad evaluation on the AI Funding assistant."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=None,
        help="Path to ground-truth JSON file (default: from settings)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for evaluation results JSON (default: from settings)",
    )
    args = parser.parse_args()

    from ai_funding_rag.config.settings import default_settings
    from ai_funding_rag.agent.rag_agent import RAGAgent
    from ai_funding_rag.evaluation.evaluator import Evaluator

    settings = default_settings
    if args.output:
        settings.eval_results_path = args.output

    try:
        settings.validate()
    except EnvironmentError as e:
        print(f"❌  Configuration error: {e}")
        sys.exit(1)

    agent = RAGAgent(settings=settings)
    if agent.corpus_size == 0:
        print("⚠️   Vector store is empty. Run `python ingest.py` first.")
        sys.exit(1)

    evaluator = Evaluator(settings=settings)

    print(f"\n🔬  Running RAG Triad evaluation on {settings.eval_dataset_path} …")
    print("    Scoring: Context Relevance | Faithfulness | Answer Relevance\n")

    report = evaluator.run_full_evaluation(agent, ground_truth_path=args.dataset)

    html_path = settings.eval_results_path.with_name("report.html")

    print("\n" + "=" * 72)
    print("📊  RAG TRIAD EVALUATION SUMMARY")
    print("=" * 72)
    print(f"  Total Questions      : {report.total_questions}")
    print(f"  Avg Context Relevance: {report.avg_context_relevance:.2%}")
    print(f"  Avg Faithfulness     : {report.avg_faithfulness:.2%}")
    print(f"  Avg Answer Relevance : {report.avg_answer_relevance:.2%}")
    print(f"  ─────────────────────────────────")
    print(f"  Avg RAG Score        : {report.avg_rag_score:.2%}  (harmonic mean)")
    print("=" * 72)
    print(f"\n  📄  JSON  → {settings.eval_results_path}")
    print(f"  🌐  HTML  → {html_path}")
    print()

    # Per-question table
    col = "{:<6} {:>12} {:>13} {:>12} {:>10}"
    print(col.format("ID", "Ctx Rel", "Faithfulness", "Ans Rel", "RAG Score"))
    print("-" * 58)
    for r in report.records:
        print(col.format(
            r.question_id,
            f"{r.context_relevance_score:.2f}",
            f"{r.faithfulness_score:.2f}",
            f"{r.answer_relevance_score:.2f}",
            f"{r.rag_score:.2f}",
        ))
    print()


if __name__ == "__main__":
    main()
