"""Database query tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import requests, json, os

output_example = '''{
    "database": "数据库名",
    "sql": "执行的SQL",
    "rows": [
    {
      "colume1": "value1",
      "colume2": "value2",
      "colume3": "value3"
    },
    {
      "colume1": "value1",
      "colume2": "value2",
      "colume3": "value3"
    }
    ],
    "error": "错误信息(如果有)"
}'''

class DatabaseQueryInput(BaseModel):
    om_ip: str | None = Field(description="environment om ip")
    db_name: str | None = Field(description="Database name")
    sql: str | None = Field(description="sql query to execute on database")
    root_pwd: str | None = Field(default="", description="root password for om node")
    sopuser_pwd: str | None = Field(default="", description="sopuser password for om node")
    ossadm_pwd: str | None = Field(default="", description="ossadm password for om node")
    ssh_user:str | None = Field(default="", description="ssh user for om node")


async def _database_query(
    om_ip: str | None,
    db_name: str | None = "",
    sql: str | None = "",
    root_pwd: str | None = "",
    sopuser_pwd: str | None = "",
    ossadm_pwd: str | None = "",
    ssh_user: str | None = "",
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
            results["rows"] = _convert_output_example_to_json_schema(response.text)
    else:
        print(os.getcwd())
        mock_response = open("mock_data\database_query_response.json", "r").read()
        results["rows"] = _convert_output_example_to_json_schema(mock_response)
    
    return json.dumps(results)

def _convert_output_example_to_json_schema(query_response: str) -> dict:
    """Convert output_example string to JSON schema."""
    res_obj =json.loads(query_response)
    columns: list[str] = res_obj["columns"]
    converted_result = []
    data = res_obj["data"]
    for row in data:
        data_dict = {}
        for i in range(len(columns)):
            col = columns[i]
            data_dict[col] = row[i]
        converted_result.append(data_dict)
    return converted_result

DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="execute sql query to database and return result",
    args_schema=DatabaseQueryInput,
    metadata={"output_example": output_example},
)