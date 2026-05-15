"""Diagnose API routes."""

import asyncio
import json
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
    Hypothesis,
    TopHypothesis,
    RecommendedSolution,
    SimilarCase,
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
        
        report = await agent.diagnose(user_input, session_id=session_id)
        
        report_json_str = report.model_dump_json()
        
        logger.info(f"[{session_id}] [Diagnose] 状态转换: RUNNING -> COMPLETED")
        await store.update(
            session_id,
            status=SessionStatus.COMPLETED,
            problem_category=report.problem_category.value if report.problem_category else "",
            top_hypothesis=report.top_hypothesis.hypothesis.problem if report.top_hypothesis else "",
            confidence=report.top_hypothesis.hypothesis.confidence if report.top_hypothesis else 0.0,
            completed_at=datetime.now(),
            report_json=report_json_str
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


_scheduler_running: bool = False
_scheduler_task: asyncio.Task | None = None


async def _task_scheduler_loop(store: SessionStore):
    global _scheduler_running
    logger.info("[Scheduler] 任务调度器启动")
    
    while _scheduler_running:
        try:
            records, _ = await store.list_all(status_filter=SessionStatus.RUNNING, limit=10)
            running_count = len(records)
            
            if running_count == 0:
                pending_records, _ = await store.list_all(status_filter=SessionStatus.PENDING, limit=1)
                
                if pending_records:
                    record = pending_records[0]
                    session_id = record.session_id
                    
                    logger.info(f"[Scheduler] 发现 PENDING 任务: {session_id}, 启动诊断")
                    
                    await store.update(session_id, status=SessionStatus.RUNNING)
                    
                    logger.info(f"[{session_id}] [Scheduler] 状态转换: PENDING -> RUNNING")
                    
                    request = DiagnoseRequest(
                        description=record.description,
                        environment=None,
                        symptoms=[],
                        priority=record.severity
                    )
                    
                    asyncio.create_task(_run_diagnostic_task(session_id, request, store))
            
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"[Scheduler] 调度器异常: {str(e)}")
            logger.exception("[Scheduler] 异常堆栈:")
            await asyncio.sleep(5)


def start_scheduler(store: SessionStore) -> asyncio.Task:
    global _scheduler_running, _scheduler_task
    
    if _scheduler_task is not None and not _scheduler_task.done():
        logger.warning("[Scheduler] 调度器已在运行")
        return _scheduler_task
    
    _scheduler_running = True
    _scheduler_task = asyncio.create_task(_task_scheduler_loop(store))
    logger.info("[Scheduler] 调度器任务已创建")
    return _scheduler_task


def stop_scheduler():
    global _scheduler_running, _scheduler_task
    
    _scheduler_running = False
    if _scheduler_task:
        _scheduler_task.cancel()
        logger.info("[Scheduler] 调度器已停止")


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
    
    summary = None
    hypotheses = None
    top_hypothesis = None
    recommended_solutions = None
    similar_cases = None
    next_steps = None
    escalation_needed = False
    generated_at = None
    error = None
    
    if record.status == SessionStatus.COMPLETED and record.report_json:
        try:
            report_data = json.loads(record.report_json)
            summary = report_data.get("summary")
            generated_at = datetime.fromisoformat(report_data.get("generated_at")) if report_data.get("generated_at") else None
            
            raw_hypotheses = report_data.get("hypotheses", [])
            if raw_hypotheses:
                hypotheses = [
                    Hypothesis(
                        id=h.get("hypothesis", {}).get("id", ""),
                        problem=h.get("hypothesis", {}).get("problem", ""),
                        confidence=h.get("hypothesis", {}).get("confidence", 0.0),
                        evidence=h.get("hypothesis", {}).get("evidence", []),
                        actions=h.get("hypothesis", {}).get("actions", []),
                    )
                    for h in raw_hypotheses
                ]
            
            raw_top = report_data.get("top_hypothesis")
            if raw_top and raw_top.get("hypothesis"):
                top_hypothesis = TopHypothesis(
                    problem=raw_top.get("hypothesis", {}).get("problem", ""),
                    confidence=raw_top.get("hypothesis", {}).get("confidence", 0.0),
                )
            
            raw_solutions = report_data.get("recommended_solutions", [])
            if raw_solutions:
                recommended_solutions = [
                    RecommendedSolution(
                        description=s.get("description", ""),
                        steps=s.get("steps", []),
                        confidence=s.get("confidence", 0.0),
                    )
                    for s in raw_solutions
                ]
            
            raw_cases = report_data.get("similar_cases", [])
            if raw_cases:
                similar_cases = [
                    SimilarCase(
                        case_id=c.get("case_id", ""),
                        title=c.get("title", ""),
                        similarity=c.get("similarity", 0.0),
                    )
                    for c in raw_cases
                ]
            
            next_steps = report_data.get("next_steps", [])
            escalation_needed = report_data.get("escalation_needed", False)
        except Exception as e:
            logger.warning(f"[{session_id}] [Diagnose] 解析 report_json 失败: {e}")
    
    if record.status == SessionStatus.FAILED:
        error = record.error_message
    
    return DiagnoseResult(
        session_id=record.session_id,
        status=status_enum,
        generated_at=generated_at,
        summary=summary,
        problem_category=record.problem_category if record.problem_category else None,
        severity=record.severity if record.severity else None,
        hypotheses=hypotheses,
        top_hypothesis=top_hypothesis,
        recommended_solutions=recommended_solutions,
        similar_cases=similar_cases,
        next_steps=next_steps,
        escalation_needed=escalation_needed,
        progress=DiagnoseProgress(
            current_step=current_step,
            completed_steps=completed_steps,
            remaining_steps=remaining_steps,
            percentage=percentage,
        ),
        error=error,
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