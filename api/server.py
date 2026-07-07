"""
api/server.py
-------------
FastAPI backend that exposes the RAG agent via REST endpoints.
The React frontend communicates exclusively through this API.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_funding_rag.config.settings import default_settings
from ai_funding_rag.agent.rag_agent import RAGAgent
from ai_funding_rag.evaluation.evaluator import Evaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.server")

# ── App init ─────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm the RAG agent at startup so /status is correct immediately."""
    try:
        logger.info("Pre-warming RAG agent…")
        agent = get_agent()
        logger.info("RAG agent ready — %d chunks in corpus", agent.corpus_size)
    except Exception as exc:
        logger.warning("Agent pre-warm failed (will retry on first request): %s", exc)
    yield  # server runs here


app = FastAPI(
    title="AI Startup Funding RAG API",
    description="Backend API for the AI Startup Funding & Investment Intelligence Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton agent ───────────────────────────────────────────────────────────

_agent: Optional[RAGAgent] = None
_evaluator: Optional[Evaluator] = None
_ingestion_status: dict = {"running": False, "message": "", "chunks": 0}


def get_agent() -> RAGAgent:
    global _agent
    if _agent is None:
        settings = default_settings
        settings.validate()
        _agent = RAGAgent(settings=settings)
    return _agent


def get_evaluator() -> Evaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator(settings=default_settings)
    return _evaluator


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = None
    show_trace: bool = True


class ChatChunk(BaseModel):
    chunk_id: str
    source: str
    page: int
    similarity: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    model: str
    input_tokens: int
    output_tokens: int
    expanded_queries: List[str]
    retrieved_chunks: List[ChatChunk]


class StatusResponse(BaseModel):
    corpus_size: int
    api_key_set: bool
    ready: bool


class IngestRequest(BaseModel):
    source_path: str = "./data/pdfs"
    force: bool = False


class IngestResponse(BaseModel):
    chunks_added: int
    total_corpus_size: int
    message: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_model=dict)
def root():
    return {"message": "AI Startup Funding RAG API is running ✅"}


@app.get("/health", response_model=dict)
def health():
    """Health check endpoint — returns service status, version, and active model."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "model": default_settings.llm_model,
    }


@app.get("/status", response_model=StatusResponse)
def get_status():
    """Check if the system is ready."""
    settings = default_settings
    api_key_set = bool(settings.google_api_key)
    corpus_size = 0
    if api_key_set:
        try:
            agent = get_agent()
            corpus_size = agent.corpus_size
        except Exception:
            pass
    return StatusResponse(
        corpus_size=corpus_size,
        api_key_set=api_key_set,
        ready=api_key_set and corpus_size > 0,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a question and get a grounded answer."""
    try:
        agent = get_agent()
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if agent.corpus_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Vector store is empty. Please ingest PDFs first.",
        )

    try:
        result = agent.ask(
            question=req.question,
            top_k=req.top_k,
            show_trace=False,  # UI handles trace display
        )
    except Exception as e:
        logger.exception("Error during agent.ask(): %s", e)
        return JSONResponse(status_code=500, content={"detail": f"Agent error: {str(e)}"})

    chunks_out = [
        ChatChunk(
            chunk_id=c.chunk_id,
            source=c.metadata.get("filename", c.chunk_id),
            page=int(c.metadata.get("page_number", 0)),
            similarity=round(c.similarity, 4),
            text=c.text,
        )
        for c in result.trace.retrieved_chunks
    ]

    return ChatResponse(
        answer=result.answer,
        model=result.model_used,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        expanded_queries=result.trace.expanded_queries,
        retrieved_chunks=chunks_out,
    )


@app.post("/reset-conversation")
def reset_conversation():
    """Clear the agent's multi-turn conversation history."""
    try:
        get_agent().reset_conversation()
        return {"message": "Conversation history cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    """Ingest PDFs from a directory into the vector store."""
    source = Path(req.source_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {source}")
    try:
        agent = get_agent()
        count = agent.ingest(source=source, force=req.force)
        return IngestResponse(
            chunks_added=count,
            total_corpus_size=agent.corpus_size,
            message=f"Ingested {count} new chunks. Total: {agent.corpus_size}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a single PDF and ingest it immediately."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    upload_dir = Path("./data/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / file.filename

    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    try:
        agent = get_agent()
        count = agent.ingest(source=dest, force=True)
        return {
            "filename": file.filename,
            "chunks_added": count,
            "total_corpus_size": agent.corpus_size,
            "message": f"'{file.filename}' uploaded and ingested ({count} chunks).",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/corpus-info")
def corpus_info():
    """Return info about what's in the vector store."""
    try:
        agent = get_agent()
        return {
            "corpus_size": agent.corpus_size,
            "vector_store_path": str(default_settings.vector_store_path),
            "collection_name": default_settings.collection_name,
            "embedding_model": default_settings.embedding_model,
            "llm_model": default_settings.llm_model,
            "chunk_size": default_settings.chunk_size,
            "chunk_overlap": default_settings.chunk_overlap,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate")
def run_evaluation():
    """
    Run the full RAG Triad evaluation suite against the ground-truth dataset.
    Scores each question on:
      - context_relevance_score  (retrieved chunks relevant to the question?)
      - faithfulness_score       (answer grounded in context — no hallucination?)
      - answer_relevance_score   (answer addresses the question?)
      - rag_score                (harmonic mean of all three)
    Also writes data/evaluation/report.html as a visual proof report.
    """
    try:
        agent = get_agent()
        evaluator = get_evaluator()
        report = evaluator.run_full_evaluation(agent)
        return report.to_dict()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Ground truth file not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset-corpus")
def reset_corpus():
    """Clear all documents from the vector store."""
    try:
        from ai_funding_rag.vectorstore.store import ChromaVectorStore
        store = ChromaVectorStore(default_settings)
        store.reset()
        global _agent
        _agent = None   # Force re-init next request
        return {"message": "Corpus cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
