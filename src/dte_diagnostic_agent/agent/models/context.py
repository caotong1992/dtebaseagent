"""Diagnostic context models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProblemCategory(str, Enum):
    SERVICE_UNAVAILABLE = "service_unavailable"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_INCONSISTENCY = "data_inconsistency"
    NETWORK_ISSUE = "network_issue"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class NodeInfo(BaseModel):
    host: str = Field(description="Node host IP or domain")
    port: int = Field(default=22, description="SSH port")
    username: str = Field(default="", description="SSH username")
    auth_type: str = Field(default="password", description="Auth type: password/ssh_key")
    password: str | None = Field(default=None, description="SSH password")
    ssh_key_path: str | None = Field(default=None, description="SSH key file path")


class ClusterInfo(BaseModel):
    cluster_name: str = Field(description="Cluster name")
    cluster_type: str = Field(default="standalone", description="Cluster type: k8s/standalone")
    node_info: NodeInfo | None = Field(default=None, description="Target node info")
    service_name: str = Field(default="DTEBaseService", description="Service name")
    namespace: str | None = Field(default=None, description="K8s namespace")


class TimeRange(BaseModel):
    start: datetime = Field(description="Start time")
    end: datetime = Field(description="End time")


class DiagnosticContext(BaseModel):
    session_id: str = Field(description="Session ID")
    problem_description: str = Field(description="Problem description")
    time_range: TimeRange = Field(description="Time range")
    environment: ClusterInfo = Field(description="Environment info")
    symptoms: list[str] = Field(default_factory=list, description="Symptom list")
    priority: Severity = Field(default=Severity.MEDIUM, description="Priority level")
    category: ProblemCategory | None = Field(default=None, description="Problem category")
    collected_data: dict[str, object] = Field(default_factory=dict, description="Collected diagnostic data")
    metadata: dict[str, object] = Field(default_factory=dict, description="Additional metadata")