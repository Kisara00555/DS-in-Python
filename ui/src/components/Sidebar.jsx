import "./Sidebar.css";

const NAV_ITEMS = [
  { id: "chat",   icon: "💬", label: "Chat" },
  { id: "corpus", icon: "📚", label: "Corpus Manager" },
  { id: "eval",   icon: "📊", label: "Evaluation" },
  { id: "about",  icon: "ℹ️", label: "About" },
];

function getSystemStatus(status) {
  if (!status) return { dot: "red", label: "Offline", sub: "API unreachable" };
  if (!status.api_key_set) return { dot: "red", label: "No API Key", sub: "Set GROQ_API_KEY" };
  if (!status.ready) return { dot: "amber", label: "Empty Corpus", sub: "Ingest PDFs first" };
  return { dot: "green", label: "Ready", sub: `${status.corpus_size} chunks` };
}

export default function Sidebar({ tab, setTab, status }) {
  const sys = getSystemStatus(status);

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🚀</div>
        <div className="sidebar-logo-text">
          <h1>AI Funding<br />Intelligence</h1>
          <span>DS205.3 RAG</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <span className="sidebar-label">Navigation</span>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            id={`nav-${item.id}`}
            className={`nav-item${tab === item.id ? " active" : ""}`}
            onClick={() => setTab(item.id)}
          >
            <span className="nav-item-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Footer status */}
      <div className="sidebar-footer">
        <div className="system-pill">
          <div className={`system-pill-dot ${sys.dot}`} />
          <div className="system-pill-info">
            <strong>{sys.label}</strong>
            <span>{sys.sub}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
