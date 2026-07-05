import { useState } from "react";
import "./TracePanel.css";

export default function TracePanel({ trace, open, onToggle }) {
  const [expandedChunk, setExpandedChunk] = useState(null);
  const { expandedQueries, chunks } = trace;

  return (
    <div className={`trace-panel ${open ? "open" : ""}`}>
      <button
        id="btn-toggle-trace"
        className="trace-toggle"
        onClick={onToggle}
      >
        <span className="trace-toggle-icon">📡</span>
        <span>
          Retrieval Trace — {chunks.length} chunks retrieved
        </span>
        <span className="trace-toggle-chevron">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="trace-body animate-fade-in">
          {/* Expanded queries */}
          {expandedQueries.length > 1 && (
            <div className="trace-queries">
              <span className="trace-section-label">🔍 Query Expansion</span>
              <div className="trace-query-list">
                {expandedQueries.map((q, i) => (
                  <div key={i} className={`trace-query ${i === 0 ? "original" : "expanded"}`}>
                    <span className="badge badge-blue">{i === 0 ? "original" : `exp ${i}`}</span>
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chunks */}
          <div className="trace-chunks">
            <span className="trace-section-label">📄 Retrieved Chunks</span>
            <div className="chunk-list">
              {chunks.map((chunk, i) => (
                <div
                  key={chunk.chunk_id}
                  id={`chunk-${i}`}
                  className={`chunk-card ${expandedChunk === i ? "expanded" : ""}`}
                  onClick={() => setExpandedChunk(expandedChunk === i ? null : i)}
                >
                  <div className="chunk-header">
                    <div className="chunk-meta">
                      <span className="badge badge-purple">#{i + 1}</span>
                      <span className="chunk-source">{chunk.source}</span>
                      <span className="badge badge-blue">p.{chunk.page}</span>
                    </div>
                    <div className="chunk-sim">
                      <div className="sim-bar">
                        <div
                          className="sim-fill"
                          style={{ width: `${Math.max(chunk.similarity * 100, 5)}%` }}
                        />
                      </div>
                      <span className="mono sim-score">{(chunk.similarity * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <p className="chunk-preview">
                    {expandedChunk === i
                      ? chunk.text
                      : chunk.text.slice(0, 150) + (chunk.text.length > 150 ? "…" : "")}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
