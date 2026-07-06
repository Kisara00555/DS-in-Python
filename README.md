# 🚀 AI Startup Funding & Investment Intelligence Assistant

**DS205.3 – Data Science with Python | Coursework**

A production-grade **Retrieval-Augmented Generation (RAG)** system that lets you query a private corpus of AI startup funding and venture capital documents using natural language.

> 📦 **GitHub Repository:** https://github.com/Kisara00555/DS-in-Python

---

## 📐 Architecture

```
data/pdfs/
    └── [your PDFs]
         │
         ▼
┌─────────────────────────┐
│  PyMuPDFLoader          │  ← ingestion/pdf_loader.py
│  (page-level extraction)│
└────────────┬────────────┘
             │ DocumentPage[]
             ▼
┌─────────────────────────┐
│  SlidingWindowChunker   │  ← ingestion/chunker.py
│  (size=800, overlap=150)│
└────────────┬────────────┘
             │ TextChunk[]
             ▼
┌─────────────────────────┐
│  LocalEmbedder          │  ← vectorstore/embedder.py
│  (all-MiniLM-L6-v2)    │
└────────────┬────────────┘
             │ float[][] (vectors)
             ▼
┌─────────────────────────┐
│  ChromaVectorStore      │  ← vectorstore/store.py
│  (persistent, on disk)  │
└────────────┬────────────┘

User Query
    │
    ▼
┌─────────────────────────┐
│  Retriever              │  ← agent/retriever.py
│  (query expansion + k-NN│
│   search + dedup)       │
└────────────┬────────────┘
             │ RetrievalTrace (chunks + metadata)
             ▼
┌─────────────────────────┐
│  Generator              │  ← agent/generator.py
│  (Gemini + history)     │
└────────────┬────────────┘
             │
             ▼
        Grounded Answer
             │
             ▼
┌─────────────────────────┐
│  Evaluator              │  ← evaluation/evaluator.py
│  (RAG Triad scoring)    │
└─────────────────────────┘
```

---

## 🗂️ Project Structure

```
ai_funding_rag/                  # Main Python package
├── config/
│   ├── __init__.py
│   └── settings.py              # All config via .env + dataclass DI
├── ingestion/
│   ├── __init__.py
│   ├── pdf_loader.py            # PyMuPDF loader (BaseLoader ABC)
│   └── chunker.py               # Sliding-window chunker (BaseChunker ABC)
├── vectorstore/
│   ├── __init__.py
│   ├── embedder.py              # Local + Gemini embedder (BaseEmbedder ABC)
│   └── store.py                 # ChromaDB persistent store (BaseVectorStore ABC)
├── agent/
│   ├── __init__.py
│   ├── prompts.py               # All LLM prompt templates
│   ├── retriever.py             # Query expansion + retrieval + traceability
│   ├── generator.py             # ChatCompletion with history
│   └── rag_agent.py             # Agentic loop orchestrator
└── evaluation/
    ├── __init__.py
    └── evaluator.py             # RAG Triad evaluation framework

data/
├── pdfs/                        # ← PUT YOUR PDFs HERE
├── vector_store/                # ChromaDB files (auto-created)
└── evaluation/
    ├── ground_truth.json        # 15 QA pairs
    ├── results.json             # Evaluation output (auto-created)
    └── report.html              # Visual HTML report (auto-created)

api/
└── server.py                    # FastAPI backend for the React UI

ui/                              # React + Vite frontend
├── src/
├── index.html
└── package.json

ingest.py                        # CLI: ingest PDFs into vector store
chat.py                          # CLI: interactive Q&A session
evaluate.py                      # CLI: run RAG Triad evaluation suite
start_app.py                     # Launch API + UI together
```

---

## ⚡ Quick Start

### 1. Clone & set up environment

```bash
git clone <your-repo-url>
cd "DS Coursework"

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` and set your `GOOGLE_API_KEY`.

### 3. Add your PDFs

Place your AI funding / venture capital PDF documents in:
```
data/pdfs/
```

Suggested sources:
- KPMG / PwC / CB Insights Venture Pulse reports
- Crunchbase Global Startup Funding reports
- a16z / Sequoia published investment theses
- State of AI reports (Air Street Capital)

### 4. Ingest

```bash
python ingest.py --source ./data/pdfs
```

### 5. Chat

```bash
python chat.py
```

### 6. Evaluate (RAG Triad)

```bash
python evaluate.py
```

Opens `data/evaluation/report.html` in your browser for a visual results table.

---

## 🔧 Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| PDF Extraction | PyMuPDF | Fastest, best fidelity, handles tables |
| Chunking | Sliding window (800/150) | Balances context vs. retrieval precision |
| Embedding Model | all-MiniLM-L6-v2 (local) | No API quota, fast, offline |
| Vector Store | ChromaDB (persistent) | Local, no cloud dependency, HNSW index |
| LLM | Gemini 2.0 Flash | Low latency, strong instruction following |
| Query Expansion | LLM-generated sub-queries | Improves recall for complex questions |
| Evaluation | RAG Triad (LLM-as-judge) | Industry-standard 3-dimensional scoring |

---

## 📊 RAG Triad Evaluation

The system is evaluated using the **RAG Triad** framework (TruEra), which measures three orthogonal dimensions of RAG quality:

| Dimension | What it measures | Failure mode detected |
|---|---|---|
| **Context Relevance** | Were the retrieved chunks relevant to the question? | Poor retrieval / embeddings |
| **Faithfulness** | Is the answer grounded in the retrieved context? | Hallucination |
| **Answer Relevance** | Does the answer address the question? | Off-topic responses |

The **aggregate RAG Score** is the harmonic mean of all three, which ensures a single weak leg drags down the overall score.

The evaluation runs against **15 domain-specific ground-truth QA pairs** covering:
- Funding stages & instruments (SAFE, term sheets)
- Valuation mechanics (pre/post-money, dilution)
- VC decision criteria
- AI startup ecosystem (unicorns, accelerators)
- Exit strategies

### Outputs

| File | Contents |
|---|---|
| `data/evaluation/results.json` | Machine-readable scores for all 15 QA pairs |
| `data/evaluation/report.html` | Visual HTML report with colour-coded score badges |

Run: `python evaluate.py`

---

## 📋 Requirements

- Python 3.10+
- Google AI Studio API key (`GOOGLE_API_KEY`) — free at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- ~200MB disk for ChromaDB + sentence-transformer model cache

---

## 👥 Authors

DS205.3 Group – Faculty of Computing
- Kisara00555 – Data Ingestion & Chunking Pipeline
- Dilusha – RAG Agent & FastAPI Backend
- Savindi – Evaluation Framework & Ground Truth
- Tharusha – React UI, Report & Documentation

## AI Usage Disclosure
In accordance with coursework guidelines, we acknowledge the use of AI (Google Gemini) during this project as a pair-programming assistant.
- **Code Generation:** AI was used to assist with boilerplate React component generation and regex parsing.
- **Debugging:** Used for troubleshooting dependency conflicts in `PyMuPDF` and `ChromaDB`.
- **Architectural Planning:** AI assisted in brainstorming the RAG Triad evaluation strategy.
All core logic, integration, and final code reviews were manually conducted by the team.

