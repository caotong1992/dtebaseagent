"""API client for dte-diag CLI tool."""

import json
from datetime import datetime
from typing import Any

import httpx

from pydantic import BaseModel


class DiagnoseRequest(BaseModel):
    description: str
    cluster_name: str
    time_range: dict[str, str] | None = None
    node_info: dict[str, Any] | None = None
    service_name: str = "DTEBaseService"
    namespace: str | None = None
    symptoms: list[str] | None = None
    priority: str = "medium"
    options: dict[str, Any] | None = None


class DiagnoseResponse(BaseModel):
    session_id: str
    status: str
    created_at: str
    estimated_duration: int | None = None


class DiagnoseResult(BaseModel):
    session_id: str
    status: str
    generated_at: str | None = None
    summary: str | None = None
    problem_category: str | None = None
    severity: str | None = None
    hypotheses: list[dict[str, Any]] | None = None
    top_hypothesis: dict[str, Any] | None = None
    recommended_solutions: list[dict[str, Any]] | None = None
    similar_cases: list[dict[str, Any]] | None = None
    next_steps: list[str] | None = None
    escalation_needed: bool | None = None
    progress: dict[str, Any] | None = None


class CaseSearchResult(BaseModel):
    total: int
    items: list[dict[str, Any]]


class ClusterInfo(BaseModel):
    name: str
    type: str
    status: str
    services: list[str]
    nodes: list[dict[str, Any]]


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIClient:
    """API client for dte-diag diagnostic service."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers["Content-Type"] = "application/json"
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        client = self._get_client()
        try:
            response = client.request(method, path, **kwargs)
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("detail", error_data.get("message", f"HTTP {response.status_code}"))
                raise APIError(error_msg, response.status_code)
            return response.json()
        except httpx.TimeoutException:
            raise APIError(f"请求超时 ({self.timeout}秒)")
        except httpx.ConnectError:
            raise APIError(f"无法连接到服务 {self.base_url}")
        except json.JSONDecodeError:
            raise APIError("响应格式无效")

    def submit_diagnose(self, request: DiagnoseRequest) -> DiagnoseResponse:
        data = self._request("POST", "/api/v1/diagnose", json=request.model_dump())
        return DiagnoseResponse(**data)

    def get_diagnose_result(self, session_id: str, include_evidence: bool = False) -> DiagnoseResult:
        params = {}
        if include_evidence:
            params["include_evidence"] = "true"
        data = self._request("GET", f"/api/v1/diagnose/{session_id}", params=params)
        return DiagnoseResult(**data)

    def cancel_diagnose(self, session_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/api/v1/diagnose/{session_id}")

    def list_diagnoses(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        cluster: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if cluster:
            params["cluster"] = cluster
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._request("GET", "/api/v1/diagnose/list", params=params)

    def search_cases(
        self,
        query: str,
        symptoms: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> CaseSearchResult:
        params = {"query": query, "limit": limit}
        if symptoms:
            params["symptoms"] = symptoms
        if category:
            params["category"] = category
        data = self._request("GET", "/api/v1/cases/search", params=params)
        return CaseSearchResult(**data)

    def get_case(self, case_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/cases/{case_id}")

    def create_case(self, session_id: str, title: str, tags: list[str] | None = None) -> dict[str, Any]:
        payload = {"session_id": session_id, "title": title}
        if tags:
            payload["tags"] = tags
        return self._request("POST", "/api/v1/cases", json=payload)

    def list_cases(self, limit: int = 20) -> dict[str, Any]:
        return self._request("GET", "/api/v1/cases", params={"limit": limit})

    def get_clusters(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/clusters")

    def get_cluster_status(self, cluster_name: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/clusters/{cluster_name}/status")

    def test_cluster_connection(self, cluster_name: str, node: str | None = None) -> dict[str, Any]:
        params = {}
        if node:
            params["node"] = node
        return self._request("POST", f"/api/v1/clusters/{cluster_name}/test", params=params)

    def health_check(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/health")

    def get_config(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/config")