"""
agent/generator.py
------------------
LLM-based answer generator backed by Google Gemini (AI Studio).
Receives formatted context + user question → produces a grounded response.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from google import genai
from google.genai import types as genai_types

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
    Wraps the Google Gemini GenerativeModel to produce grounded answers.
    Maintains a conversation history for multi-turn interactions.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialise the Generator with a Gemini client and empty history.

        Args:
            settings: Configuration object supplying the API key, model name,
                      and temperature for the generative model.
        """
        self._settings = settings
        self._client = genai.Client(api_key=settings.google_api_key)
        self._gen_config = genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=settings.llm_temperature,
        )
        self._history: List[genai_types.Content] = []

    # ── public ───────────────────────────────────────────────────────────────

    def generate(self, trace: RetrievalTrace) -> GenerationResult:
        """Generate a grounded answer from the retrieval trace."""
        user_content = RAG_PROMPT_TEMPLATE.format(
            context=trace.context_text,
            question=trace.original_query,
        )

        # Build full contents list: history + current user message
        contents = self._history + [
            genai_types.Content(role="user", parts=[genai_types.Part(text=user_content)])
        ]

        response = self._client.models.generate_content(
            model=self._settings.llm_model,
            contents=contents,
            config=self._gen_config,
        )

        answer = response.text or ""
        input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

        # Store compressed history (original question + answer only, not full context)
        self._history.append(genai_types.Content(role="user",  parts=[genai_types.Part(text=trace.original_query)]))
        self._history.append(genai_types.Content(role="model", parts=[genai_types.Part(text=answer)]))

        # Keep history bounded to last 10 turns (20 messages)
        if len(self._history) > 20:
            self._history = self._history[-20:]

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
        self._history.clear()
        logger.info("Conversation history cleared.")

