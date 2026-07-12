"""
evaluate.py
-----------
CLI entry point: run the full RAG evaluation suite.

Evaluation dimensions scored:
  RAG Triad (TruEra framework):
    1. Context Relevance  – retrieved chunks relevant to the question?
    2. Faithfulness       – answer grounded in the retrieved context?
    3. Answer Relevance   – answer addresses the question?

  Extended deterministic metrics:
    4. Keyword Precision  – expected keywords found in the answer?
    5. Keyword Recall     – coverage of expected keywords?
    6. F1 Score           – harmonic mean of precision and recall
    7. Cosine Similarity  – semantic similarity (ground-truth vs system answer)

Usage:
    python evaluate.py
    python evaluate.py --dataset ./data/evaluation/ground_truth.json
    python evaluate.py --output ./data/evaluation/my_results.json
    python evaluate.py --question "What is a SAFE note?"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Fix for Windows terminal emoji printing
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run RAG evaluation on the AI Funding assistant."
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
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="Evaluate a single question instead of the full dataset. "
             "Example: --question \"What is a SAFE note?\"",
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

    # ── Single-question mode ──────────────────────────────────────────────────
    if args.question:
        print(f"\n🔬  Evaluating single question: {args.question!r}\n")
        result = agent.ask(args.question, show_trace=False)
        sources = [c.metadata.get("filename", "Unknown") for c in result.trace.retrieved_chunks]
        record = evaluator.evaluate_answer(
            question=args.question,
            ground_truth="(no ground truth — ad-hoc evaluation)",
            system_answer=result.answer,
            retrieved_context=result.trace.context_text,
            retrieved_sources=sources,
            question_id="adhoc",
        )
        print(f"  Context Relevance : {record.context_relevance_score:.2f}")
        print(f"  Faithfulness      : {record.faithfulness_score:.2f}")
        print(f"  Answer Relevance  : {record.answer_relevance_score:.2f}")
        print(f"  RAG Score         : {record.rag_score:.2f}")
        print(f"  Precision         : {record.precision:.2f}")
        print(f"  Recall            : {record.recall:.2f}")
        print(f"  F1 Score          : {record.f1_score:.2f}")
        print(f"  Cosine Similarity : {record.cosine_similarity:.2f}")
        print(f"  Reasoning         : {record.judge_reasoning}")
        print(f"\n  Answer:\n{result.answer}")
        return

    # ── Full evaluation mode ──────────────────────────────────────────────────
    print(f"\n🔬  Running full evaluation on {settings.eval_dataset_path} …")
    print("    Scoring: RAG Triad + Precision/Recall/F1/Cosine Similarity\n")
 
    report = evaluator.run_full_evaluation(agent, ground_truth_path=args.dataset)

    html_path = settings.eval_results_path.with_name("report.html")

    print("\n" + "=" * 90)
    print("📊  EVALUATION SUMMARY")
    print("=" * 90)
    print(f"  Total Questions      : {report.total_questions}")
    print(f"  ─── RAG Triad (LLM-as-Judge) ───")
    print(f"  Avg Context Relevance: {report.avg_context_relevance:.2%}")
    print(f"  Avg Faithfulness     : {report.avg_faithfulness:.2%}")
    print(f"  Avg Answer Relevance : {report.avg_answer_relevance:.2%}")
    print(f"  Avg RAG Score        : {report.avg_rag_score:.2%}  (harmonic mean)")
    print(f"  Pass Rate (≥0.75)    : {report.pass_rate:.2%}")
    print(f"  ─── Extended Metrics (Deterministic) ───")
    print(f"  Avg Precision        : {report.avg_precision:.2%}")
    print(f"  Avg Recall           : {report.avg_recall:.2%}")
    print(f"  Avg F1 Score         : {report.avg_f1_score:.2%}")
    print(f"  Avg Cosine Similarity: {report.avg_cosine_similarity:.2%}")
    print("=" * 90)
    print(f"\n  📄  JSON  → {settings.eval_results_path}")
    print(f"  🌐  HTML  → {html_path}") 
    print()

    # Per-question table
    header = "{:<6} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8}"
    print(header.format("ID", "Ctx Rel", "Faith", "Ans Rel", "RAG", "Prec", "Recall", "F1", "CosSim"))
    print("-" * 82)
    for r in report.records:
        print(header.format(
            r.question_id,
            f"{r.context_relevance_score:.2f}",
            f"{r.faithfulness_score:.2f}",
            f"{r.answer_relevance_score:.2f}",
            f"{r.rag_score:.2f}",
            f"{r.precision:.2f}",
            f"{r.recall:.2f}",
            f"{r.f1_score:.2f}",
            f"{r.cosine_similarity:.2f}",
        ))
    print()

    # Best and worst
    print("🏆  Best Questions:") 
    for r in report.best_questions():
        print(f"    [{r.question_id}] {r.question[:70]}  → {r.rag_score:.2f}")
    print("\n⚠️   Worst Questions:")
    for r in report.worst_questions():
        print(f"    [{r.question_id}] {r.question[:70]}  → {r.rag_score:.2f}")
    print()

    # Auto-generate evaluation charts
    print("📈  Generating evaluation charts …")
    try:
        from plot_evaluation import generate_all_charts
        generate_all_charts(settings.eval_results_path)
        print("  ✅ Charts saved to data/evaluation/\n")
    except Exception as e:
        print(f"  ⚠️  Chart generation skipped: {e}\n")


if __name__ == "__main__":
    main()

# Ensure the vector store is populated before running full dataset evaluations to avoid zero-hit errors.
