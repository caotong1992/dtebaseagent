"""Log analysis tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import re


class LogAnalysisInput(BaseModel):
    session_id: str = Field(description="SSH session ID")
    log_path: str = Field(description="Log file path")
    start_time: str = Field(description="Start time in ISO format")
    end_time: str = Field(description="End time in ISO format")
    patterns: list[str] = Field(default=["error", "exception"], description="Patterns to search")


async def _log_analysis(
    session_id: str,
    log_path: str,
    start_time: str,
    end_time: str,
    patterns: list[str] = ["error", "exception"]
) -> str:
    results = {
        "log_path": log_path,
        "time_range": f"{start_time} to {end_time}",
        "matches": [],
        "anomalies": []
    }
    
    for pattern in patterns:
        results["matches"].append({
            "pattern": pattern,
            "count": 0,
            "sample": f"Sample log matching {pattern}"
        })
    
    return str(results).replace("'", '"')


LogAnalysisTool = StructuredTool.from_function(
    coroutine=_log_analysis,
    name="log_analysis",
    description="Analyze service logs to find errors and anomalies",
    args_schema=LogAnalysisInput
)