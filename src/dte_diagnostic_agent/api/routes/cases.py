"""Case management API routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from dte_diagnostic_agent.api.schemas.cases import (
    CaseSearchResponse,
    CaseSearchItem,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetail,
    CaseSolution,
    CaseMetadata,
)

router = APIRouter(prefix="/cases", tags=["cases"])

_cases_db: dict[str, CaseDetail] = {}


@router.get(
    "/search",
    response_model=CaseSearchResponse,
    summary="Search historical cases",
    description="Search historical diagnostic cases",
)
async def search_cases(
    query: str = Query(..., description="Search keywords"),
    symptoms: str | None = Query(default=None, description="Symptom filter, comma separated"),
    category: str | None = Query(default=None, description="Problem category filter"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of items to return"),
) -> CaseSearchResponse:
    """Search historical cases."""
    items = [
        CaseSearchItem(
            case_id="CASE-001",
            title="Database connection timeout",
            symptoms=["connection_timeout", "slow_response"],
            problem="Database connection pool exhausted",
            solution_summary="Increased connection pool size and optimized connection handling",
            similarity=0.85,
            created_at=datetime.now(),
        )
    ]
    
    return CaseSearchResponse(total=len(items), items=items)


@router.post(
    "",
    response_model=CaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new case",
    description="Create a new case from diagnostic result",
)
async def create_case(request: CaseCreateRequest) -> CaseCreateResponse:
    """Create a new case from diagnostic session."""
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    
    case = CaseDetail(
        case_id=case_id,
        title=request.title,
        symptoms=[],
        problem="Problem from diagnostic session",
        solution=CaseSolution(
            description="Solution from diagnostic",
            steps=["Step 1", "Step 2"],
        ),
        metadata=CaseMetadata(
            cluster=None,
            service=None,
            created_at=datetime.now(),
        ),
    )
    _cases_db[case_id] = case
    
    return CaseCreateResponse(
        case_id=case_id,
        created_at=datetime.now(),
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetail,
    summary="Get case details",
    description="Get detailed case information by ID",
    responses={
        200: {"description": "Return case details"},
        404: {"description": "Case not found"},
    },
)
async def get_case(case_id: str) -> CaseDetail:
    """Get case details by ID."""
    if case_id not in _cases_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    
    return _cases_db[case_id]