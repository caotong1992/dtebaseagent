"""Knowledge base configuration models."""

from pydantic import BaseModel, Field


class QueryProcessorConfig(BaseModel):
    """Query processor configuration."""
    
    enabled: bool = Field(default=True, description="Enable query processor")
    use_llm_translation: bool = Field(default=True, description="Use LLM for query translation")
    cache_size: int = Field(default=100, ge=0, description="Cache size for processed queries")


class LocalKBConfig(BaseModel):
    """Local markdown knowledge base configuration."""
    
    case_dir: str = Field(
        default="/var/lib/dte-diagnostic-agent/cases",
        description="Directory path for markdown case files"
    )


class RemoteKBConfig(BaseModel):
    """Remote knowledge base API configuration."""
    
    api_url: str = Field(description="Remote knowledge base API URL")
    api_key: str | None = Field(default=None, description="API key for authentication")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    headers: dict[str, str] = Field(default_factory=dict, description="Additional HTTP headers")


class KnowledgeBaseConfig(BaseModel):
    """Knowledge base configuration."""
    
    mode: str = Field(default="local", description="Knowledge base mode: local/remote")
    local: LocalKBConfig = Field(default_factory=LocalKBConfig, description="Local KB config")
    remote: RemoteKBConfig | None = Field(default=None, description="Remote KB config")
    query_processor: QueryProcessorConfig | None = Field(default=None, description="Query processor config")
    
    def validate_config(self) -> None:
        """Validate configuration based on mode."""
        match self.mode:
            case "local":
                if not self.local.case_dir:
                    raise ValueError("Local mode requires case_dir configuration")
            case "remote":
                if not self.remote or not self.remote.api_url:
                    raise ValueError("Remote mode requires api_url configuration")
            case _:
                raise ValueError(f"Unknown knowledge base mode: {self.mode}")