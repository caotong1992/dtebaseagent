"""Hypothesis models."""

from pydantic import BaseModel, Field


class Hypothesis(BaseModel):
    id: str = Field(description="Hypothesis ID")
    problem: str = Field(description="Problem description")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0-1")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    actions: list[str] = Field(default_factory=list, description="Recommended actions")
    source: str = Field(default="llm", description="Hypothesis source: llm/rule/case")


class ValidatedHypothesis(BaseModel):
    hypothesis: Hypothesis = Field(description="The hypothesis")
    validation: dict[str, object] = Field(default_factory=dict, description="Validation details")
    confirmed: bool = Field(default=False, description="Whether hypothesis is confirmed")
    additional_evidence: list[str] = Field(default_factory=list, description="Additional evidence found")