"""Diagnostic plan models."""

from pydantic import BaseModel, Field


class DiagnosticStep(BaseModel):
    name: str = Field(description="Step name")
    description: str = Field(default="", description="Step description")
    tool_name: str = Field(description="Tool name to execute")
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")
    priority: int = Field(default=0, description="Step priority")
    dependencies: list[str] = Field(default_factory=list, description="Dependent step names")


class DiagnosticPlan(BaseModel):
    steps: list[DiagnosticStep] = Field(default_factory=list, description="Diagnostic steps")
    estimated_duration: int = Field(default=300, description="Estimated duration in seconds")
    
    def get_ordered_steps(self) -> list[DiagnosticStep]:
        return sorted(self.steps, key=lambda s: s.priority)