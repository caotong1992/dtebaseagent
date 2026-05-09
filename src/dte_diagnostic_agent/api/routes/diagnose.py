"""Diagnose API routes."""

import logging
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status, Depends

from dte_diagnostic_agent.api.schemas.diagnose import (
    DiagnoseRequest,
    DiagnoseCreateResponse,
    DiagnoseResult,
    DiagnoseStatus,
    DiagnoseListResponse,
    DiagnoseListItem,
    DiagnoseCancelResponse,
    DiagnoseProgress,
)
from dte_diagnostic_agent.api.schemas.common import PaginationInfo
from dte_diagnostic_agent.storage.session_store import SessionStore
from dte_diagnostic_agent.storage.models import SessionRecord, SessionStatus
from dte_diagnostic_agent.agent.core import DTEBaseDiagnosticAgent
from dte_diagnostic_agent.agent.models.input import UserInput
from dte_diagnostic_agent.agent.models.context import ClusterInfo
from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig, LocalKBConfig

router = APIRouter(prefix="/diagnose", tags=["diagnose"])

_session_store: SessionStore | None = None
_diagnostic_agent: DTEBaseDiagnosticAgent | None = None
_llm_config = None
_kb_config: KnowledgeBaseConfig | None = None


class LLMConfig:
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o",
        temperature: float = 0.1
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature


def get_session_store() -> SessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store


def set_session_store(store: SessionStore) -> None:
    global _session_store
    _session_store = store


def set_llm_config(config: LLMConfig) -> None:
    global _llm_config
    _llm_config = config


def get_llm_config() -> LLMConfig:
    global _llm_config
    if _llm_config is None:
        return LLMConfig()
    return _llm_config


def set_kb_config(config: KnowledgeBaseConfig) -> None:
    global _kb_config
    _kb_config = config


def get_kb_config() -> KnowledgeBaseConfig | None:
    return _kb_config


def get_diagnostic_agent() -> DTEBaseDiagnosticAgent:
    global _diagnostic_agent
    if _diagnostic_agent is None:
        config = get_llm_config()
        
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("LLM API key not configured (config.llm.api_key or OPENAI_API_KEY)")
        
        kb_manager = None
        query_processor_config = None
        kb_config = get_kb_config()
        if kb_config:
            kb_manager = KnowledgeBaseManager(kb_config)
            query_processor_config = kb_config.query_processor
        
        _diagnostic_agent = DTEBaseDiagnosticAgent(
            api_key=api_key,
            base_url=config.base_url,
            model_name=config.model_name,
            temperature=config.temperature,
            kb_manager=kb_manager,
            query_processor_config=query_processor_config
        )
    return _diagnostic_agent


def set_diagnostic_agent(agent: DTEBaseDiagnosticAgent) -> None:
    global _diagnostic_agent
    _diagnostic_agent = agent


def _generate_session_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"diag-{timestamp}-{unique_id}"


def _status_to_schema(status: SessionStatus) -> DiagnoseStatus:
    mapping = {
        SessionStatus.PENDING: DiagnoseStatus.PENDING,
        SessionStatus.RUNNING: DiagnoseStatus.RUNNING,
        SessionStatus.COMPLETED: DiagnoseStatus.COMPLETED,
        SessionStatus.FAILED: DiagnoseStatus.FAILED,
        SessionStatus.CANCELLED: DiagnoseStatus.CANCELLED,
    }
    return mapping.get(status, DiagnoseStatus.PENDING)


async def _run_diagnostic_task(
    session_id: str,
    request: DiagnoseRequest,
    store: SessionStore
):
    logger.info(f"[{session_id}] [Diagnose] 状态转换: PENDING -> RUNNING")
    await store.update(session_id, status=SessionStatus.RUNNING)
    
    try:
        agent = get_diagnostic_agent()
        
        environment = None
        if request.environment:
            environment = ClusterInfo(
                cluster_name=request.environment.cluster_name,
                service_name=request.environment.service_name or "DTEBaseService",
                namespace=request.environment.namespace,
            )
        
        user_input = UserInput(
            description=request.description,
            environment=environment,
            symptoms=request.symptoms or [],
            priority=request.priority or "medium"
        )
        
        report = await agent.diagnose(user_input)
        
        logger.info(f"[{session_id}] [Diagnose] 状态转换: RUNNING -> COMPLETED")
        await store.update(
            session_id,
            status=SessionStatus.COMPLETED,
            problem_category=report.problem_category.value if report.problem_category else "",
            top_hypothesis=report.top_hypothesis.hypothesis.problem if report.top_hypothesis else "",
            confidence=report.top_hypothesis.hypothesis.confidence if report.top_hypothesis else 0.0,
            completed_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"[{session_id}] [Diagnose] 任务失败, 阶段: diagnose, 错误: {str(e)}")
        logger.exception(f"[{session_id}] [Diagnose] 异常堆栈:")
        await store.update(
            session_id,
            status=SessionStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.now()
        )


@router.post(
    "",
    response_model=DiagnoseCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit diagnostic request",
    description="Submit a new diagnostic request and return session ID",
    responses={
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication failed"},
        403: {"description": "No permission to access the cluster"},
        500: {"description": "Internal server error"},
    },
)
async def create_diagnose(
    request: DiagnoseRequest,
    background_tasks: BackgroundTasks,
    store: SessionStore = Depends(get_session_store)
) -> DiagnoseCreateResponse:
    session_id = _generate_session_id()
    cluster_name = request.environment.cluster_name if request.environment else ""
    logger.info(f"[{session_id}] [Diagnose] 任务创建, 集群: {cluster_name}")
    
    record = SessionRecord(
        session_id=session_id,
        description=request.description,
        cluster_name=cluster_name,
        status=SessionStatus.PENDING,
        created_at=datetime.now(),
    )
    
    await store.create(record)
    
    background_tasks.add_task(
        _run_diagnostic_task,
        session_id,
        request,
        store
    )
    
    return DiagnoseCreateResponse(
        session_id=session_id,
        status=DiagnoseStatus.PENDING,
        created_at=datetime.now(),
        estimated_duration=300,
    )


@router.get(
    "/{session_id}",
    response_model=DiagnoseResult,
    summary="Query diagnostic result",
    description="Query diagnostic result by session ID",
    responses={
        200: {"description": "Return diagnostic result"},
        404: {"description": "Session not found"},
        410: {"description": "Session expired"},
    },
)
async def get_diagnose(
    session_id: str,
    format: str = Query(default="json", description="Output format: json/markdown/text"),
    include_evidence: bool = Query(default=False, description="Include collected evidence"),
    store: SessionStore = Depends(get_session_store)
) -> DiagnoseResult:
    logger.info(f"[{session_id}] [Diagnose] 查询诊断结果")
    record = await store.get(session_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    status_enum = _status_to_schema(record.status)
    
    percentage = 0
    current_step = ""
    completed_steps = []
    remaining_steps = ["analyze", "hypothesize", "report"]
    
    match record.status:
        case SessionStatus.PENDING:
            percentage = 10
            current_step = "initializing"
            remaining_steps = ["connect", "collect_evidence", "analyze", "hypothesize", "report"]
        case SessionStatus.RUNNING:
            percentage = 50
            current_step = "analyzing"
            completed_steps = ["connect", "collect_evidence"]
            remaining_steps = ["analyze", "hypothesize", "report"]
        case SessionStatus.COMPLETED:
            percentage = 100
            current_step = "completed"
            completed_steps = ["connect", "collect_evidence", "analyze", "hypothesize", "report"]
            remaining_steps = []
        case SessionStatus.FAILED:
            percentage = 0
            current_step = "failed"
            remaining_steps = []
        case SessionStatus.CANCELLED:
            percentage = 0
            current_step = "cancelled"
            remaining_steps = []
    
    return DiagnoseResult(
        session_id=record.session_id,
        status=status_enum,
        progress=DiagnoseProgress(
            current_step=current_step,
            completed_steps=completed_steps,
            remaining_steps=remaining_steps,
            percentage=percentage,
        ),
    )


@router.delete(
    "/{session_id}",
    response_model=DiagnoseCancelResponse,
    summary="Cancel diagnostic task",
    description="Cancel a running diagnostic task",
    responses={
        200: {"description": "Task cancelled successfully"},
        404: {"description": "Session not found"},
    },
)
async def cancel_diagnose(
    session_id: str,
    store: SessionStore = Depends(get_session_store)
) -> DiagnoseCancelResponse:
    record = await store.get(session_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    if record.status in (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel session in {record.status.value} status",
        )
    
    logger.info(f"[{session_id}] [Diagnose] 任务取消")
    await store.update(session_id, status=SessionStatus.CANCELLED)
    
    return DiagnoseCancelResponse(
        session_id=session_id,
        status=DiagnoseStatus.CANCELLED,
        cancelled_at=datetime.now(),
    )


@router.get(
    "/list",
    response_model=DiagnoseListResponse,
    summary="List diagnostic history",
    description="List historical diagnostic sessions",
)
async def list_diagnoses(
    limit: int = Query(default=20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    status_filter: str = Query(
        default="all",
        alias="status",
        description="Filter by status: all/pending/running/completed/failed",
    ),
    cluster: str | None = Query(default=None, description="Filter by cluster name"),
    start_date: str | None = Query(default=None, description="Start date filter"),
    end_date: str | None = Query(default=None, description="End date filter"),
    store: SessionStore = Depends(get_session_store)
) -> DiagnoseListResponse:
    status_enum = None
    if status_filter != "all":
        status_enum = SessionStatus(status_filter)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    records, total = await store.list_all(
        status_filter=status_enum,
        cluster=cluster,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset,
    )
    
    items = [
        DiagnoseListItem(
            session_id=r.session_id,
            description=r.description,
            cluster_name=r.cluster_name,
            status=_status_to_schema(r.status),
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in records
    ]
    
    return DiagnoseListResponse(
        total=total,
        items=items,
        pagination=PaginationInfo(
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )