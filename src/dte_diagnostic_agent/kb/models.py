"""Knowledge base models."""

from datetime import datetime
from pydantic import BaseModel, Field


class Case(BaseModel):
    """Case data model."""
    
    case_id: str = Field(description="Unique case identifier")
    title: str = Field(description="Case title")
    category: str = Field(default="unknown", description="Case category")
    severity: str = Field(default="medium", description="Case severity: critical/high/medium/low")
    symptoms: list[str] = Field(default_factory=list, description="Symptom list")
    problem: str = Field(default="", description="Problem description")
    analysis: str = Field(default="", description="Analysis process")
    solution: list[str] = Field(default_factory=list, description="Solution steps")
    verification: str = Field(default="", description="Verification result")
    references: list[str] = Field(default_factory=list, description="Reference materials")
    related_cases: list[str] = Field(default_factory=list, description="Related case IDs")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update time")
    tags: list[str] = Field(default_factory=list, description="Tags")
    cluster: str | None = Field(default=None, description="Cluster name")
    service: str | None = Field(default=None, description="Service name")


class SearchResult(BaseModel):
    """Search result model."""
    
    case: Case = Field(description="Matched case")
    similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="Similarity score 0-1")
    match_reason: str = Field(default="", description="Match reason description")