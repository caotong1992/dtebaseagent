# DTE Diagnostic Agent 源码总结

## 项目概述

DTEBaseService问题定位AI Agent，用于智能诊断DTEBaseService服务问题，支持跨多个私有集群的运维场景。

**技术栈**: Python 3.14, LangChain 2.15.4, OpenAI API, FastAPI, Click CLI

---

## 模块结构

```
src/dte_diagnostic_agent/
├── agent/          # Agent核心模块
├── api/            # RESTful API接口
├── cli/            # 命令行工具
├── kb/             # 知识库管理
├── prompts/        # Prompt模板
├── storage/        # 数据存储
├── tools/          # 诊断工具集
├── __init__.py     # 包入口
└── __main__.py     # 启动入口
```

---

## 1. Agent核心模块 (agent/)

### 1.1 DTEBaseDiagnosticAgent (core.py)

**核心类**，集成完整诊断流程：

```python
class DTEBaseDiagnosticAgent:
    def __init__(api_key, base_url, model_name, temperature, kb_manager)
    async def diagnose(user_input) -> DiagnosticReport
```

**诊断流程**:
1. 意图解析 → IntentParser
2. 案例检索 → KnowledgeBaseManager
3. 规划生成 → DiagnosticPlanner
4. 工具执行 → 模拟执行诊断步骤
5. 推理分析 → ReasoningEngine
6. 报告生成 → DiagnosticReport

### 1.2 IntentParser (intent_parser.py)

**意图理解模块**，解析用户输入：

```python
class IntentParser:
    async def parse(user_input: UserInput) -> DiagnosticContext
```

**功能**:
- 格式化用户输入
- 调用LLM解析意图
- 提取问题描述、时间范围、环境信息
- 构建DiagnosticContext

### 1.3 DiagnosticPlanner (planner.py)

**规划调度模块**，生成诊断计划：

```python
class DiagnosticPlanner:
    async def generate_plan(context, similar_cases) -> DiagnosticPlan
```

**功能**:
- 基于问题类型生成诊断步骤
- 整合历史案例信息
- 生成默认诊断步骤（SSH连接→日志检查→资源检查→案例搜索）

### 1.4 ReasoningEngine (reasoning.py)

**推理决策模块**，分析问题原因：

```python
class ReasoningEngine:
    async def analyze(context) -> list[Hypothesis]
    async def validate_hypotheses(context, hypotheses) -> list[ValidatedHypothesis]
    def generate_solutions(hypothesis, similar_cases) -> list[Solution]
```

**功能**:
- 规则推理（预定义3条诊断规则）
- LLM推理（调用OpenAI分析）
- 假设排序和验证

**预定义规则**:
- RULE_001: 数据库连接超时
- RULE_002: 性能下降
- RULE_003: 服务不可用

### 1.5 数据模型 (agent/models/)

| 模型 | 文件 | 用途 |
|------|------|------|
| DiagnosticContext | context.py | 诊断上下文（问题描述、环境、症状等） |
| Hypothesis | hypothesis.py | 问题假设（原因、置信度、证据） |
| DiagnosticPlan | plan.py | 诊断计划（步骤列表） |
| DiagnosticReport | report.py | 诊断报告（结果、解决方案） |
| UserInput | input.py | 用户输入 |

---

## 2. API模块 (api/)

### 2.1 FastAPI应用 (main.py)

```python
def create_app(api_keys, session_dir) -> FastAPI
```

**路由**:
- `/api/v1/diagnose` - 诊断接口
- `/api/v1/cases` - 案例库接口
- `/api/v1/clusters` - 集群管理接口
- `/api/v1/health` - 健康检查接口

**中间件**:
- CORS中间件
- AuthMiddleware（API Key认证）

### 2.2 路由模块 (routes/)

| 路由 | 文件 | 端点 |
|------|------|------|
| diagnose.py | diagnose_router | POST/GET/DELETE /diagnose, GET /diagnose/list |
| cases.py | cases_router | GET /cases/search, POST /cases, GET /cases/{id} |
| clusters.py | clusters_router | GET /clusters, GET /clusters/{name}/status |
| health.py | health_router | GET /health, GET /ready, GET /config |

### 2.3 数据模型 (schemas/)

| 模型 | 文件 | 用途 |
|------|------|------|
| diagnose.py | DiagnoseRequest, DiagnoseResult | 诊断请求/响应 |
| cases.py | CaseSearchRequest, CaseResponse | 案例请求/响应 |
| clusters.py | ClusterInfo, ClusterStatus | 集群信息 |
| common.py | PaginationInfo, ErrorResponse | 通用模型 |

---

## 3. CLI模块 (cli/)

### 3.1 CLI入口 (main.py)

```python
@click.group(name="dte-diag")
def main() -> None
```

**命令**:
- `diagnose` - 执行诊断
- `status` - 查询状态
- `history` - 查看历史
- `cancel` - 取消诊断
- `search` - 搜索案例
- `case` - 案例管理（show/save/list）
- `cluster` - 集群管理（list/status/test）
- `config` - 配置管理（show/set/init）

### 3.2 命令实现 (commands/)

| 命令 | 文件 | 功能 |
|------|------|------|
| diagnose.py | 执行诊断 | 支持交互模式、等待、dry-run |
| status.py | 查询状态 | 支持watch模式 |
| history.py | 查看历史 | 支持筛选和分页 |
| cancel.py | 取消诊断 | 取消运行中的诊断 |
| search.py | 搜索案例 | 搜索案例库 |
| case.py | 案例管理 | show/save/list |
| cluster.py | 集群管理 | list/status/test |
| config_cmd.py | 配置管理 | show/set/init |

### 3.3 支撑模块

| 模块 | 文件 | 功能 |
|------|------|------|
| config.py | ConfigManager | YAML配置管理 |
| output.py | OutputFormatter | 输出格式化（table/json/yaml/text/markdown） |
| client.py | APIClient | HTTP API客户端 |

---

## 4. 知识库模块 (kb/)

### 4.1 管理器 (manager.py)

```python
class KnowledgeBaseManager:
    def __init__(config: KnowledgeBaseConfig)
    async def search(query, symptoms, category, top_k) -> list[SearchResult]
    async def get(case_id) -> Case
    async def save(case) -> str
    async def list_all(category, limit) -> list[Case]
    async def delete(case_id) -> bool
    async def reload()
```

**模式切换**:
- `local` → LocalMarkdownKB（本地Markdown文件）
- `remote` → RemoteKBClient（远程API）

### 4.2 接口抽象 (interface.py)

```python
class KnowledgeBaseInterface(ABC):
    async def search() -> list[SearchResult]
    async def get() -> Case
    async def save() -> str
    async def list_all() -> list[Case]
    async def delete() -> bool
    async def reload()
```

### 4.3 本地Markdown适配器 (local_kb.py)

```python
class LocalMarkdownKB(KnowledgeBaseInterface):
    def __init__(config: LocalKBConfig)
```

**功能**:
- 解析Markdown文件（frontmatter + 章节）
- 关键词搜索匹配
- 案例保存为Markdown文件

**Markdown格式**:
```markdown
---
case_id: CASE-001
title: 数据库连接超时
category: database
---
## 问题现象
...
## 解决方案
...
```

### 4.4 远程API适配器 (remote_kb.py)

```python
class RemoteKBClient(KnowledgeBaseInterface):
    def __init__(config: RemoteKBConfig)
```

**功能**:
- HTTP API调用
- API Key认证
- 超时配置

### 4.5 配置模型 (config.py)

```python
class KnowledgeBaseConfig(BaseModel):
    mode: str  # local/remote
    local: LocalKBConfig
    remote: RemoteKBConfig
```

---

## 5. Prompt模板 (prompts/)

| Prompt | 文件 | 用途 |
|--------|------|------|
| INTENT_PROMPT | intent.py | 意图理解，引导LLM输出结构化JSON |
| PLANNING_PROMPT | planning.py | 诊断规划，生成诊断步骤 |
| REASONING_PROMPT | reasoning.py | 推理分析，生成问题假设 |

---

## 6. 存储模块 (storage/)

### 6.1 会话存储 (session_store.py)

```python
class SessionStore:
    def __init__(session_dir: str)
    async def create(record) -> SessionRecord
    async def get(session_id) -> SessionRecord
    async def update(session_id, **updates) -> SessionRecord
    async def delete(session_id) -> bool
    async def list_all(...) -> tuple[list[SessionRecord], int]
    async def list_by_month(year, month) -> list[SessionRecord]
    async def get_statistics(year, month) -> dict
```

**存储机制**: 按自然月存储CSV文件

**文件格式**: `sessions_YYYY-MM.csv`

### 6.2 数据模型 (models.py)

```python
class SessionRecord(BaseModel):
    session_id, description, cluster_name, status, created_at...
    
class SessionStatus(Enum):
    PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
```

---

## 7. 工具模块 (tools/)

使用LangChain StructuredTool定义的诊断工具：

| 工具 | 文件 | 功能 |
|------|------|------|
| SSHConnectTool | ssh.py | SSH连接 |
| LogAnalysisTool | log.py | 日志分析 |
| DatabaseQueryTool | database.py | 数据库查询 |
| ResourceMonitorTool | resource.py | 指标采集 |
| K8sOperationTool | k8s.py | K8s操作 |
| ConfigCheckTool | config.py | 配置检查 |
| NetworkDiagTool | network.py | 网络诊断 |
| CaseSearchTool | case.py | 案例检索 |

**工具定义示例**:
```python
SSHConnectTool = StructuredTool.from_function(
    coroutine=_ssh_connect,
    name="ssh_connect",
    description="连接到目标服务器",
    args_schema=SSHConnectInput
)
```

---

## 8. 启动入口 (__main__.py)

**本地部署入口**，支持命令行参数：

```bash
python -m dte_diagnostic_agent --config config.yaml --port 8080
```

**参数**:
- `--config` - 配置文件路径
- `--port` - 服务端口
- `--host` - 监听地址
- `--api-key` - API密钥
- `--log-level` - 日志级别
- `--dry-run` - 仅验证配置

---

## 9. 完整诊断流程

```
用户输入 (UserInput)
    │
    ▼
IntentParser.parse()
    │ 提取问题描述、时间、环境
    ▼
DiagnosticContext
    │
    ▼
KnowledgeBaseManager.search()
    │ 检索相似历史案例
    ▼
DiagnosticPlanner.generate_plan()
    │ 生成诊断步骤
    ▼
DiagnosticPlan
    │
    ▼
执行工具步骤
    │ ssh_connect → log_analysis → resource_monitor
    ▼
ReasoningEngine.analyze()
    │ 规则推理 + LLM推理
    ▼
Hypothesis列表
    │
    ▼
报告生成
    │ 解决方案 + 下一步建议
    ▼
DiagnosticReport
```

---

## 10. 关键设计决策

1. **双模式知识库**: 本地Markdown + 远程API，配置切换
2. **按月存储**: CSV文件按自然月分片存储诊断记录
3. **规则+LLM推理**: 预定义规则快速匹配，LLM深度分析
4. **LangChain工具**: StructuredTool标准化工具定义
5. **CLI+API双接口**: 命令行和RESTful API两种使用方式
6. **优雅关闭**: systemd服务支持SIGTERM信号处理