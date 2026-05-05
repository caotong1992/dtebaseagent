"""User input model."""

from datetime import datetime
from pydantic import BaseModel, Field

from dte_diagnostic_agent.agent.models.context import ClusterInfo


class UserInput(BaseModel):
    description: str = Field(description="Problem description")
    time_range_start: datetime | None = Field(default=None, description="Problem start time")
    time_range_end: datetime | None = Field(default=None, description="Problem end time")
    environment: ClusterInfo | None = Field(default=None, description="Environment info")
    symptoms: list[str] = Field(default_factory=list, description="Symptom list")
    priority: str = Field(default="medium", description="Priority level")