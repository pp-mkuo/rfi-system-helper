"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class SourceEntry(BaseModel):
    entry: int
    rerank_score: float
    vector_score: float
    question: str
    stack_name: str
    last_updated: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceEntry]
    model: str
    timestamp: str


class IngestResponse(BaseModel):
    status: str
    vectors_upserted: int


class HealthResponse(BaseModel):
    status: str
    index: str
    vector_count: Optional[int] = None
