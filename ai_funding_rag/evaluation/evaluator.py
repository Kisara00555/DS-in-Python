"""
evaluation/evaluator.py
-----------------------
RAG Triad evaluation framework.

The RAG Triad (coined by TruEra/TruLens) measures three orthogonal dimensions
of RAG quality in a single evaluation pass:

  1. Context Relevance   – Were the retrieved chunks relevant to the question?
  2. Faithfulness        – Is the answer grounded in the retrieved context?
  3. Answer Relevance    – Does the answer actually address the question asked?

Uses an LLM-as-judge approach against a structured ground-truth dataset.
Results are saved as both JSON (machine-readable) and HTML (human-readable proof).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types as genai_types

from ..config.settings import Settings

logger = logging.getLogger(__name__)


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class GroundTruthItem:
    """A single QA pair from the evaluation dataset."""

    question_id: str
    question: str
    ground_truth_answer: str
    expected_keywords: List[str] = field(default_factory=list)


@dataclass
class EvaluationRecord:
    """
    Result of evaluating a single question across the full RAG Triad.

    RAG Triad scores (all 0.0–1.0):
      context_relevance  – retrieved chunks relevant to the question?
      faithfulness       – answer grounded in the retrieved context?
      answer_relevance   – answer addresses the question?
    """

    question_id: str
    question: str
    ground_truth: str
    system_answer: str
    context_relevance_score: float   # RAG Triad leg 1
    faithfulness_score: float        # RAG Triad leg 2
    answer_relevance_score: float    # RAG Triad leg 3
    judge_reasoning: str
    retrieved_sources: List[str] = field(default_factory=list)

    @property
    def rag_score(self) -> float:
        """Aggregate RAG Triad score (harmonic mean of the 3 legs)."""
        scores = [
            self.context_relevance_score,
            self.faithfulness_score,
            self.answer_relevance_score,
        ]
        # Harmonic mean penalises any single low leg more than arithmetic mean
        if any(s == 0.0 for s in scores):
            return 0.0
        return len(scores) / sum(1.0 / s for s in scores)


@dataclass
class EvaluationReport:
    """Aggregated RAG Triad evaluation report."""

    records: List[EvaluationRecord]
    avg_context_relevance: float
    avg_faithfulness: float
    avg_answer_relevance: float
    avg_rag_score: float
    total_questions: int
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        return {
            "evaluated_at": self.evaluated_at,
            "summary": {
                "total_questions": self.total_questions,
                "avg_context_relevance": round(self.avg_context_relevance, 4),
                "avg_faithfulness": round(self.avg_faithfulness, 4),
                "avg_answer_relevance": round(self.avg_answer_relevance, 4),
                "avg_rag_score": round(self.avg_rag_score, 4),
            },
            "records": [
                {
                    "question_id": r.question_id,
                    "question": r.question,
                    "ground_truth": r.ground_truth,
                    "system_answer": r.system_answer,
                    "context_relevance_score": r.context_relevance_score,
                    "faithfulness_score": r.faithfulness_score,
                    "answer_relevance_score": r.answer_relevance_score,
                    "rag_score": round(r.rag_score, 4),
                    "judge_reasoning": r.judge_reasoning,
                    "retrieved_sources": r.retrieved_sources,
                }
                for r in self.records
            ],
        }

    def generate_html_report(self, output_path: Path) -> None:
        """Write a styled, self-contained HTML evaluation report to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def score_badge(score: float) -> str:
            """Return a colour-coded badge for a score."""
            pct = int(score * 100)
            if score >= 0.8:
                colour = "#22c55e"   # green
            elif score >= 0.6:
                colour = "#f59e0b"   # amber
            else:
                colour = "#ef4444"   # red
            return (
                f'<span style="background:{colour};color:#fff;'
                f'padding:2px 8px;border-radius:12px;font-weight:600;'
                f'font-size:0.85em;">{pct}%</span>'
            )

        rows_html = ""
        for r in self.records:
            rows_html += f"""
            <tr>
              <td class="qid">{r.question_id}</td>
              <td class="question">{r.question}</td>
              <td class="score">{score_badge(r.context_relevance_score)}</td>
              <td class="score">{score_badge(r.faithfulness_score)}</td>
              <td class="score">{score_badge(r.answer_relevance_score)}</td>
              <td class="score">{score_badge(r.rag_score)}</td>
              <td class="reasoning">{r.judge_reasoning}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAG Triad Evaluation Report – AI Funding Assistant</title>
  <style>
    :root {{
      --bg: #0f172a; --surface: #1e293b; --border: #334155;
      --text: #e2e8f0; --muted: #94a3b8; --accent: #6366f1;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg); color: var(--text); padding: 2rem; }}
    h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }}
    .subtitle {{ color: var(--muted); margin-bottom: 2rem; font-size: 0.95rem; }}
    .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 2rem; }}

    /* Summary cards */
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr));
              gap: 1rem; margin-bottom: 2.5rem; }}
    .card {{ background: var(--surface); border: 1px solid var(--border);
             border-radius: 12px; padding: 1.25rem; text-align: center; }}
    .card-label {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: .06em;
                   color: var(--muted); margin-bottom: 0.5rem; }}
    .card-value {{ font-size: 2rem; font-weight: 700; }}
    .card-value.green {{ color: #22c55e; }}
    .card-value.amber {{ color: #f59e0b; }}
    .card-value.red   {{ color: #ef4444; }}

    /* Legend */
    .legend {{ display: flex; gap: 1.5rem; margin-bottom: 1.5rem; font-size: 0.82rem; }}
    .legend-item {{ display: flex; align-items: center; gap: 0.4rem; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; }}

    /* Table */
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--surface);
             border-radius: 12px; overflow: hidden; }}
    thead {{ background: #273548; }}
    th {{ padding: 0.85rem 1rem; text-align: left; font-size: 0.78rem;
          text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }}
    td {{ padding: 0.85rem 1rem; border-top: 1px solid var(--border);
          vertical-align: top; font-size: 0.88rem; }}
    tr:hover td {{ background: rgba(99,102,241,.06); }}
    .qid {{ font-weight: 700; color: var(--accent); white-space: nowrap; }}
    .question {{ max-width: 280px; }}
    .score {{ text-align: center; white-space: nowrap; }}
    .reasoning {{ color: var(--muted); font-size: 0.8rem; max-width: 260px; }}

    /* Triad explanation */
    .triad {{ background: var(--surface); border: 1px solid var(--border);
              border-radius: 12px; padding: 1.5rem; margin-bottom: 2.5rem; }}
    .triad h2 {{ font-size: 1rem; margin-bottom: 1rem; color: var(--accent); }}
    .triad-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
    .triad-item {{ background: #273548; border-radius: 8px; padding: 1rem; }}
    .triad-item h3 {{ font-size: 0.85rem; margin-bottom: 0.4rem; }}
    .triad-item p {{ font-size: 0.78rem; color: var(--muted); line-height: 1.5; }}

    footer {{ margin-top: 2rem; text-align: center; font-size: 0.8rem; color: var(--muted); }}
  </style>
</head>
<body>
  <h1>🔬 RAG Triad Evaluation Report</h1>
  <div class="subtitle">AI Startup Funding &amp; Investment Intelligence Assistant — DS205.3</div>
  <div class="meta">Evaluated: {self.evaluated_at} &nbsp;|&nbsp; Questions: {self.total_questions}</div>

  <!-- Summary Cards -->
  <div class="cards">
    <div class="card">
      <div class="card-label">Avg RAG Score</div>
      <div class="card-value {'green' if self.avg_rag_score >= 0.8 else 'amber' if self.avg_rag_score >= 0.6 else 'red'}">{self.avg_rag_score:.0%}</div>
    </div>
    <div class="card">
      <div class="card-label">Context Relevance</div>
      <div class="card-value {'green' if self.avg_context_relevance >= 0.8 else 'amber' if self.avg_context_relevance >= 0.6 else 'red'}">{self.avg_context_relevance:.0%}</div>
    </div>
    <div class="card">
      <div class="card-label">Faithfulness</div>
      <div class="card-value {'green' if self.avg_faithfulness >= 0.8 else 'amber' if self.avg_faithfulness >= 0.6 else 'red'}">{self.avg_faithfulness:.0%}</div>
    </div>
    <div class="card">
      <div class="card-label">Answer Relevance</div>
      <div class="card-value {'green' if self.avg_answer_relevance >= 0.8 else 'amber' if self.avg_answer_relevance >= 0.6 else 'red'}">{self.avg_answer_relevance:.0%}</div>
    </div>
    <div class="card">
      <div class="card-label">Total Questions</div>
      <div class="card-value" style="color:var(--accent)">{self.total_questions}</div>
    </div>
  </div>

  <!-- RAG Triad Explanation -->
  <div class="triad">
    <h2>📐 The RAG Triad (TruEra Framework)</h2>
    <div class="triad-grid">
      <div class="triad-item">
        <h3>1. Context Relevance</h3>
        <p>Are the retrieved chunks actually relevant to the user's question? Detects retrieval failures and poor embedding quality.</p>
      </div>
      <div class="triad-item">
        <h3>2. Faithfulness</h3>
        <p>Is the generated answer grounded in the retrieved context? Detects hallucination — claims not supported by the source documents.</p>
      </div>
      <div class="triad-item">
        <h3>3. Answer Relevance</h3>
        <p>Does the answer directly address the question asked? Detects off-topic or evasive responses even when context was good.</p>
      </div>
    </div>
  </div>

  <!-- Legend -->
  <div class="legend">
    <div class="legend-item"><div class="dot" style="background:#22c55e"></div> ≥ 80% Good</div>
    <div class="legend-item"><div class="dot" style="background:#f59e0b"></div> 60–79% Acceptable</div>
    <div class="legend-item"><div class="dot" style="background:#ef4444"></div> &lt; 60% Needs Improvement</div>
  </div>

  <!-- Results Table -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Question</th>
          <th>Context Rel.</th>
          <th>Faithfulness</th>
          <th>Ans. Rel.</th>
          <th>RAG Score</th>
          <th>Judge Reasoning</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  <footer>
    DS205.3 – Data Science with Python &nbsp;|&nbsp; LLM-as-Judge evaluation via Google Gemini &nbsp;|&nbsp; RAG Triad methodology
  </footer>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("HTML evaluation report saved to %s", output_path)


# ── Judge Prompt ───────────────────────────────────────────────────────────────

JUDGE_PROMPT = """You are an expert evaluator assessing a RAG (Retrieval-Augmented Generation) system.
You will score the system across the THREE dimensions of the RAG Triad.

== QUESTION ==
{question}

== RETRIEVED CONTEXT ==
{retrieved_context}

== SYSTEM ANSWER ==
{system_answer}

== GROUND TRUTH ANSWER ==
{ground_truth}

Score each dimension on a scale of 0.0 to 1.0:

1. CONTEXT RELEVANCE (0.0–1.0):
   Is the retrieved context actually relevant to the question?
   - 1.0 = all retrieved chunks are directly relevant to the question
   - 0.5 = some chunks relevant, some are off-topic
   - 0.0 = retrieved chunks have nothing to do with the question

2. FAITHFULNESS (0.0–1.0):
   Is the system answer grounded in (supported by) the retrieved context?
   - 1.0 = every claim in the answer can be traced to the retrieved context
   - 0.5 = some claims supported, some appear hallucinated
   - 0.0 = answer is fabricated / contradicts the context

3. ANSWER RELEVANCE (0.0–1.0):
   Does the system answer directly address the question asked?
   - 1.0 = answer fully and directly addresses the question
   - 0.5 = partially answers the question
   - 0.0 = answer is off-topic or refuses to answer

Respond ONLY with this exact JSON (no markdown, no extra text):
{{
  "context_relevance_score": <float 0.0-1.0>,
  "faithfulness_score": <float 0.0-1.0>,
  "answer_relevance_score": <float 0.0-1.0>,
  "reasoning": "<one concise sentence explaining the scores>"
}}"""


# ── Evaluator ──────────────────────────────────────────────────────────────────

class Evaluator:
    """
    LLM-as-judge evaluator implementing the full RAG Triad.

    Loads ground-truth QA pairs, runs each question through the RAG agent,
    then scores each response across Context Relevance, Faithfulness, and
    Answer Relevance using Gemini as an impartial judge.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.google_api_key)
        self._gen_config = genai_types.GenerateContentConfig(temperature=0.0)

    # ── public ────────────────────────────────────────────────────────────────

    def load_ground_truth(self, path: Optional[Path] = None) -> List[GroundTruthItem]:
        """Load ground-truth QA pairs from a JSON file."""
        p = path or self._settings.eval_dataset_path
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = [
            GroundTruthItem(
                question_id=item["question_id"],
                question=item["question"],
                ground_truth_answer=item["ground_truth_answer"],
                expected_keywords=item.get("expected_keywords", []),
            )
            for item in data
        ]
        logger.info("Loaded %d ground-truth items", len(items))
        return items

    def evaluate_answer(
        self,
        question: str,
        ground_truth: str,
        system_answer: str,
        retrieved_context: str = "",
        retrieved_sources: Optional[List[str]] = None,
        question_id: str = "q0",
    ) -> EvaluationRecord:
        """Score a single system answer across the full RAG Triad."""
        prompt = JUDGE_PROMPT.format(
            question=question,
            retrieved_context=retrieved_context or "(no context provided)",
            system_answer=system_answer,
            ground_truth=ground_truth,
        )
        response = self._client.models.generate_content(
            model=self._settings.llm_model,
            contents=prompt,
            config=self._gen_config,
        )
        raw = response.text or "{}"
        # Strip markdown code fences if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"```$", "", raw.strip())
        try:
            scores = json.loads(raw)
            context_relevance = float(scores.get("context_relevance_score", 0.0))
            faithfulness = float(scores.get("faithfulness_score", 0.0))
            answer_relevance = float(scores.get("answer_relevance_score", 0.0))
            reasoning = scores.get("reasoning", "")
        except (json.JSONDecodeError, ValueError):
            context_relevance = 0.0
            faithfulness = 0.0
            answer_relevance = 0.0
            reasoning = "Parse error – raw response: " + raw[:120]

        return EvaluationRecord(
            question_id=question_id,
            question=question,
            ground_truth=ground_truth,
            system_answer=system_answer,
            context_relevance_score=context_relevance,
            faithfulness_score=faithfulness,
            answer_relevance_score=answer_relevance,
            judge_reasoning=reasoning,
            retrieved_sources=retrieved_sources or [],
        )

    def run_full_evaluation(
        self,
        agent,   # RAGAgent — typed as Any to avoid circular import
        ground_truth_path: Optional[Path] = None,
    ) -> EvaluationReport:
        """
        Run end-to-end RAG Triad evaluation against the ground-truth dataset.
        Saves results as JSON and as a styled HTML report.
        """
        items = self.load_ground_truth(ground_truth_path)
        records: List[EvaluationRecord] = []

        for item in items:
            logger.info("Evaluating %s: %s", item.question_id, item.question[:60])
            result = agent.ask(item.question, show_trace=False)

            # Pass the actual retrieved context to the judge for Context Relevance scoring
            sources = [
                c.metadata.get("filename", c.source)
                for c in result.trace.retrieved_chunks
            ]
            record = self.evaluate_answer(
                question=item.question,
                ground_truth=item.ground_truth_answer,
                system_answer=result.answer,
                retrieved_context=result.trace.context_text,
                retrieved_sources=sources,
                question_id=item.question_id,
            )
            records.append(record)
            print(
                f"  [{item.question_id}] "
                f"CtxRel={record.context_relevance_score:.2f} | "
                f"Faith={record.faithfulness_score:.2f} | "
                f"AnsRel={record.answer_relevance_score:.2f} | "
                f"RAG={record.rag_score:.2f}"
            )

        avg_ctx  = sum(r.context_relevance_score for r in records) / len(records) if records else 0.0
        avg_fth  = sum(r.faithfulness_score       for r in records) / len(records) if records else 0.0
        avg_ans  = sum(r.answer_relevance_score   for r in records) / len(records) if records else 0.0
        avg_rag  = sum(r.rag_score                for r in records) / len(records) if records else 0.0

        report = EvaluationReport(
            records=records,
            avg_context_relevance=avg_ctx,
            avg_faithfulness=avg_fth,
            avg_answer_relevance=avg_ans,
            avg_rag_score=avg_rag,
            total_questions=len(records),
        )

        # ── Persist JSON ──────────────────────────────────────────────────────
        out_json = self._settings.eval_results_path
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info("JSON results saved to %s", out_json)

        # ── Persist HTML ──────────────────────────────────────────────────────
        out_html = out_json.with_name("report.html")
        report.generate_html_report(out_html)

        return report
