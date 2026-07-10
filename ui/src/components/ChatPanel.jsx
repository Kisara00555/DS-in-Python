import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import MessageBubble from "./MessageBubble";
import TracePanel from "./TracePanel";
import "./ChatPanel.css";

const SUGGESTIONS = [
  "What are the typical stages of startup funding?",
  "How does equity dilution work across rounds?",
  "What is a SAFE note and how does it work?",
  "What factors do VCs look for in AI startups?",
  "Explain pre-money vs post-money valuation",
  "What is a unicorn company?",
];

export default function ChatPanel({ messages, setMessages, loading, setLoading, status }) {
  const [input, setInput] = useState("");
  const [showTrace, setShowTrace] = useState(true);
  const [topK, setTopK] = useState(5);
  const [lastTrace, setLastTrace] = useState(null);
  const [traceOpen, setTraceOpen] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const q = text || input.trim();
    if (!q || loading) return;
    setInput("");

    const userMsg = { role: "user", content: q, timestamp: new Date() }; 
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await api.chat({ question: q, top_k: topK, show_trace: true });
      setLastTrace({
        expandedQueries: data.expanded_queries,
        chunks: data.retrieved_chunks,
      });
      const assistantMsg = {
        role: "assistant",
        content: data.answer,
        timestamp: new Date(),
        meta: { 
          model: data.model,
          inputTokens: data.input_tokens,
          outputTokens: data.output_tokens,
          chunkCount: data.retrieved_chunks.length,
        },
      };
      setMessages((prev) => [...prev, assistantMsg]);
      if (showTrace) setTraceOpen(true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: `❌ Error: ${err.message}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleReset = async () => {
    try {
      await api.resetConversation();
      setMessages([
        {
          role: "assistant", 
          content: "🔄 Conversation history cleared. Ask me anything!",
          timestamp: new Date(),
        },
      ]);
      setLastTrace(null);
      setTraceOpen(false);
    } catch {}
  };

  const notReady = !status?.ready;

  return (
    <div className="chat-panel">
      {/* Messages area */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {loading && (
          <div className="chat-thinking animate-fade-in">
            <div className="thinking-avatar">🤖</div>
            <div className="thinking-dots">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && !loading && (
        <div className="suggestions animate-fade-in-up">
          <span className="suggestions-label">Try asking:</span>
          <div className="suggestions-grid">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                id={`suggestion-${i}`}
                className="suggestion-chip"
                onClick={() => sendMessage(s)}
                disabled={notReady}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Trace panel */}
      {lastTrace && (
        <TracePanel
          trace={lastTrace}
          open={traceOpen}
          onToggle={() => setTraceOpen(!traceOpen)}
        />
      )}

      {/* Input bar */}
      <div className="chat-input-area">
        <div className="chat-input-toolbar">
          <div className="toolbar-left">
            <label className="toolbar-toggle">
              <input
                type="checkbox"
                checked={showTrace} 
                onChange={(e) => setShowTrace(e.target.checked)} 
                id="toggle-trace"
              />
              <span>Show retrieval trace</span>
            </label>
            <div className="toolbar-topk">
              <span>Top K:</span>
              <select
                id="select-topk"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="topk-select"
              >
                {[3, 5, 7, 10].map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
            </div>
          </div>
          <button id="btn-reset-conversation" className="btn btn-ghost" onClick={handleReset} title="Clear history">
            🗑️ Clear
          </button>
        </div>

        <div className="chat-input-box">
          <textarea
            ref={textareaRef}
            id="chat-input"
            className="chat-textarea"
            placeholder={
              notReady
                ? "⚠️ Ingest PDFs first in Corpus Manager..."
                : "Ask about AI startup funding, venture capital, valuations..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || notReady}
            rows={2}
            autoFocus
          />
          <button
            id="btn-send"
            className="btn btn-primary send-btn"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim() || notReady}
          >
            {loading ? <span className="spinner" /> : "↑"}
          </button>
        </div>
        <p className="chat-hint">Enter to send • Shift+Enter for new line</p>
      </div>
    </div>
  );
}
