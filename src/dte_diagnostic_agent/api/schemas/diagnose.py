"""Diagnose request and response schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    """Time range for diagnosis."""

    start: str | None = Field(
        default=None,
        description="Start time in ISO8601 format, defaults to 1 hour ago",
    )
    end: str | None = Field(
        default=None,
        description="End time in ISO8601 format, defaults to now",
    )


class NodeInfo(BaseModel):
    """Node connection information."""

    host: str | None = Field(default=None, description="Node IP or hostname")
    port: int = Field(default=22, description="SSH port")
    username: str | None = Field(default=None, description="Login username")
    auth_type: str | None = Field(
        default=None,
        description="Authentication type: password/ssh_key",
    )
    password: str | None = Field(default=None, description="Password for authentication")
    ssh_key_path: str | None = Field(default=None, description="SSH private key path")


class Environment(BaseModel):
    """Environment information for diagnosis."""

    cluster_name: str = Field(description="Cluster name")
    node_info: NodeInfo | None = Field(default=None, description="Target node information")
    service_name: str = Field(
        default="DTEBaseService",
        description="Service name",
    )
    namespace: str | None = Field(default=None, description="Kubernetes namespace")


class DiagnoseOptions(BaseModel):
    """Diagnostic options."""

    timeout: int = Field(default=300, description="Timeout in seconds")
    dry_run: bool = Field(default=False, description="Only generate plan without execution")
    verbose: bool = Field(default=False, description="Verbose output")


class Priority(str, Enum):
    """Priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiagnoseRequest(BaseModel):
    """Diagnose request model."""

    description: str = Field(description="Problem description")
    time_range: TimeRange | None = Field(default=None, description="Time range")
    environment: Environment = Field(description="Environment information")
    symptoms: list[str] | None = Field(default=None, description="List of symptoms")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    options: DiagnoseOptions | None = Field(default=None, description="Diagnostic options")


class DiagnoseStatus(str, Enum):
    """Diagnostic session status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiagnoseCreateResponse(BaseModel):
    """Response for diagnose creation."""

    session_id: str = Field(description="Session ID")
    status: DiagnoseStatus = Field(description="Current status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    estimated_duration: int = Field(description="Estimated duration in seconds")


class DiagnoseProgress(BaseModel):
    """Progress information for running diagnosis."""

    current_step: str = Field(description="Current step name")
    completed_steps: list[str] = Field(description="Completed steps")
    remaining_steps: list[str] = Field(description="Remaining steps")
    percentage: int = Field(description="Progress percentage", ge=0, le=100)


class Hypothesis(BaseModel):
    """A diagnostic hypothesis."""

    id: str = Field(description="Hypothesis ID")
    problem: str = Field(description="Problem description")
    confidence: float = Field(description="Confidence score 0-1", ge=0, le=1)
    evidence: list[str] = Field(description="Supporting evidence")
    actions: list[str] = Field(description="Suggested actions")


class TopHypothesis(BaseModel):
    """Top hypothesis summary."""

    problem: str = Field(description="Problem description")
    confidence: float = Field(description="Confidence score", ge=0, le=1)


class RecommendedSolution(BaseModel):
    """Recommended solution."""

    description: str = Field(description="Solution description")
    steps: list[str] = Field(description="Implementation steps")
    confidence: float = Field(description="Confidence score", ge=0, le=1)


class SimilarCase(BaseModel):
    """Similar historical case."""

    case_id: str = Field(description="Case ID")
    title: str = Field(description="Case title")
    similarity: float = Field(description="Similarity score", ge=0, le=1)


class DiagnoseResult(BaseModel):
    """Complete diagnostic result."""

    session_id: str = Field(description="Session ID")
    status: DiagnoseStatus = Field(description="Current status")
    generated_at: datetime | None = Field(default=None, description="Result generation time")
    summary: str | None = Field(default=None, description="Problem summary")
    problem_category: str | None = Field(default=None, description="Problem category")
    severity: str | None = Field(default=None, description="Severity level")
    hypotheses: list[Hypothesis] | None = Field(default=None, description="Diagnostic hypotheses")
    top_hypothesis: TopHypothesis | None = Field(default=None, description="Top hypothesis")
    recommended_solutions: list[RecommendedSolution] | None = Field(
        default=None, description="Recommended solutions"
    )
    similar_cases: list[SimilarCase] | None = Field(default=None, description="Similar cases")
    next_steps: list[str] | None = Field(default=None, description="Next step recommendations")
    escalation_needed: bool = Field(default=False, description="Whether escalation is needed")
    progress: DiagnoseProgress | None = Field(default=None, description="Progress info if running")
    error: str | None = Field(default=None, description="Error message if failed")


class DiagnoseListItem(BaseModel):
    """Item in diagnose list."""

    session_id: str = Field(description="Session ID")
    description: str = Field(description="Problem description")
    cluster_name: str = Field(description="Cluster name")
    status: DiagnoseStatus = Field(description="Current status")
    created_at: datetime = Field(description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")


class DiagnoseListResponse(BaseModel):
    """Response for diagnose list."""

    total: int = Field(description="Total count")
    items: list[DiagnoseListItem] = Field(description="List items")
    pagination: Any = Field(description="Pagination info")


class DiagnoseCancelResponse(BaseModel):
    """Response for diagnose cancellation."""

    session_id: str = Field(description="Session ID")
    status: DiagnoseStatus = Field(description="Current status")
    cancelled_at: datetime = Field(default_factory=datetime.now, description="Cancellation timestamp")