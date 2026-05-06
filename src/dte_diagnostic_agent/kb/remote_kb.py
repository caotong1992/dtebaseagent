"""Remote knowledge base API client implementation."""

from datetime import datetime

import httpx

from dte_diagnostic_agent.kb.interface import KnowledgeBaseInterface
from dte_diagnostic_agent.kb.models import Case, SearchResult
from dte_diagnostic_agent.kb.config import RemoteKBConfig


class RemoteKBClient(KnowledgeBaseInterface):
    """Remote knowledge base API client."""
    
    def __init__(self, config: RemoteKBConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            timeout=config.timeout,
            headers=self._build_headers()
        )
    
    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.headers)
        return headers
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10,
        keywords: list[str] | None = None
    ) -> list[SearchResult]:
        """Search via remote API."""
        try:
            response = await self.client.post(
                "/api/v1/kb/search",
                json={
                    "query": query,
                    "symptoms": symptoms,
                    "category": category,
                    "top_k": top_k,
                    "keywords": keywords
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                SearchResult(
                    case=self._parse_case(item.get("case", {})),
                    similarity=item.get("similarity", 0.0),
                    match_reason=item.get("match_reason", "")
                )
                for item in data.get("results", [])
            ]
        except httpx.HTTPError as e:
            print(f"Remote KB search error: {e}")
            return []
    
    async def get(self, case_id: str) -> Case | None:
        """Get case via remote API."""
        try:
            response = await self.client.get(f"/api/v1/kb/cases/{case_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._parse_case(response.json())
        except httpx.HTTPError:
            return None
    
    async def save(self, case: Case) -> str:
        """Save case via remote API."""
        response = await self.client.post(
            "/api/v1/kb/cases",
            json=case.model_dump()
        )
        response.raise_for_status()
        return response.json().get("case_id", case.case_id)
    
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        """List cases via remote API."""
        try:
            response = await self.client.get(
                "/api/v1/kb/cases",
                params={"category": category, "limit": limit}
            )
            response.raise_for_status()
            return [
                self._parse_case(item)
                for item in response.json().get("items", [])
            ]
        except httpx.HTTPError:
            return []
    
    async def delete(self, case_id: str) -> bool:
        """Delete case via remote API."""
        try:
            response = await self.client.delete(f"/api/v1/kb/cases/{case_id}")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
    
    async def reload(self) -> None:
        """Reload not applicable for remote KB."""
        pass
    
    def _parse_case(self, data: dict) -> Case:
        """Parse case from API response."""
        return Case(
            case_id=data.get("case_id", ""),
            title=data.get("title", ""),
            category=data.get("category", "unknown"),
            severity=data.get("severity", "medium"),
            symptoms=data.get("symptoms", []),
            problem=data.get("problem", ""),
            analysis=data.get("analysis", ""),
            solution=data.get("solution", []),
            verification=data.get("verification", ""),
            references=data.get("references", []),
            related_cases=data.get("related_cases", []),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            tags=data.get("tags", []),
            cluster=data.get("cluster"),
            service=data.get("service"),
        )
    
    def _parse_datetime(self, value: str | None) -> datetime:
        """Parse datetime from string."""
        if not value:
            return datetime.now()
        
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now()
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()