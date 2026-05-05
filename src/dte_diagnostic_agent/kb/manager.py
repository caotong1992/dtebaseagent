"""Knowledge base manager."""

from dte_diagnostic_agent.kb.interface import KnowledgeBaseInterface
from dte_diagnostic_agent.kb.models import Case, SearchResult
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig
from dte_diagnostic_agent.kb.local_kb import LocalMarkdownKB
from dte_diagnostic_agent.kb.remote_kb import RemoteKBClient


class KnowledgeBaseManager:
    """Knowledge base manager - selects implementation based on config."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        config.validate_config()
        self.config = config
        self.backend: KnowledgeBaseInterface
        
        match config.mode:
            case "local":
                self.backend = LocalMarkdownKB(config.local)
            case "remote":
                self.backend = RemoteKBClient(config.remote)
            case _:
                raise ValueError(f"Unknown knowledge base mode: {config.mode}")
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """Search for relevant cases."""
        return await self.backend.search(query, symptoms, category, top_k)
    
    async def get(self, case_id: str) -> Case | None:
        """Get a specific case."""
        return await self.backend.get(case_id)
    
    async def save(self, case: Case) -> str:
        """Save a new case."""
        return await self.backend.save(case)
    
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        """List all cases."""
        return await self.backend.list_all(category, limit)
    
    async def delete(self, case_id: str) -> bool:
        """Delete a case."""
        return await self.backend.delete(case_id)
    
    async def reload(self) -> None:
        """Reload cases from storage."""
        return await self.backend.reload()
    
    def get_backend_type(self) -> str:
        """Get current backend type."""
        return self.config.mode