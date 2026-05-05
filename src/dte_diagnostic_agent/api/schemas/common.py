"""Common schemas for API responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""

    limit: int = Field(description="Number of items per page")
    offset: int = Field(description="Current offset")
    has_more: bool = Field(description="Whether more items are available")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class ComponentStatus(str, Enum):
    """Status of system components."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Overall health status: healthy/unhealthy")
    version: str = Field(description="Application version")
    components: dict[str, ComponentStatus] = Field(
        description="Status of individual components"
    )


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(description="Whether the service is ready")


class ConfigResponse(BaseModel):
    """Configuration response."""

    model_name: str = Field(description="LLM model name")
    temperature: float = Field(description="Model temperature", ge=0, le=2)
    max_iterations: int = Field(description="Maximum agent iterations")
    timeout: int = Field(description="Default timeout in seconds")
    available_tools: list[str] = Field(description="List of available diagnostic tools")