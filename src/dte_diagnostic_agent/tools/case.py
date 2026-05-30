"""Case search tool using LangChain StructuredTool."""

import json
import logging
from typing import TYPE_CHECKING

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

output_example = '''{
  "session_id": "会话ID",
  "query": "查询文本",
  "symptoms": ["症状1", "症状2"],
  "category": "分类",
  "cases": [
    {
      "case_id": "CASE-001",
      "title": "案例标题",
      "category": "分类",
      "score": 0.95
    }
  ],
  "total": 3,
  "executed": true
}'''

class CaseSearchInput(BaseModel):
    session_id: str = Field(default="", description="Session ID for logging")
    query: str = Field(description="Search query")
    symptoms: list[str] = Field(default=[], description="Symptoms to match")
    category: str | None = Field(default=None, description="Category filter")
    limit: int = Field(default=5, description="Result limit")


def create_case_search_tool(kb_manager: "KnowledgeBaseManager") -> StructuredTool:
    async def _case_search(
        session_id: str = "",
        query: str = "",
        symptoms: list[str] = [],
        category: str | None = None,
        limit: int = 5
    ) -> str:
        logger.info(f"[{session_id}] [CaseSearchTool] 开始搜索, query: {query}, symptoms: {symptoms}, category: {category}")
        
        results = await kb_manager.search(
            query=query,
            keywords=[query] if query else None,
            symptoms=symptoms,
            category=category,
            top_k=limit
        )
        
        cases_data = []
        for r in results:
            cases_data.append({
                "case_id": r.case.case_id,
                "title": r.case.title,
                "category": r.case.category,
                "score": r.similarity
            })
        
        output = {
            "session_id": session_id,
            "query": query,
            "symptoms": symptoms,
            "category": category,
            "total": len(cases_data),
            "cases": cases_data,
            "executed": True
        }
        
        logger.info(f"[{session_id}] [CaseSearchTool] 搜索完成, 找到 {len(cases_data)} 个案例: {[c['case_id'] for c in cases_data]}")
        
        return json.dumps(output)
    
    return StructuredTool.from_function(
        coroutine=_case_search,
        name="case_search",
        description="Search historical diagnostic cases in knowledge base",
        args_schema=CaseSearchInput,
        metadata={"output_example": output_example},
    )


async def _mock_case_search(
    session_id: str = "",
    query: str = "",
    symptoms: list[str] = [],
    category: str | None = None,
    limit: int = 5
) -> str:
    results = {
        "session_id": session_id,
        "query": query,
        "symptoms": symptoms,
        "category": category,
        "total": 0,
        "cases": []
    }
    
    return str(results).replace("'", '"')


MockCaseSearchTool = StructuredTool.from_function(
    coroutine=_mock_case_search,
    name="case_search",
    description="Mock case search tool (returns empty results)",
    args_schema=CaseSearchInput,
    metadata={"output_example": output_example},
)