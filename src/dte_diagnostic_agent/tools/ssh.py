"""SSH connection tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SSHConnectInput(BaseModel):
    host: str = Field(description="Target host IP or domain")
    port: int = Field(default=22, description="SSH port")
    username: str = Field(description="SSH username")
    password: str | None = Field(default=None, description="SSH password")
    ssh_key_path: str | None = Field(default=None, description="SSH key file path")


async def _ssh_connect(
    host: str,
    port: int = 22,
    username: str = "",
    password: str | None = None,
    ssh_key_path: str | None = None
) -> str:
    try:
        import asyncssh
    except ImportError:
        return f"SSH connection failed: asyncssh module not installed. Please install it with: pip install asyncssh"
    
    try:
        conn = await asyncssh.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            client_keys=[ssh_key_path] if ssh_key_path else None,
            known_hosts=None
        )
        conn.close()
        return f"Successfully connected to {host}:{port}"
    except Exception as e:
        return f"Connection failed: {str(e)}"


SSHConnectTool = StructuredTool.from_function(
    coroutine=_ssh_connect,
    name="ssh_connect",
    description="Connect to target server node for executing remote commands",
    args_schema=SSHConnectInput
)