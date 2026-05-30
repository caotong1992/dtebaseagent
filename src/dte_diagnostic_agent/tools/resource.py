"""Resource monitor tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

output_example = '''{
  "session_id": "会话ID",
  "metrics": {
    "cpu": {
      "usage_percent": 45.5,
      "idle_percent": 54.5
    },
    "memory": {
      "total_mb": 8192,
      "used_mb": 4096,
      "free_mb": 4096,
      "usage_percent": 50.0
    },
    "disk": {
      "total_gb": 100,
      "used_gb": 60,
      "available_gb": 40,
      "usage_percent": 60.0
    },
    "network": {
      "bytes_in": 1000000,
      "bytes_out": 500000
    }
  }
}'''

class ResourceMonitorInput(BaseModel):
    session_id: str = Field(description="SSH session ID")
    metrics: list[str] = Field(default=["cpu", "memory", "disk"], description="Metrics to collect")


async def _resource_monitor(
    session_id: str,
    metrics: list[str] = ["cpu", "memory", "disk"]
) -> str:
    results = {"session_id": session_id, "metrics": {}}
    
    for metric in metrics:
        match metric:
            case "cpu":
                results["metrics"]["cpu"] = {
                    "usage_percent": 45.5,
                    "idle_percent": 54.5
                }
            case "memory":
                results["metrics"]["memory"] = {
                    "total_mb": 8192,
                    "used_mb": 4096,
                    "free_mb": 4096,
                    "usage_percent": 50.0
                }
            case "disk":
                results["metrics"]["disk"] = {
                    "total_gb": 100,
                    "used_gb": 60,
                    "available_gb": 40,
                    "usage_percent": 60.0
                }
            case "network":
                results["metrics"]["network"] = {
                    "bytes_in": 1000000,
                    "bytes_out": 500000
                }
    
    return str(results).replace("'", '"')


ResourceMonitorTool = StructuredTool.from_function(
    coroutine=_resource_monitor,
    name="resource_monitor",
    description="Collect system resource metrics including CPU, memory, disk",
    args_schema=ResourceMonitorInput,
    metadata={"output_example": output_example},
)