import { useState } from "react";
import { api } from "../api";
import "./EvalPanel.css";

export default function EvalPanel({ status }) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const runEval = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runEvaluation();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const s = report?.summary ?? null;

  function scoreColor(val) {
    if (val >= 0.8) return "text-green";
    if (val >= 0.6) return "text-amber";
    return "text-red";
  }

  return (
    <div className="eval-panel">
      <div className="eval-content">
        <h2 className="panel-heading">📊 RAG Triad Evaluation</h2>
        <p className="panel-sub">
          Scores the system across all three dimensions of the RAG Triad against 15 ground-truth QA pairs.
        </p>

        {/* RAG Triad info card */}
        <div className="eval-info-card glass">
          <div className="eval-info-icon">🔬</div>
          <div>
            <strong>The RAG Triad (TruEra Framework)</strong>
            <p>
              Three orthogonal metrics that together capture full RAG quality:
              {" "}<span className="text-blue">Context Relevance</span> (were the retrieved chunks useful?),
              {" "}<span className="text-cyan">Faithfulness</span> (is the answer grounded in context — no hallucinations?), and
              {" "}<span className="text-purple">Answer Relevance</span> (does the answer address the question?).
              The aggregate <strong>RAG Score</strong> is the harmonic mean of all three.
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button
            id="btn-run-eval"
            className="btn btn-primary"
            onClick={runEval}
            disabled={loading || !status?.ready}
          >
            {loading ? (
              <><span className="spinner" /> Running RAG Triad evaluation… (2–3 min)</>
            ) : (
              "▶ Run Full Evaluation"
            )}
          </button>

          {report && (
            <button
              id="btn-download-json"
              className="btn btn-ghost"
              onClick={() => {
                const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "rag_evaluation_report.json";
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              ⬇️ Download JSON
            </button>
          )}
        </div>

        {!status?.ready && (
          <div className="eval-warning">
            ⚠️ System not ready. Ingest PDFs first in Corpus Manager.
          </div>
        )}

        {error && <div className="eval-error">❌ {error}</div>}

        {report && (
          <div className="eval-results animate-fade-in-up">
            {/* Summary metric cards */}
            <div className="eval-metrics">
              <div className="metric-card">
                <div className={`metric-value ${scoreColor(s.avg_rag_score)}`}>
                  {(s.avg_rag_score * 100).toFixed(1)}%
                </div>
                <div className="metric-label">RAG Score</div>
                <div className="metric-bar">
                  <div className="metric-fill rag" style={{ width: `${s.avg_rag_score * 100}%` }} />
                </div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${scoreColor(s.avg_context_relevance)}`}>
                  {(s.avg_context_relevance * 100).toFixed(1)}%
                </div>
                <div className="metric-label">Context Relevance</div>
                <div className="metric-bar">
                  <div className="metric-fill ctx" style={{ width: `${s.avg_context_relevance * 100}%` }} />
                </div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${scoreColor(s.avg_faithfulness)}`}>
                  {(s.avg_faithfulness * 100).toFixed(1)}%
                </div>
                <div className="metric-label">Faithfulness</div>
                <div className="metric-bar">
                  <div className="metric-fill faith" style={{ width: `${s.avg_faithfulness * 100}%` }} />
                </div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${scoreColor(s.avg_answer_relevance)}`}>
                  {(s.avg_answer_relevance * 100).toFixed(1)}%
                </div>
                <div className="metric-label">Answer Relevance</div>
                <div className="metric-bar">
                  <div className="metric-fill rel" style={{ width: `${s.avg_answer_relevance * 100}%` }} />
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-value gradient-text">
                  {s.total_questions}
                </div>
                <div className="metric-label">Questions Tested</div>
              </div>
            </div>

            {/* Per-question table */}
            <div className="eval-table-wrap">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Question</th>
                    <th>Ctx Rel</th>
                    <th>Faithful</th>
                    <th>Ans Rel</th>
                    <th>RAG Score</th>
                    <th>Reasoning</th>
                  </tr>
                </thead>
                <tbody>
                  {report.records.map((r) => (
                    <tr key={r.question_id}>
                      <td><span className="badge badge-purple">{r.question_id}</span></td>
                      <td className="q-cell">{r.question}</td>
                      <td><ScoreCell val={r.context_relevance_score} /></td>
                      <td><ScoreCell val={r.faithfulness_score} /></td>
                      <td><ScoreCell val={r.answer_relevance_score} /></td>
                      <td><ScoreCell val={r.rag_score} bold /></td>
                      <td className="reasoning-cell">{r.judge_reasoning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="eval-footer">
              Evaluated at {report.evaluated_at} · LLM-as-Judge via Groq (Llama 3) · RAG Triad methodology
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreCell({ val, bold }) {
  const pct = (val * 100).toFixed(0);
  const cls = val >= 0.8 ? "badge-green" : val >= 0.6 ? "badge-amber" : "badge-red";
  return (
    <span className={`badge ${cls}`} style={bold ? { fontWeight: 700, fontSize: "0.9em" } : {}}>
      {pct}%
    </span>
  );
}
