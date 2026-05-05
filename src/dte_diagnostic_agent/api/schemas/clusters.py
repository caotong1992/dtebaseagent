"""Cluster management schemas."""

from pydantic import BaseModel, Field


class NodeStatus(BaseModel):
    """Node status information."""

    host: str = Field(description="Node host")
    status: str = Field(description="Node status")


class ClusterInfo(BaseModel):
    """Cluster information."""

    name: str = Field(description="Cluster name")
    type: str = Field(description="Cluster type: k8s/standalone")
    status: str = Field(description="Cluster status: available/unavailable")
    services: list[str] = Field(description="List of services")
    nodes: list[NodeStatus] = Field(description="List of nodes")


class ClusterListResponse(BaseModel):
    """Response for cluster list."""

    clusters: list[ClusterInfo] = Field(description="List of clusters")


class NodeMetrics(BaseModel):
    """Node metrics."""

    host: str = Field(description="Node host")
    cpu_usage: float = Field(description="CPU usage percentage", ge=0, le=100)
    memory_usage: float = Field(description="Memory usage percentage", ge=0, le=100)
    disk_usage: float = Field(description="Disk usage percentage", ge=0, le=100)
    status: str = Field(description="Node status")


class ServiceInfo(BaseModel):
    """Service information."""

    name: str = Field(description="Service name")
    status: str = Field(description="Service status")
    pods: list[str] = Field(description="List of pods")


class ClusterStatusResponse(BaseModel):
    """Response for cluster status."""

    cluster_name: str = Field(description="Cluster name")
    status: str = Field(description="Cluster status")
    nodes: list[NodeMetrics] = Field(description="Node metrics")
    services: list[ServiceInfo] = Field(description="Service information")