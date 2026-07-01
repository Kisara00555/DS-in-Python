import { useState, useCallback } from "react";
import { api } from "../api";
import "./CorpusPanel.css";

export default function CorpusPanel({ status, onRefresh }) {
  const [ingestPath, setIngestPath] = useState("./data/pdfs");
  const [force, setForce] = useState(false);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [log, setLog] = useState([]);
  const [dragOver, setDragOver] = useState(false);

  const addLog = (msg, type = "info") =>
    setLog((prev) => [...prev, { msg, type, time: new Date().toLocaleTimeString() }]);

  const handleIngest = async () => {
    setIngestLoading(true);
    try {
      const res = await api.ingest({ source_path: ingestPath, force });
      addLog(`✅ ${res.message}`, "success");
      onRefresh();
    } catch (err) {
      addLog(`❌ ${err.message}`, "error");
    } finally {
      setIngestLoading(false);
    }
  };

  const handleUpload = async (file) => {
    if (!file || !file.name.endsWith(".pdf")) {
      addLog("❌ Only PDF files are accepted.", "error");
      return;
    }
    setUploadLoading(true);
    try {
      const res = await api.uploadPDF(file);
      addLog(`✅ ${res.message}`, "success");
      onRefresh();
    } catch (err) {
      addLog(`❌ ${err.message}`, "error");
    } finally {
      setUploadLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm("⚠️ This will delete ALL indexed documents. Are you sure?")) return;
    setResetLoading(true);
    try {
      const res = await api.resetCorpus();
      addLog(`🗑️ ${res.message}`, "warning");
      onRefresh();
    } catch (err) {
      addLog(`❌ ${err.message}`, "error");
    } finally {
      setResetLoading(false);
    }
  };

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleUpload(file);
    },
    []
  );

  return (
    <div className="corpus-panel">
      <div className="corpus-content">
        <h2 className="panel-heading">📚 Corpus Manager</h2>
        <p className="panel-sub">Manage the documents indexed in your vector store.</p>

        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-value gradient-text">{status?.corpus_size ?? "—"}</div>
            <div className="stat-label">Total Chunks</div>
          </div>
          <div className="stat-card">
            <div className={`stat-value ${status?.api_key_set ? "text-green" : "text-red"}`}>
              {status?.api_key_set ? "✅ Set" : "❌ Missing"}
            </div>
            <div className="stat-label">Gemini API Key</div>
          </div>
          <div className="stat-card">
            <div className={`stat-value ${status?.ready ? "text-green" : "text-amber"}`}>
              {status?.ready ? "Ready" : "Not Ready"}
            </div>
            <div className="stat-label">System Status</div>
          </div>
        </div>

        <div className="corpus-grid">
          {/* Ingest from path */}
          <div className="corpus-card glass">
            <h3>📁 Ingest from Directory</h3>
            <p className="card-sub">Point to a folder of PDFs on your machine</p>
            <div className="form-group">
              <label>Source Path</label>
              <input
                id="input-ingest-path"
                type="text"
                className="text-input"
                value={ingestPath}
                onChange={(e) => setIngestPath(e.target.value)}
                placeholder="./data/pdfs"
              />
            </div>
            <label className="toggle-label">
              <input
                type="checkbox"
                id="toggle-force"
                checked={force}
                onChange={(e) => setForce(e.target.checked)}
              />
              Force re-ingest (overwrite existing)
            </label>
            <button
              id="btn-ingest"
              className="btn btn-primary"
              onClick={handleIngest}
              disabled={ingestLoading}
            >
              {ingestLoading ? <><span className="spinner" /> Ingesting…</> : "▶ Start Ingestion"}
            </button>
          </div>

          {/* Upload PDF */}
          <div className="corpus-card glass">
            <h3>⬆️ Upload a PDF</h3>
            <p className="card-sub">Drag & drop or click to upload a single PDF</p>
            <div
              id="drop-zone"
              className={`drop-zone ${dragOver ? "drag-over" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => document.getElementById("file-input").click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={(e) => handleUpload(e.target.files[0])}
              />
              {uploadLoading ? (
                <><span className="spinner" style={{ margin: "0 auto" }} /> <p>Uploading & ingesting…</p></>
              ) : (
                <>
                  <div className="drop-icon">📄</div>
                  <p>Drop PDF here or <span className="link">browse</span></p>
                  <p className="drop-hint">Ingested immediately into vector store</p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Reset */}
        <div className="danger-zone">
          <h3>⚠️ Danger Zone</h3>
          <div className="danger-row">
            <div>
              <strong>Reset Corpus</strong>
              <p>Delete all indexed documents from the vector store. Cannot be undone.</p>
            </div>
            <button
              id="btn-reset-corpus"
              className="btn btn-danger"
              onClick={handleReset}
              disabled={resetLoading}
            >
              {resetLoading ? <><span className="spinner" /> Resetting…</> : "🗑️ Reset Corpus"}
            </button>
          </div>
        </div>

        {/* Activity log */}
        {log.length > 0 && (
          <div className="activity-log">
            <div className="log-header">
              <span>Activity Log</span>
              <button className="btn btn-ghost" onClick={() => setLog([])} style={{ padding: "4px 8px", fontSize: 11 }}>Clear</button>
            </div>
            {log.map((entry, i) => (
              <div key={i} className={`log-entry log-${entry.type}`}>
                <span className="log-time mono">{entry.time}</span>
                <span>{entry.msg}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
