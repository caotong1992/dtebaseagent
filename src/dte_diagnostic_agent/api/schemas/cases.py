"""Case management schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CaseSearchItem(BaseModel):
    """Item in case search results."""

    case_id: str = Field(description="Case ID")
    title: str = Field(description="Case title")
    symptoms: list[str] = Field(description="List of symptoms")
    problem: str = Field(description="Problem description")
    solution_summary: str = Field(description="Solution summary")
    similarity: float = Field(description="Similarity score", ge=0, le=1)
    created_at: datetime = Field(description="Creation timestamp")


class CaseSearchResponse(BaseModel):
    """Response for case search."""

    total: int = Field(description="Total count")
    items: list[CaseSearchItem] = Field(description="Search results")


class CaseCreateRequest(BaseModel):
    """Request to create a case from diagnosis."""

    session_id: str = Field(description="Diagnostic session ID")
    title: str = Field(description="Case title")
    tags: list[str] | None = Field(default=None, description="Tags for categorization")


class CaseCreateResponse(BaseModel):
    """Response for case creation."""

    case_id: str = Field(description="Created case ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class CaseSolution(BaseModel):
    """Solution for a case."""

    description: str = Field(description="Solution description")
    steps: list[str] = Field(description="Implementation steps")


class CaseMetadata(BaseModel):
    """Metadata for a case."""

    cluster: str | None = Field(default=None, description="Cluster name")
    service: str | None = Field(default=None, description="Service name")
    created_at: datetime = Field(description="Creation timestamp")


class CaseDetail(BaseModel):
    """Detailed case information."""

    case_id: str = Field(description="Case ID")
    title: str = Field(description="Case title")
    symptoms: list[str] = Field(description="List of symptoms")
    problem: str = Field(description="Problem description")
    solution: CaseSolution = Field(description="Solution details")
    metadata: CaseMetadata = Field(description="Case metadata")