"""Log analysis tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import requests,json,os

output_example = '''{
  "command": "执行的命令",
  "logs": {
    "服务实例-1": "日志内容1",
    "服务实例-2": "日志内容2"
  },
  "error": "错误信息(如果有)"
}'''

class LogAnalysisInput(BaseModel):
    om_ip: str = Field(description="environment om ip")
    command: str = Field(description="command to query log")
    root_pwd: str = Field(default="", description="root password for om node")
    sopuser_pwd: str = Field(default="", description="sopuser password for om node")
    ossadm_pwd: str = Field(default="", description="ossadm password for om node")
    ssh_user:str = Field(default="", description="ssh user for om node")


async def _log_analysis(
    om_ip: str,
    command: str,
    root_pwd: str = "",
    sopuser_pwd: str = "",
    ossadm_pwd: str = "",
    ssh_user: str = "",
) -> str:
    results = {
        "command": command,
    } 
    if not os.environ.get('mock_mode'):
        payload = {
            "host": om_ip,
            "cmd": command,
            "service_name": "DTEBaseService",
            "root_pwd": root_pwd,
            "sopuser_pwd": sopuser_pwd,
            "ossadm_pwd": ossadm_pwd,
            "sshUser": ssh_user,
        }
        reponse = requests.post("https://omt.odae.dev.huawei.com/api/log_finder", payload, verify=False)
        if response.status_code != 200:
            results["error"] = f"Failed to query log: {response.status_code} - {response.text}"
        else:
            query_result = json.loads(response.text)['data']
            mapped_logs_info:dict[str,str] = {}
            for log in query_result:
                mapped_logs_info[f"服务实例-{log[0]}"] = log[1]
            results["logs"] = mapped_logs_info
    else:
        mock_response = open("test/mock_data/log_finder.response.json", "r").read()
        results["logs"] = json.loads(mock_response)
    
    return json.dumps(results)


LogAnalysisTool = StructuredTool.from_function(
    coroutine=_log_analysis,
    name="log_analysis",
    description="Analyze service logs to find errors and anomalies",
    args_schema=LogAnalysisInput,
    metadata={"output_example": output_example},
)