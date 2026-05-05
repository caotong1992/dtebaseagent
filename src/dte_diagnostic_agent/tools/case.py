"""Case search tool using LangChain StructuredTool."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class CaseSearchInput(BaseModel):
    query: str = Field(description="Search query")
    symptoms: list[str] = Field(default=[], description="Symptoms to match")
    category: str | None = Field(default=None, description="Category filter")
    limit: int = Field(default=5, description="Result limit")


async def _case_search(
    query: str,
    symptoms: list[str] = [],
    category: str | None = None,
    limit: int = 5
) -> str:
    results = {
        "query": query,
        "symptoms": symptoms,
        "category": category,
        "total": 0,
        "cases": []
    }
    
    return str(results).replace("'", '"')


CaseSearchTool = StructuredTool.from_function(
    coroutine=_case_search,
    name="case_search",
    description="Search historical diagnostic cases",
    args_schema=CaseSearchInput
)