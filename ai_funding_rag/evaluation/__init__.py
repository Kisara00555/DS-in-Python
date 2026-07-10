"""Evaluation framework — RAG Triad scoring with LLM-as-judge."""

from .evaluator import Evaluator, EvaluationReport, EvaluationRecord, GroundTruthItem

__all__ = ["Evaluator", "EvaluationReport", "EvaluationRecord", "GroundTruthItem"]
