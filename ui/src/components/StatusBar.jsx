import "./StatusBar.css";

export default function StatusBar({ status, onRefresh, modelName }) {
  const ready = status?.ready;
  const corpusSize = status?.corpus_size ?? 0;

  return (
    <header className="status-bar">
      <div className="status-bar-left">
        <h2 className="status-bar-title gradient-text">
          AI Startup Funding &amp; Investment Intelligence
        </h2>
        <span className="status-bar-sub">RAG-powered knowledge assistant</span>
      </div>
      <div className="status-bar-right">
        {status && (
          <>
            <div className={`status-chip ${ready ? "ready" : "not-ready"}`}>
              <span className="status-chip-dot" />
              {ready ? `${corpusSize} chunks indexed` : "Not ready"}
            </div>
            <span className="status-bar-model mono">✨ {modelName || "Gemini"}</span>
          </>
        )}
        <button id="btn-refresh-status" className="btn btn-ghost" onClick={onRefresh} title="Refresh status">
          🔄
        </button>
      </div>
    </header>
  );
}
