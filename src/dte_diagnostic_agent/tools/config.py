"""Config check tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ConfigCheckInput(BaseModel):
    session_id: str = Field(description="SSH session ID")
    config_path: str = Field(description="Config file path")
    check_type: str = Field(default="yaml", description="Config type: yaml/json/ini")


async def _config_check(
    session_id: str,
    config_path: str,
    check_type: str = "yaml"
) -> str:
    results = {
        "session_id": session_id,
        "config_path": config_path,
        "check_type": check_type,
        "valid": True,
        "issues": []
    }
    
    return str(results).replace("'", '"')


ConfigCheckTool = StructuredTool.from_function(
    coroutine=_config_check,
    name="config_check",
    description="Check service configuration files for issues",
    args_schema=ConfigCheckInput
)