"""RAG agent — retriever, generator, prompt templates, and agentic loop orchestrator."""

from .rag_agent import RAGAgent
from .generator import GenerationResult, Generator
from .retriever import Retriever, RetrievalTrace
from .prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE

__all__ = [
    "RAGAgent", "GenerationResult", "Generator",
    "Retriever", "RetrievalTrace",
    "SYSTEM_PROMPT", "RAG_PROMPT_TEMPLATE",
]
