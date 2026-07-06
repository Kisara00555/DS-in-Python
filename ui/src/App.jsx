import { useState, useEffect, useRef } from "react";
import { api } from "./api";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import CorpusPanel from "./components/CorpusPanel";
import EvalPanel from "./components/EvalPanel";
import AboutPanel from "./components/AboutPanel";
import StatusBar from "./components/StatusBar";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("chat");
  const [status, setStatus] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 Hello! I'm your **AI Startup Funding & Investment Intelligence Assistant**.\n\nI can answer questions about venture capital, startup funding rounds, valuations, term sheets, AI unicorns, and the broader investment ecosystem — all grounded in your private corpus.\n\nAsk me anything!",
      timestamp: new Date(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [modelName, setModelName] = useState("");

  const pollStatus = async () => {
    try {
      const s = await api.status();
      setStatus(s);
    } catch {
      setStatus(null);
    }
  };

  const fetchModelName = async () => {
    try {
      const info = await api.corpusInfo();
      setModelName(info.llm_model || "");
    } catch {
      // backend not yet ready — keep previous value
    }
  };

  useEffect(() => {
    pollStatus();
    fetchModelName();
    const id = setInterval(pollStatus, 8000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="app-shell">
      {/* Ambient background orbs */}
      <div className="ambient">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <Sidebar tab={tab} setTab={setTab} status={status} />

      <main className="main-content">
        <StatusBar status={status} onRefresh={pollStatus} modelName={modelName} />

        <div className="panel-container">
          {tab === "chat" && (
            <ChatPanel
              messages={messages}
              setMessages={setMessages}
              loading={loading}
              setLoading={setLoading}
              status={status}
            />
          )}
          {tab === "corpus" && (
            <CorpusPanel status={status} onRefresh={pollStatus} />
          )}
          {tab === "eval" && <EvalPanel status={status} />}
          {tab === "about" && <AboutPanel />}
        </div>
      </main>
    </div>
  );
}
