import "./AboutPanel.css";

const TEAM = [
  { name: "Kisara00555", role: "Member 1 – Data Ingestion & Chunking Pipeline" },
  { name: "Dilusha", role: "Member 2 – RAG Agent & FastAPI Backend" },
  { name: "Savindi", role: "Member 3 – Evaluation Framework & Ground Truth" },
  { name: "[Member 4 Name]", role: "Member 4 – React UI, Report & Documentation" },
];

export default function AboutPanel() {
  return (
    <div className="about-panel">
      <div className="about-content">
        <h2 className="panel-heading">ℹ️ About</h2>

        {/* Project description */}
        <div className="about-card glass animate-fade-in-up">
          <div className="about-card-icon">🚀</div>
          <div>
            <h3>AI Startup Funding &amp; Investment Intelligence Assistant</h3>
            <p className="about-description">
              A production-grade <strong>Retrieval-Augmented Generation (RAG)</strong> system
              that lets you query a private corpus of AI startup funding and venture capital
              documents using natural language. Built for <strong>DS205.3 – Data Science with
              Python</strong> coursework.
            </p>
          </div>
        </div>

        {/* Module info */}
        <div className="about-meta-row animate-fade-in-up">
          <div className="about-meta-card glass">
            <span className="about-meta-label">Module</span>
            <span className="about-meta-value">DS205.3</span>
          </div>
          <div className="about-meta-card glass">
            <span className="about-meta-label">System</span>
            <span className="about-meta-value">RAG + LLM-as-Judge</span>
          </div>
          <div className="about-meta-card glass">
            <span className="about-meta-label">LLM</span>
            <span className="about-meta-value">Gemini 2.0 Flash</span>
          </div>
          <div className="about-meta-card glass">
            <span className="about-meta-label">Vector DB</span>
            <span className="about-meta-value">ChromaDB</span>
          </div>
        </div>

        {/* Team */}
        <h3 className="about-section-title animate-fade-in-up">👥 Team</h3>
        <div className="about-team animate-fade-in-up">
          {TEAM.map((member, i) => (
            <div key={i} className="about-member glass">
              <div className="about-member-avatar">{member.name[0]}</div>
              <div className="about-member-info">
                <strong>{member.name}</strong>
                <span>{member.role}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Tech stack */}
        <h3 className="about-section-title animate-fade-in-up">🛠️ Technology Stack</h3>
        <div className="about-stack animate-fade-in-up">
          {[
            { label: "PDF Loader", value: "PyMuPDF" },
            { label: "Chunking", value: "Sliding Window (800/150)" },
            { label: "Embeddings", value: "all-MiniLM-L6-v2 (local)" },
            { label: "Vector Store", value: "ChromaDB (persistent)" },
            { label: "LLM", value: "Gemini 2.0 Flash" },
            { label: "Evaluation", value: "RAG Triad (TruEra)" },
            { label: "Backend", value: "FastAPI" },
            { label: "Frontend", value: "React + Vite" },
          ].map((item, i) => (
            <div key={i} className="about-stack-item glass">
              <span className="about-stack-label">{item.label}</span>
              <span className="about-stack-value">{item.value}</span>
            </div>
          ))}
        </div>

        {/* GitHub link */}
        <div className="about-footer animate-fade-in-up">
          <a
            href="https://github.com/Kisara00555/DS-in-Python"
            target="_blank"
            rel="noreferrer"
            className="btn btn-primary"
            id="btn-github-link"
          >
            🔗 View on GitHub
          </a>
        </div>
      </div>
    </div>
  );
}
