# DTE Diagnostic Agent 源码总结

## 项目概述

DTEBaseService问题定位AI Agent，用于智能诊断DTEBaseService服务问题，支持跨多个私有集群的运维场景。

**技术栈**: Python 3.14, LangChain 2.15.4, OpenAI API, FastAPI, Click CLI

---

## 项目目录结构

```
d:\code\dtebaseagent/
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略配置
├── README.md                 # 项目说明文档
├── AGENTS.md                 # 源码总结文档
├── config.yaml               # 主配置文件
├── config.yaml.example       # 配置文件示例
├── design.md                 # 设计文档
├── requirements.txt          # Python 依赖
│
├── bin/                      # 启动停止脚本
│   ├── start.bat             # Windows 启动脚本
│   ├── start.sh              # Linux 启动脚本
│   ├── stop.bat              # Windows 停止脚本
│   └── stop.sh               # Linux 停止脚本
│
├── cases/                    # 案例库目录
│   ├── collector_task/       # Collector 任务案例
│   │   ├── CASE-020-collector_task_failed.md
│   │   ├── CASE-021-collector_task_failed_csm.loading.error.md
│   │   └── CASE-022-collector_task_failed_csm.task.timeout.md
│   ├── database/             # 数据库案例
│   │   ├── CASE-001-db-connection-timeout.md
│   │   └── CASE-002-db-slow-query.md
│   └── network/              # 网络案例
│   │   └── CASE-010-network-timeout.md
│
├── deployment/               # 部署配置
│   └── README.md
│
├── docs/                     # 文档目录
│   ├── api.md                # API 文档
│   └── cli.md                # CLI 文档
│
├── src/                      # 源代码
│   └── dte_diagnostic_agent/
│
└── test/                     # 测试脚本
│   └── call_api.py
```

---

## 模块结构

```
src/dte_diagnostic_agent/
├── agent/          # Agent核心模块
│   ├── core.py     # 诊断流程主类
│   ├── intent_parser.py  # 意图解析
│   ├── planner.py  # 诊断规划
│   ├── reasoning.py  # 推理分析
│   ├── case_step_parser.py  # 案例步骤解析器
│   ├── info_extractor.py  # 关键信息提取器
│   └── models/     # 数据模型
│       ├── context.py     # 诊断上下文
│       ├── hypothesis.py  # 问题假设
│       ├── input.py       # 用户输入
│       ├── plan.py        # 诊断计划
│       ├── report.py      # 诊断报告
│       └── parsed_step.py # 解析步骤模型
│
├── api/            # RESTful API接口
│   ├── main.py     # FastAPI 应用
│   ├── middleware/ # 中间件
│   │   └ auth.py   # API Key认证
│   ├── routes/     # 路由模块
│   │   ├── cases.py    # 案例路由
│   │   └ diagnose.py  # 诊断路由
│   └── schemas/    # 数据模型
│       ├── cases.py    # 案例模型
│       ├── clusters.py # 集群模型
│       ├── common.py   # 通用模型
│       └ diagnose.py  # 诊断模型
│
├── cli/            # 命令行工具
│   ├── main.py     # CLI 入口
│   ├── client.py   # HTTP API客户端
│   ├── config.py   # 配置管理
│   ├── output.py   # 输出格式化
│   └ commands/     # 命令实现
│       ├── cancel.py   # 取消诊断
│       ├── case.py     # 案例管理
│       ├── cluster.py  # 集群管理
│       ├── config_cmd.py  # 配置管理
│       ├── diagnose.py  # 执行诊断
│       ├── history.py   # 历史记录
│       ├── search.py    # 搜索案例
│       ├── status.py    # 状态查询
│
├── kb/             # 知识库管理
│   ├── config.py   # 配置模型
│   ├── interface.py  # 接口抽象
│   ├── keyword_extractor.py  # 关键词提取
│   ├── local_kb.py  # 本地Markdown适配器
│   ├── manager.py   # 知识库管理器
│   ├── models.py    # 数据模型
│   ├── query_processor.py  # 查询预处理器
│   ├── remote_kb.py # 远程API适配器
│   └ translator.py  # 翻译服务
│
├── prompts/        # Prompt模板
│   ├── intent.py   # 意图理解
│   ├── planning.py # 诊断规划
│   ├── reasoning.py  # 推理分析
│   └── case_step.py  # 案例步骤解析
│
├── storage/        # 数据存储
│   ├── models.py   # 数据模型
│   └ session_store.py  # 会话存储
│
├── tools/          # 诊断工具集
│   ├── case.py     # 案例检索工具
│   ├── config.py   # 配置检查工具
│   ├── database.py # 数据库查询工具
│   ├── k8s.py      # K8s操作工具
│   ├── log.py      # 日志分析工具
│   ├── network.py  # 网络诊断工具
│   ├── resource.py # 指标采集工具
│   ├── ssh.py      # SSH连接工具
│
├── __init__.py     # 包入口
└── __main__.py     # 启动入口
```

---

## 1. Agent核心模块 (agent/)

### 1.1 DTEBaseDiagnosticAgent (core.py)

**核心类**，集成完整诊断流程：

```python
class DTEBaseDiagnosticAgent:
    def __init__(
        api_key, 
        base_url, 
        model_name, 
        temperature, 
        kb_manager, 
        query_processor_config,
        case_step_parser  # 新增参数
    )
    async def diagnose(user_input, session_id) -> DiagnosticReport
```

**诊断流程**:
1. 意图解析 → IntentParser
2. 案例检索 → KnowledgeBaseManager（支持查询预处理）
3. 案例步骤解析 → CaseStepParser（新增）
4. 迭代检索检测 → has_iterative_search（新增）
5. 规划生成 → DiagnosticPlanner
6. 工具执行 → 模拟执行诊断步骤
7. 推理分析 → ReasoningEngine
8. 报告生成 → DiagnosticReport

**新增功能**:
- session_id 参数传递，保持日志一致性
- collected_data 存储步骤执行结果
- 迭代检索流程支持（引导型案例）

### 1.2 IntentParser (intent_parser.py)

**意图理解模块**，解析用户输入：

```python
class IntentParser:
    async def parse(user_input: UserInput, session_id: str) -> DiagnosticContext
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

### 1.5 CaseStepParser (case_step_parser.py)

**案例步骤解析器**，将案例分析过程转换为结构化步骤：

```python
class CaseStepParser:
    def __init__(llm: ChatOpenAI)
    async def parse_case_analysis(case: Case) -> ParsedAnalysis
    def to_diagnostic_steps(parsed, collected_data) -> list[DiagnosticStep]
    def _replace_template_vars(params, collected_data) -> dict
    def detect_iterative_search(parsed) -> bool
```

**功能**:
- 使用 LLM 解析案例的分析过程章节
- 提取结构化的诊断步骤
- 支持模板变量替换（{task_id}, {last_error_code}）
- 检测是否需要迭代检索
- 内置缓存机制避免重复调用 LLM

### 1.6 KeyInfoExtractor (info_extractor.py)

**关键信息提取器**，从工具执行结果提取关键信息：

```python
class KeyInfoExtractor:
    ERROR_CODE_PATTERN = r'(csm\.[a-z]+\.[a-z]+|data\.[a-z]+\.[a-z]+|send\.[a-z]+\.[a-z]+|task\.[a-z]+\.[a-z]+)'
    
    def extract_last_error_code(result: dict) -> str | None
    def extract_task_id(context: DiagnosticContext) -> str | None
```

**功能**:
- 从数据库查询结果提取 last_error_code
- 从问题描述提取 task_id
- 支持正则匹配错误码模式（csm.xxx.xxx 格式）

### 1.7 数据模型 (agent/models/)

| 模型 | 文件 | 用途 |
|------|------|------|
| DiagnosticContext | context.py | 诊断上下文（问题描述、环境、症状、collected_data） |
| Hypothesis | hypothesis.py | 问题假设（原因、置信度、证据） |
| DiagnosticPlan | plan.py | 诊断计划（步骤列表） |
| DiagnosticReport | report.py | 诊断报告（结果、解决方案） |
| UserInput | input.py | 用户输入 |
| StepActionType | parsed_step.py | 步骤动作类型枚举（TOOL_EXECUTE, CASE_SEARCH, MANUAL_CHECK, DECISION） |
| ParsedStep | parsed_step.py | 解析后的步骤模型（step_number, action_type, tool_name, parameters, description, next_action, template_vars） |
| ParsedAnalysis | parsed_step.py | 解析后的分析模型（case_id, steps, has_iterative_search） |

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

### 2.3 数据模型 (schemas/)

| 模型 | 文件 | 用途 |
|------|------|------|
| diagnose.py | DiagnoseRequest, DiagnoseResult | 诊断请求/响应 |
| cases.py | CaseSearchRequest, CaseResponse | 案例请求/响应 |
| clusters.py | ClusterInfo, ClusterStatus | 集群信息 |
| common.py | PaginationInfo, ErrorResponse | 通用模型 |

### 2.4 中间件 (middleware/)

| 模块 | 文件 | 功能 |
|------|------|------|
| auth.py | AuthMiddleware | API Key认证中间件 |

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
    async def search(query, keywords, symptoms, category, top_k) -> list[SearchResult]
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
- 多关键词搜索匹配（支持中英文双语）
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
## 分析过程
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
    query_processor: QueryProcessorConfig | None
```

### 4.6 查询预处理模块

**KeywordExtractor** (keyword_extractor.py)
- 提取中文词组、英文单词、专业术语
- 识别 PascalCase 格式的技术术语

**TranslatorService** (translator.py)
- 使用 LLM 进行中英文双向翻译
- 内置缓存机制避免重复调用

**QueryProcessor** (query_processor.py)
- 整合关键词提取和翻译
- 输出双语关键词列表（chinese_keywords, english_keywords, all_keywords）
- 专业术语保留原值不翻译

```python
class QueryProcessor:
    async def process(query: str) -> PreprocessedQuery

@dataclass
class PreprocessedQuery:
    original: str
    chinese_keywords: list[str]
    english_keywords: list[str]
    all_keywords: list[str]
```

---

## 5. Prompt模板 (prompts/)

| Prompt | 文件 | 用途 |
|--------|------|------|
| INTENT_PROMPT | intent.py | 意图理解，引导LLM输出结构化JSON |
| PLANNING_PROMPT | planning.py | 诊断规划，生成诊断步骤 |
| REASONING_PROMPT | reasoning.py | 推理分析，生成问题假设 |
| CASE_STEP_PARSE_PROMPT | case_step.py | 案例步骤解析，引导LLM将分析过程转换为JSON结构 |

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

## 9. 启动脚本 (bin/)

### 9.1 Windows脚本

**start.bat** - 启动服务
- 用法: start.bat [port]
- 默认端口: 8080
- 功能: 自动检测并重启已有进程

**stop.bat** - 停止服务
- 用法: stop.bat [port]
- 功能: 通过端口查找并停止进程

### 9.2 Linux脚本

**start.sh** - 启动服务
- 用法: ./start.sh [port]
- 默认端口: 8080
- PID文件: bin/dte-diag.pid
- 日志输出: logs/agent.log

**stop.sh** - 停止服务
- 用法: ./stop.sh [port]
- 功能: 通过PID文件或端口停止进程

---

## 10. 案例库目录 (cases/)

| 目录 | 案例 |
|------|------|
| database/ | CASE-001 数据库连接超时, CASE-002 数据库慢查询 |
| network/ | CASE-010 网络超时 |
| collector_task/ | CASE-020 Collector任务失败, CASE-021 csm.loading.error, CASE-022 csm.task.timeout |

---

## 11. 完整诊断流程

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
QueryProcessor.process()
    │ 关键词提取 + 中英文翻译
    ▼
KnowledgeBaseManager.search()
    │ 多语言关键词检索相似案例
    ▼
CaseStepParser.parse_case_analysis()
    │ 解析案例分析过程
    ▼
检测迭代检索需求 (has_iterative_search)
    │
    ├─ 有迭代需求 ────────────────────────┐
    │                                      │
    │  _build_plan_from_parsed_cases()     │
    │      │ 从解析案例生成计划             │
    │      ▼                               │
    │  执行 tool_execute 步骤              │
    │      │ 如 database_query             │
    │      ▼                               │
    │  KeyInfoExtractor.extract()          │
    │      │ 提取 last_error_code           │
    │      ▼                               │
    │  KnowledgeBaseManager.search(error_code)
    │      │ 第二轮精确检索                 │
    │      ▼                               │
    │  更新诊断计划                         │
    │                                      │
    └──────────────────────────────────────┘
    │
    ▼
执行诊断步骤
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

## 12. 关键设计决策

1. **双模式知识库**: 本地Markdown + 远程API，配置切换
2. **按月存储**: CSV文件按自然月分片存储诊断记录
3. **规则+LLM推理**: 预定义规则快速匹配，LLM深度分析
4. **LangChain工具**: StructuredTool标准化工具定义
5. **CLI+API双接口**: 命令行和RESTful API两种使用方式
6. **优雅关闭**: systemd服务支持SIGTERM信号处理
7. **查询预处理**: 关键词提取 + 中英文双向翻译，提高知识库检索可靠性
8. **启动脚本**: bin 目录提供 Windows/Linux 启动停止脚本
9. **案例步骤解析器**: 使用 LLM 将案例的分析过程转换为结构化的可执行步骤
10. **迭代检索机制**: 支持引导型案例，先执行步骤获取信息，再用新信息进行第二轮检索
11. **模板变量系统**: 支持在案例中定义模板变量（{task_id}, {last_error_code}），运行时动态替换
12. **关键信息提取**: 使用正则表达式从工具执行结果提取关键信息（错误码、任务ID等）