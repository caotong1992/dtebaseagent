"""Diagnostic report models."""

from datetime import datetime
from pydantic import BaseModel, Field

from dte_diagnostic_agent.agent.models.context import Severity, ProblemCategory
from dte_diagnostic_agent.agent.models.hypothesis import ValidatedHypothesis
from dte_diagnostic_agent.kb.models import Case


class Solution(BaseModel):
    description: str = Field(description="Solution description")
    steps: list[str] = Field(default_factory=list, description="Solution steps")
    based_on_case: str | None = Field(default=None, description="Based on case ID")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Solution confidence")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisites")
    risks: list[str] = Field(default_factory=list, description="Potential risks")


class DiagnosticReport(BaseModel):
    session_id: str = Field(description="Session ID")
    generated_at: datetime = Field(description="Report generation time")
    summary: str = Field(description="Problem summary")
    problem_category: ProblemCategory = Field(description="Problem category")
    severity: Severity = Field(description="Severity level")
    
    hypotheses: list[ValidatedHypothesis] = Field(default_factory=list, description="All hypotheses")
    top_hypothesis: ValidatedHypothesis | None = Field(default=None, description="Top hypothesis")
    
    similar_cases: list[Case] = Field(default_factory=list, description="Similar historical cases")
    recommended_solutions: list[Solution] = Field(default_factory=list, description="Recommended solutions")
    
    collected_evidence: dict[str, object] = Field(default_factory=dict, description="Collected evidence")
    diagnostic_steps: list[dict[str, object]] = Field(default_factory=list, description="Executed diagnostic steps")
    
    next_steps: list[str] = Field(default_factory=list, description="Next steps")
    escalation_needed: bool = Field(default=False, description="Whether escalation is needed")