"""Session record models for CSV storage."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionRecord(BaseModel):
    session_id: str = Field(description="Unique session identifier")
    description: str = Field(default="", description="Problem description")
    cluster_name: str = Field(default="", description="Cluster name")
    status: SessionStatus = Field(default=SessionStatus.PENDING, description="Session status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    problem_category: str = Field(default="", description="Problem category")
    severity: str = Field(default="medium", description="Severity level")
    top_hypothesis: str = Field(default="", description="Top hypothesis")
    confidence: float = Field(default=0.0, description="Confidence score")
    error_message: str = Field(default="", description="Error message if failed")
    report_json: str = Field(default="", description="Serialized DiagnosticReport JSON")

    def to_csv_row(self) -> dict[str, str]:
        row = {
            "session_id": self.session_id,
            "description": self.description,
            "cluster_name": self.cluster_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "problem_category": self.problem_category,
            "severity": self.severity,
            "top_hypothesis": self.top_hypothesis,
            "confidence": str(self.confidence),
            "error_message": self.error_message,
            "report_json": self.report_json,
        }
        return row

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "SessionRecord":
        return cls(
            session_id=row.get("session_id", ""),
            description=row.get("description", ""),
            cluster_name=row.get("cluster_name", ""),
            status=SessionStatus(row.get("status", "pending")),
            created_at=datetime.fromisoformat(row.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(row.get("updated_at", datetime.now().isoformat())),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
            problem_category=row.get("problem_category", ""),
            severity=row.get("severity", "medium"),
            top_hypothesis=row.get("top_hypothesis", ""),
            confidence=float(row.get("confidence", "0.0")),
            error_message=row.get("error_message", ""),
            report_json=row.get("report_json", ""),
        )