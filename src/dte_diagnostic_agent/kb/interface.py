"""Knowledge base interface abstraction."""

from abc import ABC, abstractmethod

from dte_diagnostic_agent.kb.models import Case, SearchResult


class KnowledgeBaseInterface(ABC):
    """Abstract interface for knowledge base operations."""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """Search for relevant cases.
        
        Args:
            query: Search query string
            symptoms: Optional symptom filter list
            category: Optional category filter
            top_k: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    async def get(self, case_id: str) -> Case | None:
        """Get a specific case by ID.
        
        Args:
            case_id: Case identifier
            
        Returns:
            Case object or None if not found
        """
        pass
    
    @abstractmethod
    async def save(self, case: Case) -> str:
        """Save a new case.
        
        Args:
            case: Case object to save
            
        Returns:
            Case ID or file path
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        """List all cases.
        
        Args:
            category: Optional category filter
            limit: Maximum number of cases to return
            
        Returns:
            List of Case objects
        """
        pass
    
    @abstractmethod
    async def delete(self, case_id: str) -> bool:
        """Delete a case.
        
        Args:
            case_id: Case identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def reload(self) -> None:
        """Reload cases from storage."""
        pass