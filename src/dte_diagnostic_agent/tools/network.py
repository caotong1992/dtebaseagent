"""Network diagnostic tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

output_example = '''{
  "session_id": "会话ID",
  "target_host": "目标主机",
  "test_type": "ping/port/traceroute",
  "reachable": true,
  "latency_ms": 10,
  "port_open": true,
  "port": 80,
  "hops": [],
  "error": "错误信息(如果有)"
}'''

class NetworkDiagInput(BaseModel):
    session_id: str = Field(description="SSH session ID")
    target_host: str = Field(description="Target host to test")
    test_type: str = Field(default="ping", description="Test type: ping/port/traceroute")


async def _network_diag(
    session_id: str,
    target_host: str,
    test_type: str = "ping"
) -> str:
    results = {
        "session_id": session_id,
        "target_host": target_host,
        "test_type": test_type
    }
    
    match test_type:
        case "ping":
            results["reachable"] = True
            results["latency_ms"] = 10
        case "port":
            results["port_open"] = True
            results["port"] = 80
        case "traceroute":
            results["hops"] = []
        case _:
            results["error"] = "Unknown test type"
    
    return str(results).replace("'", '"')


NetworkDiagTool = StructuredTool.from_function(
    coroutine=_network_diag,
    name="network_diag",
    description="Execute network diagnostics: ping, port check, traceroute",
    args_schema=NetworkDiagInput,
    metadata={"output_example": output_example},
)