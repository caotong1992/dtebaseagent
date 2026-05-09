"""Database query tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class DatabaseQueryInput(BaseModel):
    db_host: str = Field(description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(description="Database name")
    db_user: str = Field(description="Database user")
    db_password: str = Field(description="Database password")
    query_type: str = Field(description="Query type: connections/slow_queries/locks/replication")


async def _database_query(
    db_host: str,
    db_port: int = 5432,
    db_name: str = "",
    db_user: str = "",
    db_password: str = "",
    query_type: str = "connections"
) -> str:
    results = {
        "database": f"{db_host}:{db_port}/{db_name}",
        "query_type": query_type
    }
    #  last_result,last_error_code,last_fail_reason
    results["last_result"] = "failed"
    results["last_error_code"] = "csm.loading.error"
    results["last_fail_reason"] = "采集预加载失败"
    
    # match query_type:
    #     case "connections":
    #         results["active_connections"] = 50
    #         results["max_connections"] = 100
    #     case "slow_queries":
    #         results["slow_queries"] = [
    #             {"query": "SELECT * FROM large_table", "time_ms": 5000}
    #         ]
    #     case "locks":
    #         results["locks"] = []
    #     case "replication":
    #         results["replication_active"] = True
    #     case _:
    #         results["error"] = "Unknown query type"
    
    return str(results).replace("'", '"')


DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="Query database status including connections, slow queries, locks",
    args_schema=DatabaseQueryInput
)