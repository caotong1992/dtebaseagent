# DTE Diagnostic Agent - Code Wiki

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [模块详解](#3-模块详解)
4. [关键类与函数](#4-关键类与函数)
5. [依赖关系](#5-依赖关系)
6. [数据模型](#6-数据模型)
7. [配置说明](#7-配置说明)
8. [运行方式](#8-运行方式)
9. [API接口](#9-api接口)
10. [CLI命令](#10-cli命令)
11. [工具集](#11-工具集)
12. [知识库管理](#12-知识库管理)
13. [诊断流程](#13-诊断流程)
14. [扩展性设计](#14-扩展性设计)

---

## 1. 项目概述

### 1.1 项目定位

DTE Diagnostic Agent 是一个智能运维诊断 AI Agent，专门用于 DTEBaseService 服务的问题定位和诊断。系统支持跨多个私有集群的运维场景，能够自动分析日志、数据库、系统指标等多维数据，输出问题可能原因和解决建议。

### 1.2 技术栈

| 技术组件 | 版本/说明 |
|---------|----------|
| Python | 3.14 |
| LangChain | 0.3.0+ |
| OpenAI API | 兼容接口 |
| FastAPI | Web框架 |
| Click | CLI框架 |
| Pydantic | 数据验证 |
| asyncssh | SSH连接 |
| asyncpg | PostgreSQL |
| kubernetes | K8s客户端 |

### 1.3 核心能力

- 接收用户描述的问题现象、时间范围和环境信息
- 查询历史维护案例库进行相似案例匹配（支持中英文双语检索）
- 自动连接目标环境进行诊断
- 分析日志、数据库、系统指标等多维数据
- 输出问题可能原因和解决建议

---

## 2. 整体架构

### 2.1 架构层次图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户交互层                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │       CLI工具       │  │       API接口       │                  │
│  │    (Click框架)      │  │    (FastAPI)       │                  │
│  └─────────────────────┘  └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent 核心层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 意图理解模块  │  │ 规划调度模块  │  │ 推理决策模块  │               │
│  │IntentParser  │  │DiagnosticPlan│  │ReasoningEng  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 上下文管理   │  │  知识库管理   │  │ 结果生成模块  │               │
│  │DiagnosticCtx │  │KnowledgeBase │  │DiagnosticRep │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         工具执行层                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │SSH连接  │ │日志分析 │ │数据库查询│ │指标采集 │ │案例检索 │      │
│  │ssh.py   │ │log.py   │ │database │ │resource │ │case.py  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │配置检查 │ │进程管理 │ │网络诊断 │ │存储检查 │ │K8s操作  │      │
│  │config.py│ │k8s.py   │ │network  │ │         │ │         │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         数据存储层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 历史案例库   │  │  会话存储    │  │  配置仓库    │               │
│  │ cases/*.md   │  │ sessions/*.csv│  │ config.yaml │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 项目目录结构

```
dte_diagnostic_agent/
├── agent/          # Agent核心模块
│   ├── core.py     # 诊断流程主类 DTEBaseDiagnosticAgent
│   ├── intent_parser.py  # 意图解析 IntentParser
│   ├── planner.py  # 诊断规划 DiagnosticPlanner
│   ├── reasoning.py  # 推理分析 ReasoningEngine
│   └── models/     # 数据模型
│       ├── context.py     # DiagnosticContext
│       ├── hypothesis.py  # Hypothesis, ValidatedHypothesis
│       ├── input.py       # UserInput
│       ├── plan.py        # DiagnosticPlan, DiagnosticStep
│       └── report.py      # DiagnosticReport, Solution
│
├── api/            # RESTful API接口
│   ├── main.py     # FastAPI 应用 create_app()
│   ├── middleware/ # 中间件
│   │   └ auth.py   # AuthMiddleware API Key认证
│   ├── routes/     # 路由模块
│   │   ├── cases.py    # cases_router 案例路由
│   │   └ diagnose.py  # diagnose_router 诊断路由
│   └── schemas/    # 数据模型
│       ├── cases.py    # CaseSearchRequest, CaseResponse
│       ├── clusters.py # ClusterInfo, ClusterStatus
│       ├── common.py   # PaginationInfo, ErrorResponse
│       └ diagnose.py  # DiagnoseRequest, DiagnoseResult
│
├── cli/            # 命令行工具
│   ├── main.py     # CLI入口 dte-diag
│   ├── client.py   # APIClient HTTP客户端
│   ├── config.py   # ConfigManager 配置管理
│   ├── output.py   # OutputFormatter 输出格式化
│   └ commands/     # 命令实现
│       ├── cancel.py   # cancel 取消诊断
│       ├── case.py     # case show/save/list
│       ├── cluster.py  # cluster list/status/test
│       ├── config_cmd.py  # config show/set/init
│       ├── diagnose.py  # diagnose 执行诊断
│       ├── history.py   # history 历史记录
│       ├── search.py    # search 搜索案例
│       ├── status.py    # status 状态查询
│
├── kb/             # 知识库管理
│   ├── config.py   # KnowledgeBaseConfig 配置模型
│   ├── interface.py  # KnowledgeBaseInterface 接口抽象
│   ├── keyword_extractor.py  # KeywordExtractor 关键词提取
│   ├── local_kb.py  # LocalMarkdownKB 本地Markdown适配器
│   ├── manager.py   # KnowledgeBaseManager 知识库管理器
│   ├── models.py    # Case, SearchResult 数据模型
│   ├── query_processor.py  # QueryProcessor 查询预处理器
│   ├── remote_kb.py # RemoteKBClient 远程API适配器
│   └ translator.py  # TranslatorService 翻译服务
│
├── prompts/        # Prompt模板
│   ├── intent.py   # INTENT_PROMPT 意图理解
│   ├── planning.py # PLANNING_PROMPT 诊断规划
│   └ reasoning.py  # REASONING_PROMPT 推理分析
│
├── storage/        # 数据存储
│   ├── models.py   # SessionRecord, SessionStatus
│   └ session_store.py  # SessionStore 会话存储
│
├── tools/          # 诊断工具集
│   ├── case.py     # CaseSearchTool 案例检索
│   ├── config.py   # ConfigCheckTool 配置检查
│   ├── database.py # DatabaseQueryTool 数据库查询
│   ├── k8s.py      # K8sOperationTool K8s操作
│   ├── log.py      # LogAnalysisTool 日志分析
│   ├── network.py  # NetworkDiagTool 网络诊断
│   ├── resource.py # ResourceMonitorTool 指标采集
│   ├── ssh.py      # SSHConnectTool SSH连接
│
├── __init__.py     # 包入口 __version__
└── __main__.py     # 启动入口 main()
```

---

## 3. 模块详解

### 3.1 Agent核心模块 (agent/)

#### 3.1.1 DTEBaseDiagnosticAgent (core.py)

**职责**: 诊断流程主控制器，协调各模块完成完整诊断流程。

**核心方法**:

| 方法 | 功能 | 返回类型 |
|------|------|----------|
| `__init__()` | 初始化LLM、解析器、规划器、推理引擎、知识库 | - |
| `diagnose(user_input)` | 执行完整诊断流程 | DiagnosticReport |
| `_search_similar_cases()` | 搜索相似历史案例 | list[Case] |
| `_execute_step()` | 执行诊断步骤 | dict |
| `_generate_report()` | 生成诊断报告 | DiagnosticReport |

**诊断流程**:
```
用户输入 → IntentParser.parse() → DiagnosticContext
         → QueryProcessor.process() → 双语关键词
         → KnowledgeBaseManager.search() → 相似案例
         → DiagnosticPlanner.generate_plan() → DiagnosticPlan
         → 执行诊断步骤 → 收集证据
         → ReasoningEngine.analyze() → Hypothesis列表
         → ReasoningEngine.validate_hypotheses() → ValidatedHypothesis
         → 生成DiagnosticReport
```

#### 3.1.2 IntentParser (intent_parser.py)

**职责**: 解析用户输入，提取关键信息构建诊断上下文。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `parse(user_input)` | 解析用户输入返回DiagnosticContext |
| `_format_input()` | 格式化用户输入为文本 |
| `_parse_response()` | 解析LLM响应JSON |
| `_build_time_range()` | 构建时间范围对象 |
| `_build_environment()` | 构建环境信息对象 |

**提取信息**:
- problem_description: 问题描述
- time_range: 时间范围 (start, end)
- environment: 环境信息 (cluster_name, node_info, service_name)
- symptoms: 症状列表
- priority: 优先级 (critical/high/medium/low)
- category: 问题类别

#### 3.1.3 DiagnosticPlanner (planner.py)

**职责**: 根据问题类型生成诊断计划。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `generate_plan(context, similar_cases)` | 生成诊断计划 |
| `_format_similar_cases()` | 格式化相似案例文本 |
| `_build_steps()` | 构建诊断步骤列表 |
| `_get_default_steps()` | 获取默认诊断步骤 |

**默认诊断步骤**:
1. connect_server (ssh_connect)
2. check_logs (log_analysis)
3. check_resources (resource_monitor)
4. search_cases (case_search)

#### 3.1.4 ReasoningEngine (reasoning.py)

**职责**: 分析诊断数据，生成问题假设。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `analyze(context)` | 分析上下文生成假设列表 |
| `_llm_reasoning()` | LLM推理生成假设 |
| `validate_hypotheses()` | 验证假设 |
| `generate_solutions()` | 生成解决方案 |
| `_rank_hypotheses()` | 按置信度排序假设 |

**预定义诊断规则**:

| 规则ID | 名称 | 匹配症状 | 置信度 |
|--------|------|----------|--------|
| RULE_001 | 数据库连接超时 | 超时、连接失败、timeout | 0.75 |
| RULE_002 | 性能下降 | 慢、性能、响应缓慢 | 0.70 |
| RULE_003 | 服务不可用 | 不可用、宕机、crash | 0.80 |

---

### 3.2 API模块 (api/)

#### 3.2.1 FastAPI应用 (main.py)

**职责**: 提供RESTful API服务入口。

**核心函数**:

| 函数 | 功能 |
|------|------|
| `create_app()` | 创建并配置FastAPI应用 |
| `lifespan()` | 应用生命周期管理 |

**路由注册**:
- `/api/v1/diagnose` - diagnose_router
- `/api/v1/cases` - cases_router

**中间件**:
- CORSMiddleware: 跨域支持
- AuthMiddleware: API Key认证

#### 3.2.2 路由模块 (routes/)

**diagnose_router** (diagnose.py):

| 端点 | 方法 | 功能 |
|------|------|------|
| `/diagnose` | POST | 创建诊断任务 |
| `/diagnose/{id}` | GET | 查询诊断状态 |
| `/diagnose/{id}` | DELETE | 取消诊断任务 |
| `/diagnose/list` | GET | 诊断任务列表 |

**cases_router** (cases.py):

| 端点 | 方法 | 功能 |
|------|------|------|
| `/cases/search` | GET | 搜索案例库 |
| `/cases` | POST | 创建新案例 |
| `/cases/{id}` | GET | 获取案例详情 |

---

### 3.3 CLI模块 (cli/)

#### 3.3.1 CLI入口 (main.py)

**职责**: 提供命令行工具入口。

**命令结构**:

```
dte-diag
├── diagnose      # 执行诊断
├── status        # 查询状态
├── history       # 历史记录
├── cancel        # 取消诊断
├── search        # 搜索案例
├── case          # 案例管理
│   ├── show      # 查看案例
│   ├── save      # 保存案例
│   └── list      # 列出案例
├── cluster       # 集群管理
│   ├── list      # 列出集群
│   ├── status    # 集群状态
│   └── test      # 测试连接
└── config        # 配置管理
    ├── show      # 查看配置
    ├── set       # 设置配置
    └── init      # 初始化配置
```

**全局选项**:
- `--config`: 配置文件路径
- `--api-url`: API服务地址
- `--api-key`: API认证密钥
- `--output`: 输出格式 (table/json/yaml/text/markdown)
- `--verbose`: 详细输出
- `--quiet`: 静默模式

---

### 3.4 知识库模块 (kb/)

#### 3.4.1 KnowledgeBaseManager (manager.py)

**职责**: 知识库管理器，根据配置选择实现。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `search(query, keywords)` | 搜索案例 |
| `get(case_id)` | 获取案例 |
| `save(case)` | 保存案例 |
| `list_all()` | 列出所有案例 |
| `delete(case_id)` | 删除案例 |
| `reload()` | 重载案例库 |

**模式切换**:
- `local` → LocalMarkdownKB
- `remote` → RemoteKBClient

#### 3.4.2 LocalMarkdownKB (local_kb.py)

**职责**: 本地Markdown文件知识库实现。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `_load_index()` | 加载所有案例文件 |
| `_parse_case_file()` | 解析Markdown案例 |
| `_parse_frontmatter()` | 解析YAML前置数据 |
| `_parse_sections()` | 解析Markdown章节 |
| `search()` | 多关键词搜索匹配 |

**Markdown格式**:
```markdown
---
case_id: CASE-001
title: 数据库连接超时
category: database
severity: high
tags: [database, connection, timeout]
---
## 问题现象
数据库连接频繁超时，用户登录失败。

## 症状列表
- 连接超时
- 服务响应缓慢

## 解决方案
1. 增加连接池大小
2. 设置连接超时时间
```

#### 3.4.3 QueryProcessor (query_processor.py)

**职责**: 查询预处理器，提取关键词并进行中英文翻译。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `process(query)` | 处理查询返回双语关键词 |
| `_extract_keywords()` | 提取关键词 |
| `_translate_keywords()` | 翻译关键词 |
| `_merge_and_deduplicate()` | 合并去重关键词 |

**输出结构**:
```python
PreprocessedQuery:
    original: str              # 原始查询
    chinese_keywords: list     # 中文关键词
    english_keywords: list     # 英文关键词
    all_keywords: list         # 合并关键词
```

**技术术语保留**:
- DTEBaseService, PostgreSQL, MySQL, Redis
- Kubernetes, K8s, Docker, API, REST
- HTTP, HTTPS, TCP, UDP, IP, DNS
- CPU, Memory, RAM, GPU, SSD
- JWT, OAuth, OIDC, LDAP

---

### 3.5 存储模块 (storage/)

#### 3.5.1 SessionStore (session_store.py)

**职责**: 诊断会话存储，按月存储CSV文件。

**核心方法**:

| 方法 | 功能 |
|------|------|
| `create(record)` | 创建会话记录 |
| `get(session_id)` | 获取会话 |
| `update(session_id, **updates)` | 更新会话 |
| `delete(session_id)` | 删除会话 |
| `list_all()` | 列出所有会话 |
| `list_by_month()` | 按月列出会话 |
| `get_statistics()` | 获取统计信息 |

**存储机制**:
- 文件格式: `sessions_YYYY-MM.csv`
- 存储路径: `{session_dir}/sessions_YYYY-MM.csv`
- 当前月缓存: 内存缓存当前月数据

---

### 3.6 工具模块 (tools/)

**职责**: 定义诊断工具，使用LangChain StructuredTool。

| 工具 | 文件 | 功能 |
|------|------|------|
| SSHConnectTool | ssh.py | SSH连接到目标服务器 |
| LogAnalysisTool | log.py | 分析服务日志 |
| DatabaseQueryTool | database.py | 查询数据库状态 |
| ResourceMonitorTool | resource.py | 采集系统指标 |
| K8sOperationTool | k8s.py | Kubernetes操作 |
| ConfigCheckTool | config.py | 配置检查 |
| NetworkDiagTool | network.py | 网络诊断 |
| CaseSearchTool | case.py | 案例检索 |

---

## 4. 关键类与函数

### 4.1 核心类

#### DTEBaseDiagnosticAgent

```python
class DTEBaseDiagnosticAgent:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model_name: str = "gpt-4o",
        temperature: float = 0.1,
        kb_manager: KnowledgeBaseManager | None = None,
        query_processor_config: QueryProcessorConfig | None = None
    )
    
    async def diagnose(self, user_input: UserInput) -> DiagnosticReport
```

#### IntentParser

```python
class IntentParser:
    def __init__(self, llm: ChatOpenAI)
    
    async def parse(self, user_input: UserInput) -> DiagnosticContext
```

#### DiagnosticPlanner

```python
class DiagnosticPlanner:
    def __init__(self, llm: ChatOpenAI)
    
    async def generate_plan(
        self,
        context: DiagnosticContext,
        similar_cases: list[Case]
    ) -> DiagnosticPlan
```

#### ReasoningEngine

```python
class ReasoningEngine:
    def __init__(self, llm: ChatOpenAI)
    
    async def analyze(self, context: DiagnosticContext) -> list[Hypothesis]
    
    async def validate_hypotheses(
        self,
        context: DiagnosticContext,
        hypotheses: list[Hypothesis]
    ) -> list[ValidatedHypothesis]
    
    def generate_solutions(
        self,
        hypothesis: Hypothesis,
        similar_cases: list
    ) -> list[Solution]
```

#### KnowledgeBaseManager

```python
class KnowledgeBaseManager:
    def __init__(self, config: KnowledgeBaseConfig)
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10,
        keywords: list[str] | None = None
    ) -> list[SearchResult]
```

#### SessionStore

```python
class SessionStore:
    def __init__(self, session_dir: str = "./data/sessions")
    
    async def create(self, record: SessionRecord) -> SessionRecord
    async def get(self, session_id: str) -> SessionRecord | None
    async def update(self, session_id: str, **updates) -> SessionRecord | None
```

### 4.2 核心函数

#### create_app (api/main.py)

```python
def create_app(
    api_keys: list[str] | None = None,
    session_dir: str = "./data/sessions",
    config: AppConfig | None = None,
    logger: logging.Logger | None = None
) -> FastAPI
```

#### main (__main__.py)

```python
def main() -> int:
    """本地部署入口函数"""
    
def load_config(config_path: Path | None = None) -> AppConfig
def setup_logging(log_level: str, log_file: str | None = None) -> None
def validate_config(config: AppConfig) -> list[str]
```

---

## 5. 依赖关系

### 5.1 模块依赖图

```
agent/core.py
    ├── agent/intent_parser.py
    │       └── prompts/intent.py
    ├── agent/planner.py
    │       └── prompts/planning.py
    ├── agent/reasoning.py
    │       └── prompts/reasoning.py
    ├── agent/models/*
    │       ├── input.py
    │       ├── context.py
    │       ├── plan.py
    │       ├── hypothesis.py
    │       └ report.py
    ├── kb/manager.py
    │       ├── kb/interface.py
    │       ├── kb/local_kb.py
    │       ├── kb/remote_kb.py
    │       ├── kb/models.py
    │       ├── kb/query_processor.py
    │       │       ├── kb/keyword_extractor.py
    │       │       └ kb/translator.py
    │       └── kb/config.py
    └── langchain_openai.ChatOpenAI

api/main.py
    ├── api/routes/diagnose.py
    ├── api/routes/cases.py
    ├── api/middleware/auth.py
    ├── storage/session_store.py
    └── kb/config.py

cli/main.py
    ├── cli/config.py
    ├── cli/output.py
    ├── cli/client.py
    └── cli/commands/*
```

### 5.2 外部依赖

| 依赖包 | 用途 |
|--------|------|
| langchain | Agent框架 |
| langchain-openai | OpenAI LLM接口 |
| langchain-core | 核心组件 |
| openai | OpenAI API客户端 |
| fastapi | Web框架 |
| uvicorn | ASGI服务器 |
| click | CLI框架 |
| rich | 终端输出美化 |
| pydantic | 数据验证 |
| asyncssh | SSH连接 |
| asyncpg | PostgreSQL异步驱动 |
| kubernetes | K8s客户端 |
| pyyaml | YAML解析 |
| python-dotenv | 环境变量 |
| python-frontmatter | Markdown解析 |

---

## 6. 数据模型

### 6.1 Agent数据模型

#### UserInput (agent/models/input.py)

```python
class UserInput(BaseModel):
    description: str                    # 问题描述
    time_range_start: datetime | None   # 开始时间
    time_range_end: datetime | None     # 结束时间
    environment: ClusterInfo | None     # 环境信息
    symptoms: list[str] = []            # 症状列表
    priority: str = "medium"            # 优先级
```

#### DiagnosticContext (agent/models/context.py)

```python
class DiagnosticContext(BaseModel):
    session_id: str                     # 会话ID
    problem_description: str            # 问题描述
    time_range: TimeRange               # 时间范围
    environment: ClusterInfo            # 环境信息
    symptoms: list[str]                 # 症状列表
    priority: Severity                  # 优先级
    category: ProblemCategory | None    # 问题类别
    collected_data: dict                # 收集的数据
    metadata: dict                      # 元数据
```

#### DiagnosticPlan (agent/models/plan.py)

```python
class DiagnosticStep(BaseModel):
    name: str                           # 步骤名称
    description: str                    # 步骤描述
    tool_name: str                      # 工具名称
    parameters: dict                    # 参数
    priority: int                       # 优先级

class DiagnosticPlan(BaseModel):
    steps: list[DiagnosticStep]         # 步骤列表
    estimated_duration: int             # 预估时长
```

#### Hypothesis (agent/models/hypothesis.py)

```python
class Hypothesis(BaseModel):
    id: str                             # 假设ID
    problem: str                        # 问题描述
    confidence: float                   # 置信度 (0-1)
    evidence: list[str]                 # 支持证据
    actions: list[str]                  # 建议操作
    source: str                         # 来源 (rule/llm)

class ValidatedHypothesis(BaseModel):
    hypothesis: Hypothesis              # 假设
    validation: dict                    # 验证结果
    confirmed: bool                     # 是否确认
    additional_evidence: list[str]      # 额外证据
```

#### DiagnosticReport (agent/models/report.py)

```python
class Solution(BaseModel):
    description: str                    # 解决方案描述
    steps: list[str]                    # 步骤列表
    based_on_case: str | None           # 基于案例ID
    confidence: float                   # 置信度

class DiagnosticReport(BaseModel):
    session_id: str                     # 会话ID
    generated_at: datetime              # 生成时间
    summary: str                        # 摘要
    problem_category: ProblemCategory   # 问题类别
    severity: Severity                  # 严重程度
    hypotheses: list[ValidatedHypothesis] # 假设列表
    top_hypothesis: ValidatedHypothesis | None # 最佳假设
    similar_cases: list[Case]           # 相似案例
    recommended_solutions: list[Solution] # 推荐方案
    collected_evidence: dict            # 收集证据
    diagnostic_steps: list              # 诊断步骤
    next_steps: list[str]               # 后续建议
    escalation_needed: bool             # 是否需要升级
```

### 6.2 知识库数据模型

#### Case (kb/models.py)

```python
class Case(BaseModel):
    case_id: str                        # 案例ID
    title: str                          # 标题
    category: str                       # 类别
    severity: str                       # 严重程度
    symptoms: list[str]                 # 症状列表
    problem: str                        # 问题描述
    analysis: str                       # 分析过程
    solution: list[str]                 # 解决方案
    verification: str                   # 验证结果
    references: list[str]               # 参考资料
    related_cases: list[str]            # 相关案例
    created_at: datetime                # 创建时间
    updated_at: datetime                # 更新时间
    tags: list[str]                     # 标签
    cluster: str | None                 # 集群
    service: str | None                 # 服务
    similarity: float = 0.0             # 相似度
```

#### SearchResult (kb/models.py)

```python
class SearchResult(BaseModel):
    case: Case                          # 案例对象
    similarity: float                   # 相似度
    match_reason: str                   # 匹配原因
```

### 6.3 存储数据模型

#### SessionRecord (storage/models.py)

```python
class SessionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SessionRecord(BaseModel):
    session_id: str                     # 会话ID
    description: str                    # 问题描述
    cluster_name: str                   # 集群名称
    status: SessionStatus               # 状态
    created_at: datetime                # 创建时间
    updated_at: datetime                # 更新时间
    completed_at: datetime | None       # 完成时间
    problem_category: str | None        # 问题类别
    severity: str | None                # 严重程度
    top_hypothesis: str | None          # 最佳假设
    confidence: float | None            # 置信度
    error_message: str | None           # 错误信息
```

---

## 7. 配置说明

### 7.1 配置文件结构 (config.yaml)

```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 1

llm:
  api_key: ${LLM_API_KEY}              # 支持环境变量引用
  base_url: https://api.openai.com/v1
  model_name: gpt-4o
  temperature: 0.1
  max_iterations: 15

storage:
  session_dir: ./data/sessions
  case_dir: ./cases
  log_dir: ./logs

logging:
  level: INFO
  file: /var/log/dte-diagnostic-agent/agent.log
  max_size: 10MB
  backup_count: 5

auth:
  api_keys:
    - your-api-key-1
    - your-api-key-2
  env_key: DTE_DIAG_API_KEY

clusters:
  prod-01:
    kubeconfig: /path/to/kubeconfig-prod-01
    ssh_key: ~/.ssh/id_rsa_prod

knowledge_base:
  mode: local                          # local/remote
  
  local:
    case_dir: ./cases
  
  remote:
    api_url: https://kb-api.example.com
    api_key: null
    timeout: 30
  
  query_processor:
    enabled: true
    use_llm_translation: true
    cache_size: 100
```

### 7.2 配置文件优先级

1. 命令行指定路径: `--config /path/to/config.yaml`
2. 系统配置目录: `/etc/dte-diagnostic-agent/config.yaml`
3. 用户配置目录: `~/.dte-diag/config.yaml`

### 7.3 环境变量支持

配置文件支持 `${VAR_NAME}` 格式引用环境变量：

```yaml
llm:
  api_key: ${LLM_API_KEY}
```

环境变量可通过 `.env` 文件加载。

---

## 8. 运行方式

### 8.1 启动脚本

**Windows**:
```batch
bin\start.bat [port]
```

**Linux**:
```bash
./bin/start.sh [port]
```

默认端口: 8080

### 8.2 命令行启动

```bash
python -m dte_diagnostic_agent --config config.yaml --port 8080
```

**参数**:
- `--config`: 配置文件路径
- `--port`: 服务端口
- `--host`: 监听地址
- `--api-key`: API密钥
- `--log-level`: 日志级别
- `--dry-run`: 仅验证配置

### 8.3 systemd服务

**服务文件**: `/etc/systemd/system/dte-diagnostic-agent.service`

```bash
sudo systemctl start dte-diagnostic-agent
sudo systemctl stop dte-diagnostic-agent
sudo systemctl status dte-diagnostic-agent
```

### 8.4 CLI工具使用

```bash
dte-diag diagnose --description "服务响应缓慢" --cluster prod-01
dte-diag status <session_id>
dte-diag history
dte-diag search --query "连接超时"
dte-diag case show CASE-001
```

---

## 9. API接口

### 9.1 诊断接口

#### POST /api/v1/diagnose

创建诊断任务

**请求体**:
```json
{
  "description": "问题描述",
  "time_range_start": "2024-01-15T10:00:00",
  "time_range_end": "2024-01-15T11:00:00",
  "environment": {
    "cluster_name": "prod-01",
    "node_info": {
      "host": "192.168.1.100",
      "port": 22,
      "username": "admin"
    },
    "service_name": "DTEBaseService"
  },
  "symptoms": ["超时", "响应缓慢"],
  "priority": "high"
}
```

**响应**:
```json
{
  "session_id": "diag-xxx",
  "status": "pending",
  "created_at": "2024-01-15T10:00:00"
}
```

#### GET /api/v1/diagnose/{session_id}

查询诊断状态

#### DELETE /api/v1/diagnose/{session_id}

取消诊断任务

#### GET /api/v1/diagnose/list

诊断任务列表

### 9.2 案例接口

#### GET /api/v1/cases/search

搜索案例库

**参数**:
- `query`: 搜索关键词
- `symptoms`: 症状筛选
- `category`: 类别筛选
- `limit`: 返回数量

#### POST /api/v1/cases

创建新案例

#### GET /api/v1/cases/{case_id}

获取案例详情

### 9.3 健康检查

#### GET /api/v1/health

健康检查端点（无需认证）

---

## 10. CLI命令

### 10.1 diagnose - 执行诊断

```bash
dte-diag diagnose --description "问题描述" --cluster prod-01 \
  --node 192.168.1.100 \
  --ssh-key ~/.ssh/id_rsa \
  --service DTEBaseService \
  --last 1h \
  --priority high \
  --wait
```

**参数**:
- `--description`: 问题描述（必填）
- `--cluster`: 集群名称（必填）
- `--node`: 目标节点IP
- `--ssh-key`: SSH密钥路径
- `--service`: 服务名称
- `--last`: 最近时间段 (1h, 30m, 2d)
- `--priority`: 优先级
- `--wait`: 等待诊断完成
- `--interactive`: 交互式输入

### 10.2 status - 查询状态

```bash
dte-diag status <session_id> --watch --include-evidence
```

### 10.3 history - 历史记录

```bash
dte-diag history --limit 20 --status completed --cluster prod-01
```

### 10.4 search - 搜索案例

```bash
dte-diag search --query "连接超时" --symptoms "慢查询,高延迟"
```

### 10.5 case - 案例管理

```bash
dte-diag case show CASE-001
dte-diag case save <session_id> --title "案例标题" --tags "database"
dte-diag case list --limit 20
```

### 10.6 cluster - 集群管理

```bash
dte-diag cluster list
dte-diag cluster status prod-01
dte-diag cluster test prod-01 --node 192.168.1.100
```

### 10.7 config - 配置管理

```bash
dte-diag config show
dte-diag config set default.cluster prod-01
dte-diag config init --api-url http://localhost:8080
```

---

## 11. 工具集

### 11.1 SSH连接工具 (ssh.py)

```python
SSHConnectTool = StructuredTool.from_function(
    coroutine=_ssh_connect,
    name="ssh_connect",
    description="连接到目标服务器节点",
    args_schema=SSHConnectInput
)
```

**参数**:
- host: 目标主机
- port: SSH端口
- username: 用户名
- password: 密码
- ssh_key_path: 密钥路径

### 11.2 日志分析工具 (log.py)

```python
LogAnalysisTool = StructuredTool.from_function(
    coroutine=_log_analysis,
    name="log_analysis",
    description="分析服务日志",
    args_schema=LogAnalysisInput
)
```

**参数**:
- session_id: 会话ID
- log_path: 日志路径
- start_time: 开始时间
- end_time: 结束时间
- patterns: 搜索模式

### 11.3 数据库查询工具 (database.py)

```python
DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="查询数据库状态",
    args_schema=DatabaseQueryInput
)
```

**查询类型**:
- connections: 连接状态
- slow_queries: 慢查询
- locks: 锁状态
- replication: 复制状态

### 11.4 指标采集工具 (resource.py)

```python
ResourceMonitorTool = StructuredTool.from_function(
    coroutine=_resource_monitor,
    name="resource_monitor",
    description="采集系统资源指标",
    args_schema=ResourceMonitorInput
)
```

**采集指标**:
- cpu: CPU使用率
- memory: 内存使用率
- disk: 磁盘使用率
- network: 网络流量

---

## 12. 知识库管理

### 12.1 双模式架构

```
KnowledgeBaseManager
    ├── mode: local → LocalMarkdownKB
    │       └── case_dir: ./cases/*.md
    └── mode: remote → RemoteKBClient
            └── api_url: https://kb-api.example.com
```

### 12.2 查询预处理流程

```
用户查询
    │
    ▼
KeywordExtractor.extract_keywords()
    │ 提取中文词组、英文单词、技术术语
    ▼
关键词列表
    │
    ▼
TranslatorService.translate()
    │ 中文→英文，英文→中文
    │ 技术术语保留原值
    ▼
双语关键词
    │ chinese_keywords, english_keywords
    ▼
LocalMarkdownKB.search()
    │ 多关键词匹配
    ▼
SearchResult列表
```

### 12.3 案例文件格式

```markdown
---
case_id: CASE-001
title: 数据库连接超时问题解决
category: database
severity: high
tags:
  - database
  - connection
  - timeout
created_at: 2024-01-15T10:00:00
updated_at: 2024-01-15T11:00:00
---

## 问题现象
数据库连接频繁超时，用户登录失败。

## 症状列表
- 连接超时
- 服务响应缓慢
- 用户无法登录

## 分析过程
1. 检查数据库连接状态
2. 分析连接池配置
3. 查看连接持有时间

## 解决方案
1. 增加连接池大小到100
2. 设置连接超时时间为30秒
3. 添加连接健康检查

## 验证结果
问题解决，服务恢复正常。

## 参考资料
- PostgreSQL最佳实践
- 连接池配置指南
```

---

## 13. 诊断流程

### 13.1 完整流程图

```
用户输入 (UserInput)
    │
    ▼
IntentParser.parse()
    │ 格式化输入 → LLM调用 → 解析响应
    │ 提取: 问题描述、时间范围、环境信息、症状、优先级、类别
    ▼
DiagnosticContext
    │
    ▼
QueryProcessor.process()
    │ 关键词提取 → 中英文翻译 → 合并去重
    │ 输出: chinese_keywords, english_keywords, all_keywords
    ▼
KnowledgeBaseManager.search()
    │ 多关键词匹配 → 计算相似度 → 排序返回
    ▼
相似案例列表 (list[Case])
    │
    ▼
DiagnosticPlanner.generate_plan()
    │ 格式化案例 → LLM调用 → 解析步骤
    │ 生成: DiagnosticPlan (steps列表)
    ▼
DiagnosticPlan
    │
    ▼
执行诊断步骤
    │ for step in plan.steps:
    │     _execute_step(context, step)
    │     context.collected_data[step.name] = result
    ▼
收集证据 (collected_data)
    │
    ▼
ReasoningEngine.analyze()
    │ 规则匹配 → LLM推理 → 合并假设 → 排序
    ▼
Hypothesis列表
    │
    ▼
ReasoningEngine.validate_hypotheses()
    │ 验证假设 → 生成ValidatedHypothesis
    ▼
ValidatedHypothesis列表
    │
    ▼
_generate_report()
    │ 选择最佳假设 → 生成解决方案 → 构建报告
    ▼
DiagnosticReport
```

### 13.2 诊断步骤执行

```python
for step in plan.get_ordered_steps():
    result = await self._execute_step(context, step, session_id)
    context.collected_data[step.name] = result
```

**模拟执行结果**:
- ssh_connect: `{"status": "simulated_connection"}`
- log_analysis: `{"logs": [], "anomalies": []}`
- resource_monitor: `{"cpu": 50.0, "memory": 60.0, "disk": 70.0}`
- database_query: `{"connections": 50, "slow_queries": []}`
- case_search: `{"cases_found": N}`

### 13.3 推理分析流程

```
DiagnosticContext
    │
    ▼
规则匹配
    │ for rule in self.rules:
    │     if rule.match(context):
    │         hypotheses.append(rule.hypothesis)
    ▼
规则假设列表
    │
    ▼
LLM推理
    │ 构建推理Prompt → LLM调用 → 解析响应
    ▼
LLM假设列表
    │
    ▼
合并排序
    │ hypotheses.extend(llm_hypotheses)
    │ sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
    ▼
最终假设列表
```

---

## 14. 扩展性设计

### 14.1 工具插件机制

```python
class ToolPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str
    
    @property
    @abstractmethod
    def description(self) -> str
    
    @abstractmethod
    async def execute(self, params: BaseModel) -> object
    
    def to_structured_tool(self) -> StructuredTool

class ToolRegistry:
    def register(self, tool: ToolPlugin)
    def get(self, name: str) -> ToolPlugin | None
    def to_langchain_tools(self) -> list[StructuredTool]
```

### 14.2 知识库适配器扩展

```python
class KnowledgeBaseInterface(ABC):
    async def search() -> list[SearchResult]
    async def get() -> Case | None
    async def save() -> str
    async def list_all() -> list[Case]
    async def delete() -> bool
    async def reload()
```

**已有实现**:
- LocalMarkdownKB: 本地Markdown文件
- RemoteKBClient: HTTP API远程知识库

**扩展步骤**:
1. 继承 `KnowledgeBaseInterface`
2. 实现所有抽象方法
3. 在配置中添加对应配置项
4. 在 `KnowledgeBaseManager` 中注册新模式

### 14.3 诊断规则扩展

```python
class DiagnosticRule:
    rule_id: str
    name: str
    conditions: dict
    hypothesis: Hypothesis
    
    def match(self, context: DiagnosticContext) -> bool
```

**添加新规则**:
在 `ReasoningEngine._load_rules()` 中添加新的 `DiagnosticRule` 实例。

---

## 附录

### A. 日志格式

```
%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s
```

### B. 会话存储CSV格式

| 字段 | 说明 |
|------|------|
| session_id | 会话ID |
| description | 问题描述 |
| cluster_name | 集群名称 |
| status | 状态 |
| created_at | 创建时间 |
| updated_at | 更新时间 |
| completed_at | 完成时间 |
| problem_category | 问题类别 |
| severity | 严重程度 |
| top_hypothesis | 最佳假设 |
| confidence | 置信度 |
| error_message | 错误信息 |

### C. 输出格式支持

| 格式 | 说明 |
|------|------|
| table | 表格格式（默认） |
| json | JSON格式 |
| yaml | YAML格式 |
| text | 纯文本格式 |
| markdown | Markdown格式 |

### D. 问题类别枚举

| 类别 | 值 |
|------|-----|
| 服务不可用 | service_unavailable |
| 性能下降 | performance_degradation |
| 数据不一致 | data_inconsistency |
| 网络问题 | network_issue |
| 资源耗尽 | resource_exhaustion |
| 配置错误 | configuration_error |
| 未知 | unknown |

### E. 严重程度枚举

| 级别 | 值 |
|------|-----|
| 关键 | critical |
| 高 | high |
| 中 | medium |
| 低 | low |

---

**文档版本**: 1.0  
**最后更新**: 2026-05-06  
**项目版本**: 0.1.0