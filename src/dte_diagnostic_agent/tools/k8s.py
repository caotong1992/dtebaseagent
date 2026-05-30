"""K8s operation tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

output_example = '''{
  "namespace": "命名空间",
  "action": "执行的操作",
  "pods": [{"name": "...", "status": "..."}],
  "logs": "Pod日志内容(如果有)",
  "description": "Pod描述信息(如果有)",
  "events": [],
  "error": "错误信息(如果有)"
}'''

class K8sOperationInput(BaseModel):
    namespace: str = Field(description="K8s namespace")
    pod_name: str | None = Field(default=None, description="Pod name")
    action: str = Field(description="Action: status/logs/describe/events")


async def _k8s_operation(
    namespace: str,
    pod_name: str | None = None,
    action: str = "status"
) -> str:
    results = {"namespace": namespace, "action": action}
    
    match action:
        case "status":
            results["pods"] = [
                {"name": "dtebaseservice-0", "status": "Running", "ready": True}
            ]
        case "logs":
            if pod_name:
                results["logs"] = f"Logs for {pod_name}"
        case "describe":
            if pod_name:
                results["description"] = f"Description for {pod_name}"
        case "events":
            results["events"] = []
        case _:
            results["error"] = "Unknown action"
    
    return str(results).replace("'", '"')


K8sOperationTool = StructuredTool.from_function(
    coroutine=_k8s_operation,
    name="k8s_operation",
    description="Execute Kubernetes operations: pod status, logs, events",
    args_schema=K8sOperationInput,
    metadata={"output_example": output_example},
)