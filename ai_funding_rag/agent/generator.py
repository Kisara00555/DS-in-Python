"""
agent/generator.py
------------------
LLM-based answer generator backed by Groq.
Receives formatted context + user question → produces a grounded response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from typing import List, Dict

import groq

from ..config.settings import Settings
from .prompts import RAG_PROMPT_TEMPLATE, SYSTEM_PROMPT
from .retriever import RetrievalTrace

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Full result including the answer and the trace.""" 

    question: str
    answer: str
    trace: RetrievalTrace
    model_used: str
    input_tokens: int
    output_tokens: int


class Generator: 
    """
    Wraps the Groq client to produce grounded answers.
    Maintains a conversation history for multi-turn interactions.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialise the Generator with a Groq client and empty history.

        Args:
            settings: Configuration object supplying the API key, model name,
                      and temperature for the generative model.
        """
        self._settings = settings
        self._client = groq.Groq(api_key=settings.groq_api_key)
        self._history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # ── public ───────────────────────────────────────────────────────────────

    def generate(self, trace: RetrievalTrace) -> GenerationResult:
        """Generate a grounded answer from the retrieval trace."""
        user_content = RAG_PROMPT_TEMPLATE.format(
            context=trace.context_text,
            question=trace.original_query,
        )

        # Build full contents list: history + current user message
        messages = self._history + [
            {"role": "user", "content": user_content}
        ]

        response = self._client.chat.completions.create(
            model=self._settings.llm_model,
            messages=messages,
            temperature=self._settings.llm_temperature,
        )

        answer = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0 
        output_tokens = response.usage.completion_tokens if response.usage else 0

        # Store compressed history (original question + answer only, not full context)
        self._history.append({"role": "user", "content": trace.original_query})
        self._history.append({"role": "assistant", "content": answer})

        # Keep history bounded to last 10 turns (20 messages) + 1 system prompt
        if len(self._history) > 21:
            self._history = [self._history[0]] + self._history[-20:]

        logger.info(
            "Generated answer: %d input tokens, %d output tokens",
            input_tokens,
            output_tokens,
        )

        return GenerationResult(
            question=trace.original_query,
            answer=answer,
            trace=trace,
            model_used=self._settings.llm_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ) 

    def reset_history(self) -> None:
        """Clear conversation history (start fresh session)."""
        self._history = [{"role": "system", "content": SYSTEM_PROMPT}]
        logger.info("Conversation history cleared.")


# The generator enforces strict adherence to context to avoid LLM hallucinations during response generation.
