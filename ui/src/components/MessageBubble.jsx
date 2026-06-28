import "./MessageBubble.css";

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Simple markdown-like renderer
function renderContent(text) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    // Bold **text**
    line = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Inline code `code`
    line = line.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Source citations [Source: ...]
    line = line.replace(/\[Source:([^\]]+)\]/g, '<span class="citation">[Source:$1]</span>');
    return <p key={i} dangerouslySetInnerHTML={{ __html: line || "&nbsp;" }} />;
  });
}

export default function MessageBubble({ message }) {
  const { role, content, timestamp, meta } = message;

  if (role === "user") {
    return (
      <div className="bubble-row bubble-user animate-fade-in-up">
        <div className="bubble bubble-user-inner">
          <p>{content}</p>
          <span className="bubble-time">{formatTime(timestamp)}</span>
        </div>
        <div className="bubble-avatar user-avatar">🧑</div>
      </div>
    );
  }

  if (role === "error") {
    return (
      <div className="bubble-row animate-fade-in-up">
        <div className="bubble bubble-error">
          <p>{content}</p>
        </div>
      </div>
    );
  }

  // Assistant
  return (
    <div className="bubble-row animate-fade-in-up">
      <div className="bubble-avatar bot-avatar">🤖</div>
      <div className="bubble bubble-assistant">
        <div className="bubble-content">{renderContent(content)}</div>
        {meta && (
          <div className="bubble-meta">
            <span className="badge badge-blue">{meta.model}</span>
            <span className="badge badge-purple">📡 {meta.chunkCount} chunks</span>
            <span className="bubble-tokens mono">
              {meta.inputTokens}↑ / {meta.outputTokens}↓ tokens
            </span>
            <span className="bubble-time">{formatTime(timestamp)}</span>
          </div>
        )}
        {!meta && (
          <span className="bubble-time" style={{ marginTop: 8, display: "block" }}>
            {formatTime(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}
