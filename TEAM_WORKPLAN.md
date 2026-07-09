# 👥 DS205.3 — Team Work Division Plan
## AI Startup Funding & Investment Intelligence Assistant

> **4 Members | 10-Day Sprint | GitHub Commit Plan**
> Share this file with your team. Each person follows their own section.

---

## ⚡ Quick Setup (ALL members must do this on Day 1)

```bash
# 1. Clone the ACTUAL repo
git clone https://github.com/Kisara00555/DS-in-Python
cd DS-in-Python

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in your .env
copy .env.example .env
# Open .env and paste your GROQ_API_KEY

# 5. Install frontend dependencies
cd ui && npm install && cd ..
```

> **Git workflow rule:** Each person works on their own branch, raises a pull request to `main`, and the team leader reviews and merges.
> Branch naming: `member1/ingestion`, `member2/agent-api`, `member3/evaluation`, `member4/ui-docs`

---

## 👤 MEMBER 1 — Data Ingestion & Chunking Pipeline

**Role:** You own how the system reads PDFs and splits them into chunks.
**Branch:** `member1/ingestion`

### Your Files (primary responsibility)

| File | What it does |
|------|-------------|
| `ai_funding_rag/ingestion/pdf_loader.py` | Loads raw PDFs using PyMuPDF |
| `ai_funding_rag/ingestion/chunker.py` | Splits text into overlapping chunks |
| `ai_funding_rag/ingestion/__init__.py` | Package exports |
| `ingest.py` | CLI script to run ingestion from terminal |
| `data/pdfs/` | The 4 PDFs that form the corpus |
| `data/evaluation/ground_truth.json` | 15 Q&A pairs used for evaluation |

### What you need to understand

1. **`PyMuPDFLoader`** - reads each PDF page by page. Falls back to block-mode for scanned PDFs.
2. **`SlidingWindowChunker`** - splits text using a sliding window (800 chars, 150 overlap). It is sentence-aware, it won't cut mid-sentence.
3. **`BaseLoader` and `BaseChunker`** - abstract base classes. Your code implements them. Do NOT delete the ABCs.

### 10-Day Commit Plan

| Day | Task | Git Commit Message |
|-----|------|--------------------|
| **Day 1** | Clone repo, install deps, run `python ingest.py` to verify it works | `feat(m1): initial setup - verified ingest pipeline runs` |
| **Day 2** | Read `pdf_loader.py` fully. Add a `__repr__` to the `Document` dataclass showing `source`, `page`, `char_count` | `feat(m1/loader): add Document.__repr__ with source, page, char_count` |
| **Day 3** | Add a page-count validator to `PyMuPDFLoader.load()` — if a PDF has 0 pages, raise a `ValueError` with a helpful message | `feat(m1/loader): add zero-page validation with ValueError` |
| **Day 4** | Read `chunker.py`. Add a minimum chunk length filter — skip any chunk shorter than 50 characters (avoids noise chunks) | `feat(m1/chunker): filter chunks shorter than 50 chars` |
| **Day 5** | Add a `chunk_count()` method to `SlidingWindowChunker` that returns the total number of chunks it would produce without storing them | `feat(m1/chunker): add chunk_count() preview method` |
| **Day 6** | Find 1 additional PDF about AI startup funding online (must be publicly available). Add it to `data/pdfs/` and run `ingest.py` | `data(m1): add [PDF name] to corpus, re-ingested` |
| **Day 7** | Add 5 more Q&A pairs to `data/evaluation/ground_truth.json` based on the new PDF. Keep the same JSON format. | `data(m1): add 5 new ground-truth QA pairs from [source]` |
| **Day 8** | Add logging to `pdf_loader.py` using Python's `logging` module — log each page loaded and any fallback-to-blocks events | `feat(m1/loader): add logging for page load and fallback events` |
| **Day 9** | Write a docstring for every public method in both `pdf_loader.py` and `chunker.py` (Args, Returns, Raises) | `docs(m1): add full docstrings to loader and chunker` |
| **Day 10** | Run the full system with `python start_app.py`, take a screenshot of the running UI. Write a 1-paragraph comment in `ingest.py` explaining the pipeline | `docs(m1): pipeline explanation comment + verified full system run` |

### Definition of Done

- [ ] `python ingest.py` runs without errors
- [ ] At least 5 PDFs in `data/pdfs/`
- [ ] At least 12 Q&A pairs in `ground_truth.json`
- [ ] All methods have docstrings
- [ ] No chunk shorter than 50 chars is stored
- [ ] Zero-page PDF raises `ValueError`

---

## 👤 MEMBER 2 — RAG Agent & FastAPI Backend

**Role:** You own the brain of the system — the agent that retrieves context and generates answers — and the API that exposes it.
**Branch:** `member2/agent-api`

### Your Files (primary responsibility)

| File | What it does |
|------|-------------|
| `ai_funding_rag/agent/rag_agent.py` | Orchestrator — chains retrieval → generation |
| `ai_funding_rag/agent/retriever.py` | Query expansion + vector search + dedup |
| `ai_funding_rag/agent/generator.py` | Calls Groq to generate the grounded answer |
| `ai_funding_rag/agent/prompts.py` | System prompt and judge prompt templates |
| `ai_funding_rag/agent/__init__.py` | Package exports |
| `api/server.py` | FastAPI app with all 8 HTTP endpoints |
| `chat.py` | CLI chat interface |
| `start_app.py` | Launcher that starts backend + frontend |

### What you need to understand

1. **`RAGAgent`** - takes a question, calls `Retriever.retrieve()`, then `Generator.generate()`. Maintains conversation history.
2. **`Retriever`** - uses LLM to expand the query into 3 sub-queries, searches each, deduplicates by `chunk_id`.
3. **`Generator`** - formats the retrieved chunks as context and calls Groq's `chat.completions.create()`.
4. **`server.py`** - FastAPI app. Every endpoint is documented with OpenAPI. Uses a global `RAGAgent` singleton.

### 10-Day Commit Plan

| Day | Task | Git Commit Message |
|-----|------|--------------------|
| **Day 1** | Clone repo. Run `python chat.py` and ask 3 questions. Screenshot the retrieval trace output. | `feat(m2): initial setup - verified CLI chat and trace` |
| **Day 2** | Read `rag_agent.py` fully. Add a `history_length` property that returns the number of turns in conversation history | `feat(m2/agent): add history_length property` |
| **Day 3** | Add a `clear_history()` method to `RAGAgent` that resets `self._history` to empty list | `feat(m2/agent): add clear_history() method` |
| **Day 4** | Read `retriever.py`. Add a retrieval timeout — if `_expand_query()` takes more than 10 seconds, fall back to the original query without expansion | `feat(m2/retriever): add 10s timeout fallback for query expansion` |
| **Day 5** | Read `prompts.py`. Add a `SYSTEM_PROMPT_STRICT` variant — an even stricter version that adds "Do NOT speculate under any circumstances" to the rules | `feat(m2/prompts): add SYSTEM_PROMPT_STRICT variant` |
| **Day 6** | In `generator.py`, log the exact number of input and output tokens used per call (Groq returns these in `response.usage`) | `feat(m2/generator): log token usage per call` |
| **Day 7** | In `server.py`, add a `GET /health` endpoint that returns `{"status": "ok", "version": "1.0.0", "model": settings.LLM_MODEL}` | `feat(m2/api): add GET /health endpoint` |
| **Day 8** | Add a request ID to every API response — generate a UUID in each endpoint and include it as `"request_id"` in the JSON | `feat(m2/api): add request_id UUID to all API responses` |
| **Day 9** | Write full docstrings for every public method in `rag_agent.py`, `retriever.py`, and `generator.py` | `docs(m2): full docstrings for agent, retriever, generator` |
| **Day 10** | Test all 8 API endpoints using the React UI. Fix any issues found and commit the fixes. | `fix(m2): verify all 8 endpoints via React UI, patch issues` |

### Definition of Done

- [ ] `python chat.py` works and shows retrieval trace
- [ ] `uvicorn api.server:app` starts without errors
- [ ] `GET /health` returns version and model name
- [ ] `clear_history()` method exists on `RAGAgent`
- [ ] All methods have docstrings
- [ ] Token counts logged per call

---

## 👤 MEMBER 3 — Evaluation Framework & Ground Truth

**Role:** You own the quality measurement of the system. You define how good the RAG is and you prove it with numbers. You are also responsible for the 5-Min Video Demonstration.
**Branch:** `member3/evaluation`

### Your Files (primary responsibility)

| File | What it does |
|------|-------------|
| `ai_funding_rag/evaluation/evaluator.py` | Full RAG Triad evaluator — LLM-as-judge |
| `ai_funding_rag/evaluation/__init__.py` | Package exports |
| `evaluate.py` | CLI script to run the evaluation suite |
| `data/evaluation/ground_truth.json` | The 15+ Q&A pairs (you will review and validate these) |
| `data/evaluation/results.json` | Auto-generated output (you will analyse this) |
| `data/evaluation/report.html` | HTML report (you will validate its accuracy) |

### What you need to understand

1. **RAG Triad (TruEra Framework)** — three metrics:
   - **Context Relevance**: Were the retrieved chunks useful for this question?
   - **Faithfulness**: Is the answer grounded in the context (no hallucinations)?
   - **Answer Relevance**: Does the answer actually address the question asked?
2. **`JUDGE_PROMPT`** — the evaluator sends question + context + answer to Groq and asks it to score 0.0 to 1.0 on all three dimensions.
3. **Harmonic mean** (`EvaluationRecord.rag_score`) — punishes any single dimension being low.
4. **`evaluate.py`** — reads `ground_truth.json`, calls the agent for each question, scores each answer, saves `results.json` and `report.html`.

### 10-Day Commit Plan

| Day | Task | Git Commit Message |
|-----|------|--------------------|
| **Day 1** | Clone repo. Run `python evaluate.py` and let it score all 15 Q&A pairs. Open `data/evaluation/report.html` and screenshot the scores. | `feat(m3): initial setup - ran full evaluation, saved baseline scores` |
| **Day 2** | Read `evaluator.py` fully. In `JUDGE_PROMPT`, add a 4th instruction that explicitly asks the judge to check if any factual claims in the answer are NOT in the context | `feat(m3/evaluator): strengthen judge prompt with factual grounding check` |
| **Day 3** | Add a `worst_questions()` method to the `EvaluationReport` dataclass — returns the 3 Q&A records with the lowest `rag_score` | `feat(m3/evaluator): add worst_questions() method to EvaluationReport` |
| **Day 4** | Add a `best_questions()` method — returns the 3 records with the highest `rag_score`. Print both in `evaluate.py` | `feat(m3/evaluator): add best_questions() + print in evaluate.py` |
| **Day 5** | Review all 15 Q&A pairs in `ground_truth.json`. Fix any that have vague questions. Add a `"source_pdf"` field to each pair indicating which PDF it tests. | `data(m3): audit and annotate all 15 ground truth QA pairs with source_pdf` |
| **Day 6** | Add a `pass_rate` property to `EvaluationReport` — returns the percentage of questions where `rag_score >= 0.75` | `feat(m3/evaluator): add pass_rate property (threshold=0.75)` |
| **Day 7** | In `evaluate.py`, add a `--question` CLI flag so you can evaluate a single question: `python evaluate.py --question "What is a SAFE note?"` | `feat(m3/cli): add --question flag for single-question evaluation` |
| **Day 8** | Run evaluation with the new PDFs Member 1 added. Analyse which questions score lowest and why. Write your analysis as a comment block in `evaluate.py` | `docs(m3): add score analysis comments for new corpus questions` |
| **Day 9** | Write full docstrings for every public class and method in `evaluator.py` | `docs(m3): full docstrings for entire evaluator module` |
| **Day 10** | Record the 5-minute video demo (screen recording). Upload to YouTube as Unlisted. Add the YouTube link to `README.md` and `REPORT.md`. | `docs(m3): add YouTube demo link to README and REPORT` |

### Definition of Done

- [ ] `python evaluate.py` runs end-to-end without errors
- [ ] `worst_questions()` and `best_questions()` methods exist
- [ ] `pass_rate` property exists on `EvaluationReport`
- [ ] `--question` flag works for single evaluation
- [ ] All Q&A pairs have a `"source_pdf"` field
- [ ] Final `results.json` and `report.html` committed
- [ ] All public methods have docstrings
- [ ] YouTube demo link is in both README and REPORT

---

## 👤 MEMBER 4 — React UI, Report & Documentation

**Role:** You own the user interface, the README, and the formal academic Technical Report. You are the face of the project.
**Branch:** `member4/ui-docs`

### Your Files (primary responsibility)

| File | What it does |
|------|-------------|
| `ui/src/components/ChatPanel.jsx` | Chat interface |
| `ui/src/components/EvalPanel.jsx` | Evaluation results panel |
| `ui/src/components/CorpusPanel.jsx` | Document upload/ingest panel |
| `ui/src/components/TracePanel.jsx` | Retrieval trace viewer |
| `ui/src/components/Sidebar.jsx` | Navigation sidebar |
| `ui/src/components/StatusBar.jsx` | Top status bar |
| `ui/src/api.js` | Frontend API client |
| `README.md` | Technical README for the repo |
| `REPORT.md` | 3,000-word formal academic report |

### What you need to understand

1. **React + Vite** — the UI is a single-page app. All components live in `ui/src/components/`.
2. **`api.js`** — the frontend speaks to FastAPI via a Vite proxy. No CORS issues, all 8 API routes are proxied.
3. **The 3 panels** — Chat (query), Corpus Manager (ingest PDFs), Evaluation (run RAG Triad).
4. **TracePanel** — shows query expansion + retrieved chunks with similarity scores. This is KEY for the Viva demo.
5. **README.md** — must include: GitHub URL, architecture diagram, setup instructions, technical decisions table.
6. **REPORT.md** — 3,000 words, 6 sections (see below).

### 10-Day Commit Plan

| Day | Task | Git Commit Message |
|-----|------|--------------------|
| **Day 1** | Clone repo. Run `python start_app.py` to launch the full system. Explore all 3 panels. Take screenshots. | `docs(m4): initial setup - captured screenshots of all 3 panels` |
| **Day 2** | In `Sidebar.jsx`, add a 4th nav item `{ id: "about", icon: "ℹ️", label: "About" }`. Create a simple `AboutPanel.jsx` that shows the team names, module, and project description. | `feat(m4/ui): add About panel with team info` |
| **Day 3** | In `App.jsx`, wire up the `AboutPanel` to the new `"about"` tab. Create `AboutPanel.css` with the same glass styling as other panels. | `feat(m4/ui): wire AboutPanel into tab routing with glass CSS` |
| **Day 4** | In `ChatPanel.jsx`, add a "Copy answer" button that appears on each assistant message bubble. Use `navigator.clipboard.writeText()`. | `feat(m4/ui): add copy-to-clipboard button on assistant messages` |
| **Day 5** | In `EvalPanel.jsx`, add a "Download JSON" button that saves the results to a `.json` file on the user's machine using a Blob + anchor trick. | `feat(m4/ui): add Download JSON button to EvalPanel` |
| **Day 6** | Update `README.md`: (a) Replace GitHub URL placeholder with actual URL, (b) Add team member names under `## Team`, (c) Add `## Screenshots` section with 2 embedded screenshots | `docs(m4): update README with team names, GitHub URL, screenshots` |
| **Day 7** | Write the first 3 sections of the academic report. Save as `REPORT.md`. Commit a first draft. | `docs(m4): first draft REPORT.md - sections I, II, III` |
| **Day 8** | Write sections IV, V, VI of the report. Use the actual evaluation scores from Member 3's `results.json`. | `docs(m4): complete REPORT.md - sections IV, V, VI with real scores` |
| **Day 9** | Final polish of the report: word count check (~3,000 words), fix grammar, add bibliography (cite the 4+ source PDFs). | `docs(m4): REPORT.md final polish, bibliography, word count confirmed` |
| **Day 10** | Finalize the academic report ensuring all technical details are accurately documented. | `docs(m4): final technical report completion` |

### Definition of Done

- [ ] `npm run dev` (inside `ui/`) opens a working UI
- [ ] About panel shows team member names
- [ ] Copy button works on chat messages
- [ ] Download JSON works in EvalPanel
- [ ] README has: actual GitHub URL, team names, screenshots
- [ ] `REPORT.md` is ~3,000 words with all 6 sections

---

## REPORT.md Structure (Member 4's main task)

```
# DS205.3 Coursework — Technical Report
## AI Startup Funding & Investment Intelligence Assistant
Group Members: [names] | Date: [date]

---

## I. Problem Statement (~500 words)
- Why do general-purpose LLMs fail at private VC/funding data?
- What gap does a RAG system fill?
- Why is hallucination especially dangerous in financial/investment contexts?

## II. System Architecture & Design (~600 words)
- Draw the data flow: PDF → Loader → Chunker → Embedder → ChromaDB → Retriever → Generator → Answer
- Explain why you chose the ABC + Dependency Injection pattern
- Justify: PyMuPDF over PDFMiner, SentenceTransformer over OpenAI embeddings, ChromaDB over Pinecone

## III. Implementation & Traceability (~600 words)
- Explain the agentic loop: query expansion → retrieval → dedup → generation
- Show an example: a question → the 5 retrieved chunks → the final answer
- Explain how the system avoids hallucination (system prompt rules)

## IV. Empirical Evaluation (~600 words)
- Describe the RAG Triad methodology (Context Relevance, Faithfulness, Answer Relevance)
- Include a table of all 15+ QA pairs with their scores (copy from results.json)
- Discuss: which questions scored lowest and why?
- Report the overall pass rate and average RAG Score

## V. Personal Reflection (~400 words)
- What was harder than expected?
- What would you do differently?
- How did OOP/ABCs make the project easier to extend?

## VI. Future Work (~300 words)
- Reflection/self-critique step in the agentic loop
- Multimodal ingestion (tables, charts from PDFs)
- Swapping ChromaDB for Pinecone for cloud scaling
- Fine-tuning the embedding model on VC-domain text
```

---

## Cross-Member Integration Points

These are the moments where your work touches someone else's. Communicate before Day 7.

| Handoff | From | To | What |
|---------|------|-----|------|
| New PDFs added to corpus | Member 1 | Member 3 | Member 3 must re-run evaluation after new PDFs are ingested |
| Q&A pairs expanded | Member 1 | Member 3 | Member 3 reviews and annotates the new pairs |
| `/health` endpoint added | Member 2 | Member 4 | Member 4 can add a version display in StatusBar |
| Final evaluation scores | Member 3 | Member 4 | Member 4 needs the `results.json` numbers for the report |
| Team names | Everyone | Member 4 | Tell Member 4 your full name for the About panel and report |

---

## Git Commit Rules (All Members)

1. **Commit every day** — even if it is small. The commit history is assessed.
2. **Use the commit message format** shown in your plan: `type(scope): description`
3. **Never push directly to `main`** — always use your branch and raise a pull request.
4. **Pull request title** should summarise all your changes.

### Commit Types Reference

| Type | Use for |
|------|---------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `docs` | Documentation or comments |
| `data` | Adding PDFs or Q&A pairs |
| `style` | UI or CSS changes |
| `refactor` | Code restructuring without changing behaviour |

---

## Final Submission Checklist (Team Leader verifies)

- [ ] GitHub repo is **public** and URL is in `README.md`
- [ ] Regular commits from all 4 members visible in history
- [ ] `python start_app.py` launches successfully from a fresh clone
- [ ] `python evaluate.py` runs and produces `results.json`
- [ ] `REPORT.md` is in the root at ~3,000 words
- [ ] YouTube demo link in `README.md`
- [ ] `.env.example` present (no real API key inside)
- [ ] `.env` is in `.gitignore` (NEVER commit your real key)
- [ ] `requirements.txt` is up to date
- [ ] All 4 branches merged into `main` before submission
