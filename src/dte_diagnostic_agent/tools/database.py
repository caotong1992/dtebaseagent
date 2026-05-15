"""Database query tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class DatabaseQueryInput(BaseModel):
    om_ip: str = Field(description="environment om ip")
    db_name: str = Field(description="Database name")
    sql: str = Field(description="sql query to execute on database")


async def _database_query(
    om_ip: str,
    db_name: str = "",
    sql: str = ""
) -> str:
    results = {
        "database": f"{om_ip}/{db_name}",
        "sql": sql,
        "rows": [
            {
                "last_result": "failed",
                "last_error_code": "csm.loading.error",
                "last_fail_reason": "采集预加载失败"
            }
        ],
        "row_count": 1,
        "executed": True
    }
    
    import json
    return json.dumps(results)


DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="execute sql query to database and return result",
    args_schema=DatabaseQueryInput
)