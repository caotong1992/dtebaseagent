"""Diagnostic context models."""

from datetime import datetime
from enum import Enum
from typing import Any
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
    COLLECTION_TASK_FAILED = "collection_task_failed"
    UNKNOWN = "unknown"


class NodeInfo(BaseModel):
    node_name: str = Field(default="", description="Node name")
    host: str = Field(default="", description="Node host IP or domain")
    port: int = Field(default=22, description="SSH port")
    username: str = Field(default="", description="SSH username")
    auth_type: str = Field(default="password", description="Auth type: password/ssh_key")
    password: str | None = Field(default=None, description="SSH password")
    root_password: str | None = Field(default=None, description="Root password")
    ssh_key_path: str | None = Field(default=None, description="SSH key file path")


class ClusterInfo(BaseModel):
    cluster_name: str = Field(default="", description="Cluster name")
    cluster_type: str = Field(default="vm", description="Cluster type: k8s/vm")
    node_info: list[NodeInfo] = Field(default_factory=list, description="Target node info list")
    service_name: str = Field(default="DTEBaseService", description="Service name")
    namespace: str | None = Field(default=None, description="K8s namespace")


class TimeRange(BaseModel):
    start: datetime = Field(description="Start time")
    end: datetime = Field(description="End time")


class DiagnosticContext(BaseModel):
    session_id: str = Field(description="Session ID")
    problem_description: str = Field(description="Problem description")
    time_range: TimeRange | None = Field(default=None, description="Time range")
    environment: ClusterInfo | None = Field(default=None, description="Environment info")
    symptoms: list[str] = Field(default_factory=list, description="Symptom list")
    priority: Severity = Field(default=Severity.MEDIUM, description="Priority level")
    category: ProblemCategory | None = Field(default=None, description="Problem category")
    collected_data: dict[str, Any] = Field(default_factory=dict, description="步骤执行收集的数据")
    metadata: dict[str, object] = Field(default_factory=dict, description="Additional metadata")
    extracted_vars: dict[str, Any] = Field(default_factory=dict, description="提取的变量")
    retrieval_results: dict[str, Any] = Field(default_factory=dict, description="检索结果")

    def set_var(self, name: str, value: Any):
        self.collected_data[name.lower()] = value

    def get_var_value(self, name: str) -> Any:
        return self.collected_data.get(name.lower(), None)
