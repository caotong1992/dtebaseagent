"""Log analysis tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import re


class LogAnalysisInput(BaseModel):
    om_ip: str = Field(description="environment om ip")
    command: str = Field(description="command to query log")


async def _log_analysis(
    om_ip: str,
    command: str
) -> str:
    results = {
        "om_ip": om_ip,
        "command": command,
        "output": "[2026-01-01 12:00:00] Error: Redis timeout"
    }
    return str(results).replace("'", '"')


LogAnalysisTool = StructuredTool.from_function(
    coroutine=_log_analysis,
    name="log_analysis",
    description="Analyze service logs to find errors and anomalies",
    args_schema=LogAnalysisInput
)