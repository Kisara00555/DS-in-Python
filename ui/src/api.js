// src/api.js — Centralised API client
// Requests use relative paths — Vite dev server proxies them to localhost:8000
const BASE = "";

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body instanceof FormData) {
    opts.body = body;
  } else if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "API error");
  return data;
}

export const api = {
  status:           ()      => req("GET",  "/status"),
  corpusInfo:       ()      => req("GET",  "/corpus-info"),
  chat:             (body)  => req("POST", "/chat", body),
  resetConversation:()      => req("POST", "/reset-conversation"),
  ingest:           (body)  => req("POST", "/ingest", body),
  resetCorpus:      ()      => req("POST", "/reset-corpus"),
  runEvaluation:    ()      => req("POST", "/evaluate"),
  uploadPDF: async (file) => {
    const form = new FormData();
    form.append("file", file);
    return req("POST", "/upload-pdf", form);
  },
};
