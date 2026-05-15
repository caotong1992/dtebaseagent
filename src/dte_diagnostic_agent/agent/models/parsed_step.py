"""Parsed step models for case step parser."""

from enum import Enum

from pydantic import BaseModel, Field


class StepActionType(str, Enum):
    TOOL_EXECUTE = "tool_execute"
    CASE_SEARCH = "case_search"
    MANUAL_CHECK = "manual_check"
    DECISION = "decision"


class ExtractType(str, Enum):
    FIELD = "field"
    REGEX = "regex"
    JSON_PATH = "json_path"


class ExtractRule(BaseModel):
    source: str = Field(description="Data source, e.g., 'rows', 'raw_result', 'result'")
    type: ExtractType = Field(description="Extraction type")
    value: str = Field(description="Field name, regex pattern, or JSON path")


class ParsedStep(BaseModel):
    step_number: int = Field(description="Step sequence number")
    action_type: StepActionType = Field(description="Type of action to perform")
    tool_name: str | None = Field(default=None, description="Tool name for tool_execute action")
    parameters: dict[str, object] = Field(default_factory=dict, description="Action parameters")
    description: str = Field(default="", description="Step description")
    next_action: str | None = Field(default=None, description="Next action hint")
    template_vars: list[str] = Field(default_factory=list, description="Template variables in parameters")
    output_vars: list[str] = Field(default_factory=list, description="Output variable names")
    extract_rules: dict[str, ExtractRule] = Field(default_factory=dict, description="Extraction rules for output variables")


class ParsedAnalysis(BaseModel):
    case_id: str = Field(description="Source case ID")
    steps: list[ParsedStep] = Field(default_factory=list, description="Parsed diagnostic steps")
    has_iterative_search: bool = Field(default=False, description="Whether contains case_search action")