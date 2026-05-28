"""Database query tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import requests, json, os


class DatabaseQueryInput(BaseModel):
    om_ip: str = Field(description="environment om ip")
    db_name: str = Field(description="Database name")
    sql: str = Field(description="sql query to execute on database")
    root_pwd: str = Field(default="", description="root password for om node")
    sopuser_pwd: str = Field(default="", description="sopuser password for om node")
    ossadm_pwd: str = Field(default="", description="ossadm password for om node")
    ssh_user:str = Field(default="", description="ssh user for om node")


async def _database_query(
    om_ip: str,
    db_name: str = "",
    sql: str = "",
    root_pwd: str = "",
    sopuser_pwd: str = "",
    ossadm_pwd: str = "",
    ssh_user: str = "",
) -> str:
    results = {
        "database": f"{db_name}",
        "sql": sql,
    }
    if not os.environ.get('mock_mode'):
        payload = {
            "host": om_ip,
            "db": db_name,
            "sql": sql,
            "root_pwd": root_pwd,
            "sopuser_pwd": sopuser_pwd,
            "ossadm_pwd": ossadm_pwd,
            "sshUser": ssh_user,
        }
        reponse = requests.post("https://omt.odae.dev.huawei.com/api/query_db", payload, verify=False)
        if response.status_code != 200:
            results["error"] = f"Failed to query database: {response.status_code} - {response.text}"
        else:
            results["rows"] = json.loads(response.text)
    else:
        mock_response = open("test/mock_data/database_query_response.json", "r").read()
        results["rows"] = json.loads(mock_response)
    return json.dumps(results)


DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="execute sql query to database and return result",
    args_schema=DatabaseQueryInput
)