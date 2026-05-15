"""Diagnostic plan models."""

from pydantic import BaseModel, Field

from dte_diagnostic_agent.agent.models.parsed_step import ExtractRule


class DiagnosticStep(BaseModel):
    name: str = Field(description="Step name")
    description: str = Field(default="", description="Step description")
    tool_name: str = Field(description="Tool name to execute")
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")
    priority: int = Field(default=0, description="Step priority")
    dependencies: list[str] = Field(default_factory=list, description="Dependent step names")
    template_vars: list[str] = Field(default_factory=list, description="Template variables in parameters")
    output_vars: list[str] = Field(default_factory=list, description="Output variable names")
    extract_rules: dict[str, ExtractRule] = Field(default_factory=dict, description="Extraction rules for output variables")


class DiagnosticPlan(BaseModel):
    session_id: str = Field(default="", description="Session ID for traceability")
    steps: list[DiagnosticStep] = Field(default_factory=list, description="Diagnostic steps")
    estimated_duration: int = Field(default=300, description="Estimated duration in seconds")
    
    def get_ordered_steps(self) -> list[DiagnosticStep]:
        return sorted(self.steps, key=lambda s: s.priority)