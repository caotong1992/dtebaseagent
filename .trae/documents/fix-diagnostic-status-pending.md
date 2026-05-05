# 修复诊断任务状态一直为pending的问题

## 问题分析

### 根本原因
`create_diagnose` API端点（diagnose.py 第69-91行）只创建了SessionRecord并设置状态为PENDING，但**没有启动实际的诊断流程**。

当前流程：
```
用户提交诊断请求 → 创建SessionRecord(status=PENDING) → 返回响应
                                                    ↓
                                            任务永远保持PENDING
```

缺失的流程：
- 没有调用 `DTEBaseDiagnosticAgent.diagnose()` 方法
- 没有异步后台任务执行诊断
- 没有状态更新机制（PENDING → RUNNING → COMPLETED/FAILED）

## 修复方案

### 方案：使用FastAPI BackgroundTasks异步执行诊断

修复流程：
```
用户提交诊断请求 → 创建SessionRecord(status=PENDING) → 启动后台诊断任务 → 返回响应
                                                    ↓
                                            后台任务执行：
                                            1. 更新状态为RUNNING
                                            2. 执行诊断流程
                                            3. 更新状态为COMPLETED/FAILED
                                            4. 保存诊断结果
```

## 实施步骤

### 步骤1: 修改diagnose.py导入BackgroundTasks

在 `api/routes/diagnose.py` 添加导入：
```python
from fastapi import BackgroundTasks
```

### 步骤2: 创建后台诊断执行函数

创建 `_run_diagnostic_task` 函数：
```python
async def _run_diagnostic_task(
    session_id: str,
    request: DiagnoseRequest,
    store: SessionStore
):
    # 更新状态为RUNNING
    await store.update(session_id, status=SessionStatus.RUNNING)
    
    try:
        # 获取Agent配置
        agent = get_diagnostic_agent()
        
        # 构建UserInput
        user_input = UserInput(
            description=request.description,
            environment=request.environment,
            symptoms=request.symptoms or [],
            priority=request.priority or "medium"
        )
        
        # 执行诊断
        report = await agent.diagnose(user_input)
        
        # 更新状态为COMPLETED并保存结果
        await store.update(
            session_id,
            status=SessionStatus.COMPLETED,
            problem_category=report.problem_category.value if report.problem_category else "",
            top_hypothesis=report.top_hypothesis.hypothesis.problem if report.top_hypothesis else "",
            confidence=report.top_hypothesis.hypothesis.confidence if report.top_hypothesis else 0.0,
            completed_at=datetime.now()
        )
        
    except Exception as e:
        # 更新状态为FAILED
        await store.update(
            session_id,
            status=SessionStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.now()
        )
```

### 步骤3: 修改create_diagnose添加后台任务

修改 `create_diagnose` 函数：
```python
async def create_diagnose(
    request: DiagnoseRequest,
    background_tasks: BackgroundTasks,
    store: SessionStore = Depends(get_session_store)
) -> DiagnoseCreateResponse:
    session_id = _generate_session_id()
    
    record = SessionRecord(
        session_id=session_id,
        description=request.description,
        cluster_name=request.environment.cluster_name if request.environment else "",
        status=SessionStatus.PENDING,
        created_at=datetime.now(),
    )
    
    await store.create(record)
    
    # 启动后台诊断任务
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
```

### 步骤4: 创建Agent实例管理

添加全局Agent实例：
```python
_diagnostic_agent: DTEBaseDiagnosticAgent | None = None

def get_diagnostic_agent() -> DTEBaseDiagnosticAgent:
    global _diagnostic_agent
    if _diagnostic_agent is None:
        # 从配置获取API Key
        api_key = os.environ.get("OPENAI_API_KEY", "")
        _diagnostic_agent = DTEBaseDiagnosticAgent(api_key=api_key)
    return _diagnostic_agent

def set_diagnostic_agent(agent: DTEBaseDiagnosticAgent) -> None:
    global _diagnostic_agent
    _diagnostic_agent = agent
```

### 步骤5: 修改get_diagnose返回完整结果

更新 `get_diagnose` 函数返回诊断报告内容：
```python
@router.get("/{session_id}")
async def get_diagnose(...) -> DiagnoseResult:
    record = await store.get(session_id)
    if not record:
        raise HTTPException(...)
    
    # 根据状态返回不同结果
    return DiagnoseResult(
        session_id=record.session_id,
        status=_status_to_schema(record.status),
        progress=DiagnoseProgress(...),
        # 添加诊断结果字段
        summary=record.problem_category if record.status == SessionStatus.COMPLETED else "",
        hypotheses=[],  # 可从存储中获取
        recommended_solutions=[],  # 可从存储中获取
    )
```

## 涉及文件

| 文件 | 修改内容 |
|------|----------|
| api/routes/diagnose.py | 添加BackgroundTasks、后台任务函数、Agent实例管理 |
| storage/models.py | 可能需要添加字段存储诊断结果 |
| __main__.py | 初始化Agent实例 |

## 测试验证

1. POST /api/v1/diagnose → 状态应为PENDING，后台任务启动
2. 等待几秒后 GET /api/v1/diagnose/{session_id} → 状态应为RUNNING或COMPLETED
3. 最终状态应为COMPLETED（成功）或FAILED（失败）