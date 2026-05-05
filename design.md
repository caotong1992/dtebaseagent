# DTEBaseService 问题定位 AI Agent 设计方案

## 1. 概述

### 1.1 目标
设计一个智能AI Agent，用于DTEBaseService服务的问题定位和诊断，支持跨多个私有集群的运维场景。

### 1.2 核心能力
- 接收用户描述的问题现象、时间范围和环境信息
- 查询历史维护案例库进行相似案例匹配
- 自动连接目标环境进行诊断
- 分析日志、数据库、系统指标等多维数据
- 输出问题可能原因和解决建议

### 1.3 技术约束

| 约束项 | 版本/要求 |
|--------|----------|
| Python | 3.14 |
| LangChain | 2.15.4 |
| LLM API | OpenAI API |
| 异步框架 | asyncio (Python 3.14 内置) |
| 类型系统 | Python 3.14 新特性 (泛型类型改进) |

**Python 3.14 新特性应用**:
- 使用改进的泛型类型语法 (`list[str]` 替代 `List[str]`)
- 利用更高效的异步运行时
- 使用新的字符串格式化和模式匹配特性

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户交互层                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐                  │
│  │       CLI工具       │  │       API接口       │                  │
│  └─────────────────────┘  └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent 核心层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 意图理解模块  │  │ 规划调度模块  │  │ 推理决策模块  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 上下文管理   │  │  记忆模块    │  │ 结果生成模块  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         工具执行层                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │SSH连接  │ │日志分析 │ │数据库查询│ │指标采集 │ │案例检索 │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │配置检查 │ │进程管理 │ │网络诊断 │ │存储检查 │ │K8s操作  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         数据存储层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 历史案例库   │  │  知识图谱    │  │  会话存储    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 诊断结果库   │  │  配置仓库    │  │  日志索引    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. API接口设计

系统提供RESTful API接口用于诊断服务调用，支持异步诊断流程。

### 3.1 诊断接口

#### POST /api/v1/diagnose
提交诊断请求

**请求体**:
```json
{
  "description": "string - 问题描述，必填",
  "time_range": {
    "start": "string - ISO8601时间格式，可选，默认最近1小时",
    "end": "string - ISO8601时间格式，可选，默认当前时间"
  },
  "environment": {
    "cluster_name": "string - 集群名称，必填",
    "node_info": {
      "host": "string - 节点IP或域名，可选",
      "port": "integer - SSH端口，默认22",
      "username": "string - 登录用户名，可选",
      "auth_type": "string - 认证类型: password/ssh_key",
      "password": "string - 密码，可选",
      "ssh_key_path": "string - SSH密钥路径，可选"
    },
    "service_name": "string - 服务名称，默认DTEBaseService",
    "namespace": "string - K8s命名空间，可选"
  },
  "symptoms": ["string - 症状列表，可选"],
  "priority": "string - 优先级: critical/high/medium/low，默认medium",
  "options": {
    "timeout": "integer - 超时时间(秒)，默认300",
    "dry_run": "boolean - 仅生成计划不执行，默认false",
    "verbose": "boolean - 详细输出，默认false"
  }
}
```

**响应**:
```json
{
  "session_id": "string - 会话ID",
  "status": "string - 状态: pending/running/completed/failed",
  "created_at": "string - ISO8601时间",
  "estimated_duration": "integer - 预估耗时(秒)"
}
```

**状态码**:
- 200: 成功创建诊断任务
- 400: 请求参数无效
- 401: 认证失败
- 403: 无权限访问指定集群
- 500: 服务内部错误

#### GET /api/v1/diagnose/{session_id}
查询诊断结果

**路径参数**:
- session_id: 会话ID

**查询参数**:
- format: string - 输出格式: json/markdown/text，默认json
- include_evidence: boolean - 是否包含收集的证据，默认false

**响应（进行中）**:
```json
{
  "session_id": "string",
  "status": "running",
  "progress": {
    "current_step": "string - 当前步骤名称",
    "completed_steps": ["string - 已完成步骤"],
    "remaining_steps": ["string - 待执行步骤"],
    "percentage": "integer - 进度百分比"
  }
}
```

**响应（已完成）**:
```json
{
  "session_id": "string",
  "status": "completed",
  "generated_at": "string",
  "summary": "string - 问题摘要",
  "problem_category": "string - 问题类别",
  "severity": "string - 严重程度",
  "hypotheses": [
    {
      "id": "string",
      "problem": "string - 问题描述",
      "confidence": "float - 置信度0-1",
      "evidence": ["string - 支持证据"],
      "actions": ["string - 建议操作"]
    }
  ],
  "top_hypothesis": {
    "problem": "string",
    "confidence": "float"
  },
  "recommended_solutions": [
    {
      "description": "string",
      "steps": ["string"],
      "confidence": "float"
    }
  ],
  "similar_cases": [
    {
      "case_id": "string",
      "title": "string",
      "similarity": "float"
    }
  ],
  "next_steps": ["string - 后续建议"],
  "escalation_needed": "boolean"
}
```

**状态码**:
- 200: 成功返回结果
- 404: 会话不存在
- 410: 会话已过期

#### DELETE /api/v1/diagnose/{session_id}
取消诊断任务

**响应**:
```json
{
  "session_id": "string",
  "status": "cancelled",
  "cancelled_at": "string"
}
```

#### GET /api/v1/diagnose/list
列出诊断历史

**查询参数**:
- limit: integer - 返回数量，默认20，最大100
- offset: integer - 偏移量，默认0
- status: string - 状态筛选: all/pending/running/completed/failed
- cluster: string - 集群筛选
- start_date: string - 开始日期筛选
- end_date: string - 结束日期筛选

**响应**:
```json
{
  "total": "integer - 总数",
  "items": [
    {
      "session_id": "string",
      "description": "string",
      "cluster_name": "string",
      "status": "string",
      "created_at": "string",
      "completed_at": "string"
    }
  ],
  "pagination": {
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
}
```

### 3.2 案例库接口

#### GET /api/v1/cases/search
搜索历史案例

**查询参数**:
- query: string - 搜索关键词，必填
- symptoms: string - 症状筛选，逗号分隔
- category: string - 问题类别筛选
- limit: integer - 返回数量，默认10

**响应**:
```json
{
  "total": "integer",
  "items": [
    {
      "case_id": "string",
      "title": "string",
      "symptoms": ["string"],
      "problem": "string",
      "solution_summary": "string",
      "similarity": "float",
      "created_at": "string"
    }
  ]
}
```

#### POST /api/v1/cases
创建新案例（从诊断结果保存）

**请求体**:
```json
{
  "session_id": "string - 诊断会话ID",
  "title": "string - 案例标题",
  "tags": ["string - 标签"]
}
```

**响应**:
```json
{
  "case_id": "string",
  "created_at": "string"
}
```

#### GET /api/v1/cases/{case_id}
获取案例详情

**响应**:
```json
{
  "case_id": "string",
  "title": "string",
  "symptoms": ["string"],
  "problem": "string",
  "solution": {
    "description": "string",
    "steps": ["string"]
  },
  "metadata": {
    "cluster": "string",
    "service": "string",
    "created_at": "string"
  }
}
```

---

## 4. CLI工具设计

系统提供命令行工具 `dte-diag` 用于交互式诊断操作。

### 4.1 全局选项

```
--config <path>          配置文件路径，默认 ~/.dte-diag/config.yaml
--api-url <url>          API服务地址，默认 http://localhost:8080
--api-key <key>          API认证密钥
--output <format>        输出格式: json/yaml/text/table，默认 table
--verbose                详细输出模式
--quiet                  静默模式，仅输出结果
--no-color               禁用彩色输出
--help                   显示帮助信息
--version                显示版本信息
```

### 4.2 主命令

#### diagnose - 执行诊断

```
dte-diag diagnose [选项]

必选参数:
  --description <text>       问题描述
  --cluster <name>           集群名称

可选参数:
  --node <ip>                目标节点IP
  --node-user <username>     节点登录用户
  --node-port <port>         SSH端口，默认22
  --auth-type <type>         认证类型: password/key
  --password <pwd>           登录密码
  --ssh-key <path>           SSH密钥路径
  --service <name>           服务名称，默认DTEBaseService
  --namespace <ns>           K8s命名空间

时间参数:
  --time-start <time>        问题开始时间，ISO8601格式
  --time-end <time>          问题结束时间，ISO8601格式
  --last <duration>          最近时间段，如: 1h, 30m, 2d

诊断选项:
  --priority <level>         优先级: critical/high/medium/low
  --timeout <seconds>        超时时间，默认300
  --dry-run                  仅生成诊断计划不执行
  --wait                     等待诊断完成并显示结果
  --follow                   实时显示诊断进度

交互模式:
  -i, --interactive          交互式输入模式，逐步引导输入
```

**示例**:
```bash
# 最简诊断
dte-diag diagnose --description "服务响应缓慢" --cluster prod-01

# 完整参数诊断
dte-diag diagnose \
  --description "数据库连接超时，用户无法登录" \
  --cluster prod-01 \
  --node 192.168.1.100 \
  --node-user admin \
  --ssh-key ~/.ssh/id_rsa \
  --service DTEBaseService \
  --namespace production \
  --last 1h \
  --priority high \
  --wait

# 交互式诊断
dte-diag diagnose -i

# 仅生成计划
dte-diag diagnose --description "服务异常" --cluster prod-01 --dry-run
```

#### status - 查询诊断状态

```
dte-diag status <session_id> [选项]

参数:
  session_id                 诊断会话ID

选项:
  --format <format>          输出格式: json/markdown/text
  --include-evidence         包含收集的证据详情
  --watch                    持续监控直到完成
```

**示例**:
```bash
# 查询诊断状态
dte-diag status diag-20240115-001

# 持续监控并显示详细证据
dte-diag status diag-20240115-001 --watch --include-evidence

# Markdown格式输出
dte-diag status diag-20240115-001 --format markdown
```

#### history - 查看历史记录

```
dte-diag history [选项]

选项:
  --limit <n>                返回数量，默认20
  --status <status>          状态筛选: all/pending/running/completed/failed
  --cluster <name>           集群筛选
  --date <date>              日期筛选
  --after <date>             此日期之后的记录
  --before <date>            此日期之前的记录
```

**示例**:
```bash
# 查看最近20条记录
dte-diag history

# 查看特定集群的失败诊断
dte-diag history --cluster prod-01 --status failed

# 查看今天的记录
dte-diag history --date today

# 查看最近7天已完成的诊断
dte-diag history --after "7 days ago" --status completed
```

#### cancel - 取消诊断

```
dte-diag cancel <session_id>
```

**示例**:
```bash
dte-diag cancel diag-20240115-001
```

#### search - 搜索案例库

```
dte-diag search [选项]

必选参数:
  --query <text>             搜索关键词

选项:
  --symptoms <list>          症状筛选，逗号分隔
  --category <category>      问题类别筛选
  --limit <n>                返回数量，默认10
```

**示例**:
```bash
# 搜索超时相关案例
dte-diag search --query "连接超时"

# 搜索特定症状的案例
dte-diag search --query "性能问题" --symptoms "慢查询,高延迟"

# 搜索特定类别
dte-diag search --query "数据库" --category performance_degradation
```

#### case - 案例管理

```
# 查看案例详情
dte-diag case show <case_id>

# 从诊断结果保存案例
dte-diag case save <session_id> --title <title> [--tags <tags>]

# 列出所有案例
dte-diag case list [--limit <n>]
```

**示例**:
```bash
# 查看案例详情
dte-diag case show CASE-001

# 从诊断结果保存案例
dte-diag case save diag-20240115-001 --title "数据库连接池耗尽解决方案" --tags "database,connection"

# 列出案例
dte-diag case list --limit 20
```

#### cluster - 集群管理

```
# 列出可用集群
dte-diag cluster list

# 查看集群状态
dte-diag cluster status <cluster_name>

# 测试集群连接
dte-diag cluster test <cluster_name> [--node <ip>]
```

**示例**:
```bash
# 列出集群
dte-diag cluster list

# 查看集群状态
dte-diag cluster status prod-01

# 测试连接
dte-diag cluster test prod-01 --node 192.168.1.100
```

#### config - 配置管理

```
# 查看当前配置
dte-diag config show

# 设置配置项
dte-diag config set <key> <value>

# 初始化配置文件
dte-diag config init [--api-url <url>] [--api-key <key>]
```

**示例**:
```bash
# 初始化配置
dte-diag config init --api-url http://localhost:8080

# 设置默认集群
dte-diag config set default.cluster prod-01

# 查看配置
dte-diag config show
```

### 4.3 输出格式示例

#### table格式（默认）
```
Session ID       Status      Cluster    Description          Created At
diag-20240115-001 completed   prod-01    数据库连接超时        2024-01-15 10:30
diag-20240115-002 running     prod-02    服务响应缓慢          2024-01-15 11:00
```

#### json格式
```json
{"session_id": "diag-20240115-001", "status": "completed", ...}
```

#### text格式
```
诊断会话: diag-20240115-001
状态: 已完成
集群: prod-01
问题描述: 数据库连接超时
创建时间: 2024-01-15 10:30:00

诊断结果:
问题类别: 数据库连接问题
置信度: 85%
最可能原因: 数据库连接池配置不足
建议操作:
  1. 检查连接池配置
  2. 分析连接持有时间
```

#### markdown格式
```markdown
## 诊断报告 - diag-20240115-001

### 问题摘要
数据库连接超时

### 诊断结果
- **问题类别**: 数据库连接问题
- **置信度**: 85%
- **严重程度**: 高

### 可能原因
1. 数据库连接池配置不足 (85%)
2. 存在连接泄漏 (60%)

### 建议方案
1. 检查连接池配置
2. 分析连接持有时间
```

### 4.4 配置文件格式

配置文件位置: `~/.dte-diag/config.yaml`

```yaml
api:
  url: http://localhost:8080
  key: your-api-key
  timeout: 300

defaults:
  cluster: prod-01
  service: DTEBaseService
  output: table
  priority: medium

auth:
  ssh_key_path: ~/.ssh/id_rsa
  username: admin

logging:
  level: info
  file: ~/.dte-diag/logs/dte-diag.log
```

---

## 5. 核心组件设计

### 5.1 意图理解模块 (Intent Understanding)

**功能**: 解析用户输入，提取关键信息

**输入信息提取**:
```json
{
  "problem_description": "服务响应缓慢",
  "time_range": {
    "start": "2024-01-15 10:00:00",
    "end": "2024-01-15 11:00:00"
  },
  "environment": {
    "cluster_name": "cluster-prod-01",
    "node_info": {
      "host": "192.168.1.100",
      "port": 22,
      "username": "admin",
      "auth_type": "ssh_key",
      "ssh_key_path": "/path/to/key"
    },
    "service_name": "DTEBaseService",
    "namespace": "production"
  },
  "symptoms": ["高延迟", "超时错误"],
  "priority": "high"
}
```

**处理流程**:
1. 文本预处理和实体识别
2. 时间表达式解析
3. 环境信息结构化
4. 问题现象分类

### 5.2 规划调度模块 (Planning & Orchestration)

**功能**: 根据问题类型生成诊断计划

**诊断策略模板**:

```yaml
strategies:
  service_unavailable:
    steps:
      - name: check_process_status
        tool: process_manager
        action: status
      - name: check_service_logs
        tool: log_analyzer
        action: fetch_recent
      - name: check_network
        tool: network_diagnostic
        action: connectivity_test
      - name: check_resources
        tool: resource_monitor
        action: get_metrics
      
  performance_degradation:
    steps:
      - name: check_system_metrics
        tool: resource_monitor
        action: get_metrics
      - name: analyze_slow_logs
        tool: log_analyzer
        action: search_patterns
        patterns: ["slow", "timeout", "delay"]
      - name: check_database
        tool: database_query
        action: check_connections
      - name: check_cache
        tool: cache_manager
        action: status
        
  data_inconsistency:
    steps:
      - name: check_database_logs
        tool: log_analyzer
        action: fetch_errors
      - name: check_replication
        tool: database_query
        action: check_replication_status
      - name: check_data_integrity
        tool: database_query
        action: run_consistency_check
```

### 5.3 推理决策模块 (Reasoning & Decision)

**功能**: 基于收集的信息进行推理分析

**推理引擎设计**:

```python
class ReasoningEngine:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.rules = self.load_diagnostic_rules()
        
    def analyze(self, context: DiagnosticContext) -> list[Hypothesis]:
        hypotheses = []
        
        for rule in self.rules:
            if rule.match(context.symptoms):
                hypotheses.append(rule.generate_hypothesis(context))
        
        llm_hypotheses = self._llm_reasoning(context)
        hypotheses.extend(llm_hypotheses)
        
        return self.rank_hypotheses(hypotheses)
    
    async def _llm_reasoning(self, context: DiagnosticContext) -> list[Hypothesis]:
        prompt = self._build_reasoning_prompt(context)
        response = await self.llm.ainvoke(prompt)
        return self._parse_hypotheses(response.content)
    
    def rank_hypotheses(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        return sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
```

**诊断规则示例**:

```json
{
  "rule_id": "RULE_001",
  "name": "数据库连接池耗尽",
  "conditions": [
    {"metric": "db_connection_count", "operator": ">", "value": 90, "unit": "%"},
    {"log_pattern": "connection.*timeout|pool.*exhausted"},
    {"symptom": "服务超时"}
  ],
  "hypothesis": {
    "problem": "数据库连接池配置不足或连接泄漏",
    "confidence": 0.85,
    "actions": [
      "检查连接池配置",
      "分析连接持有时间",
      "检查是否有长事务"
    ]
  }
}
```

---

## 6. 工具集设计

### 6.1 SSH连接工具 (SSHConnector)

```python
import asyncssh

class SSHConnector:
    """SSH连接工具 - 用于连接私有集群节点"""
    
    def __init__(self, connection_pool_size: int = 10):
        self.pool_size = connection_pool_size
        self.sessions: dict[str, asyncssh.SSHClientConnection] = {}
    
    async def connect(self, node_info: NodeInfo) -> asyncssh.SSHClientConnection:
        """建立SSH连接"""
        conn = await asyncssh.connect(
            host=node_info.host,
            port=node_info.port,
            username=node_info.username,
            password=node_info.password,
            client_keys=[node_info.ssh_key_path] if node_info.ssh_key_path else None,
            known_hosts=None
        )
        self.sessions[node_info.host] = conn
        return conn
    
    async def execute_command(
        self,
        session: asyncssh.SSHClientConnection,
        command: str
    ) -> CommandResult:
        """执行远程命令"""
        result = await session.run(command)
        return CommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_status
        )
    
    async def upload_file(
        self,
        session: asyncssh.SSHClientConnection,
        local_path: str,
        remote_path: str
    ):
        await asyncssh.scp(local_path, (session, remote_path))
    
    async def download_file(
        self,
        session: asyncssh.SSHClientConnection,
        remote_path: str,
        local_path: str
    ):
        await asyncssh.scp((session, remote_path), local_path)

class CommandResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
```

### 4.2 日志分析工具 (LogAnalyzer)

```python
import re
from collections import Counter

class LogAnalyzer:
    """日志分析工具"""
    
    async def fetch_logs(
        self,
        session: asyncssh.SSHClientConnection,
        log_path: str,
        time_range: TimeRange
    ) -> list[LogEntry]:
        """获取指定时间范围的日志"""
        start_str = time_range.start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = time_range.end.strftime("%Y-%m-%d %H:%M:%S")
        
        command = f"awk '/{start_str}/,/{end_str}/' {log_path}"
        result = await session.run(command)
        return self._parse_logs(result.stdout)
    
    def _parse_logs(self, log_content: str) -> list[LogEntry]:
        """解析日志内容"""
        entries = []
        for line in log_content.splitlines():
            parsed = self._parse_log_line(line)
            if parsed:
                entries.append(parsed)
        return entries
    
    async def search_patterns(
        self,
        logs: list[LogEntry],
        patterns: list[str]
    ) -> list[LogMatch]:
        """搜索日志模式"""
        matches = []
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for log in logs:
                if regex.search(log.message):
                    matches.append(LogMatch(
                        log_entry=log,
                        pattern=pattern,
                        matched_text=regex.findall(log.message)
                    ))
        return matches
    
    async def detect_anomalies(self, logs: list[LogEntry]) -> list[Anomaly]:
        """检测日志异常"""
        anomalies = []
        
        error_count = Counter(log.level for log in logs if log.level == "ERROR")
        for level, count in error_count.items():
            if count > 10:
                anomalies.append(Anomaly(
                    type="high_error_rate",
                    severity="high",
                    description=f"发现{count}条ERROR级别日志",
                    count=count
                ))
        
        return anomalies
    
    async def analyze_error_stack(self, logs: list[LogEntry]) -> ErrorAnalysis:
        """分析错误堆栈"""
        errors = [log for log in logs if log.level == "ERROR"]
        return ErrorAnalysis(
            error_count=len(errors),
            error_types=self._classify_errors(errors),
            stack_traces=self._extract_stacks(errors)
        )

class LogMatch(BaseModel):
    log_entry: LogEntry
    pattern: str
    matched_text: list[str]

class Anomaly(BaseModel):
    type: str
    severity: str
    description: str
    count: int

class ErrorAnalysis(BaseModel):
    error_count: int
    error_types: dict[str, int]
    stack_traces: list[str]
```

### 4.3 数据库查询工具 (DatabaseQuery)

```python
import asyncpg

class DatabaseQuery:
    """数据库查询工具"""
    
    async def connect(self, db_config: DBConfig) -> asyncpg.Connection:
        """建立数据库连接"""
        return await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password
        )
    
    async def check_connections(self, conn: asyncpg.Connection) -> ConnectionStatus:
        """检查数据库连接状态"""
        result = await conn.fetchval(
            "SELECT count(*) FROM pg_stat_activity"
        )
        max_conn = await conn.fetchval(
            "SELECT setting FROM pg_settings WHERE name = 'max_connections'"
        )
        return ConnectionStatus(
            active_connections=result,
            max_connections=int(max_conn)
        )
    
    async def check_slow_queries(
        self,
        conn: asyncpg.Connection,
        threshold_ms: int = 1000
    ) -> list[SlowQuery]:
        """检查慢查询"""
        results = await conn.fetch("""
            SELECT query, mean_exec_time, calls 
            FROM pg_stat_statements 
            WHERE mean_exec_time > $1
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """, threshold_ms)
        return [SlowQuery(query=r['query'], mean_time=r['mean_exec_time'], calls=r['calls']) for r in results]
    
    async def check_locks(self, conn: asyncpg.Connection) -> list[DBLock]:
        """检查数据库锁"""
        results = await conn.fetch("""
            SELECT locktype, relation, mode, granted 
            FROM pg_locks 
            WHERE NOT granted
        """)
        return [DBLock(locktype=r['locktype'], relation=r['relation'], mode=r['mode']) for r in results]
    
    async def check_replication_status(self, conn: asyncpg.Connection) -> ReplicationStatus:
        """检查复制状态"""
        results = await conn.fetch("SELECT * FROM pg_stat_replication")
        return ReplicationStatus(
            replication_active=len(results) > 0,
            replicas=[r['client_addr'] for r in results]
        )

class DBConfig(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str

class ConnectionStatus(BaseModel):
    active_connections: int
    max_connections: int

class SlowQuery(BaseModel):
    query: str
    mean_time: float
    calls: int

class DBLock(BaseModel):
    locktype: str
    relation: str | None
    mode: str

class ReplicationStatus(BaseModel):
    replication_active: bool
    replicas: list[str]
```

### 4.4 指标采集工具 (ResourceMonitor)

```python
class ResourceMonitor:
    """资源监控工具"""
    
    async def get_system_metrics(
        self,
        session: asyncssh.SSHClientConnection,
        metrics: list[str] = None
    ) -> SystemMetrics:
        """获取系统指标"""
        if metrics is None:
            metrics = ['cpu', 'memory', 'disk', 'network']
        
        results = {}
        for metric in metrics:
            results[metric] = await self._collect_metric(session, metric)
        
        return SystemMetrics(
            cpu=results.get('cpu'),
            memory=results.get('memory'),
            disk=results.get('disk'),
            network=results.get('network')
        )
    
    async def _collect_metric(
        self,
        session: asyncssh.SSHClientConnection,
        metric: str
    ):
        collectors = {
            'cpu': self._collect_cpu,
            'memory': self._collect_memory,
            'disk': self._collect_disk,
            'network': self._collect_network
        }
        return await collectors[metric](session)
    
    async def _collect_cpu(self, session: asyncssh.SSHClientConnection) -> CPUMetrics:
        result = await session.run("top -bn1 | grep 'Cpu(s)'")
        return self._parse_cpu_info(result.stdout)
    
    async def _collect_memory(self, session: asyncssh.SSHClientConnection) -> MemoryMetrics:
        result = await session.run("free -m | grep Mem")
        return self._parse_memory_info(result.stdout)
    
    async def _collect_disk(self, session: asyncssh.SSHClientConnection) -> DiskMetrics:
        result = await session.run("df -h / | tail -1")
        return self._parse_disk_info(result.stdout)
    
    def _parse_cpu_info(self, output: str) -> CPUMetrics:
        parts = output.split()
        return CPUMetrics(
            usage_percent=float(parts[1].replace('%us,', '')),
            idle_percent=float(parts[3].replace('%id,', ''))
        )
    
    def _parse_memory_info(self, output: str) -> MemoryMetrics:
        parts = output.split()
        return MemoryMetrics(
            total=int(parts[1]),
            used=int(parts[2]),
            free=int(parts[3]),
            usage_percent=float(parts[2]) / float(parts[1]) * 100
        )
    
    def _parse_disk_info(self, output: str) -> DiskMetrics:
        parts = output.split()
        return DiskMetrics(
            total=parts[1],
            used=parts[2],
            available=parts[3],
            usage_percent=float(parts[4].replace('%', ''))
        )

class SystemMetrics(BaseModel):
    cpu: CPUMetrics | None
    memory: MemoryMetrics | None
    disk: DiskMetrics | None
    network: NetworkMetrics | None

class CPUMetrics(BaseModel):
    usage_percent: float
    idle_percent: float

class MemoryMetrics(BaseModel):
    total: int
    used: int
    free: int
    usage_percent: float

class DiskMetrics(BaseModel):
    total: str
    used: str
    available: str
    usage_percent: float

class NetworkMetrics(BaseModel):
    bytes_in: int
    bytes_out: int
```

### 6.5 案例检索工具 (CaseRetriever)

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class CaseRetriever:
    """历史案例检索工具"""
    
    def __init__(self, embeddings: OpenAIEmbeddings | None = None):
        self.embeddings = embeddings or OpenAIEmbeddings()
        self.vector_store: FAISS | None = None
    
    def load_cases(self, cases: list[HistoricalCase]):
        """加载历史案例到向量库"""
        texts = [f"{c.title}: {c.problem} - {c.symptoms}" for c in cases]
        metadatas = [{"case_id": c.case_id, "title": c.title} for c in cases]
        self.vector_store = FAISS.from_texts(
            texts, self.embeddings, metadatas=metadatas
        )
    
    async def search_similar_cases(
        self,
        problem_description: str,
        symptoms: list[str],
        top_k: int = 5
    ) -> list[HistoricalCase]:
        """搜索相似历史案例"""
        if self.vector_store is None:
            return []
        
        query_text = f"{problem_description} {' '.join(symptoms)}"
        results = self.vector_store.similarity_search(query_text, k=top_k)
        
        return [
            HistoricalCase(
                case_id=r.metadata["case_id"],
                title=r.metadata["title"],
                symptoms=symptoms,
                problem=problem_description,
                solution=Solution(description="", steps=[], confidence=0.0),
                created_at=datetime.now(),
                similarity_score=0.0
            )
            for r in results
        ]
    
    async def get_solution_from_case(
        self,
        case: HistoricalCase,
        current_context: DiagnosticContext
    ) -> Solution:
        """从历史案例提取解决方案"""
        return case.solution
```

### 6.6 Kubernetes操作工具 (K8sOperator)

```python
from kubernetes import client, config
from kubernetes.client import V1Pod, V1PodList

class K8sOperator:
    """Kubernetes集群操作工具"""
    
    def __init__(self, kubeconfig_path: str | None = None):
        self.kubeconfig = kubeconfig_path
        self.core_v1: client.CoreV1Api | None = None
    
    def connect(self, cluster_info: ClusterInfo):
        """连接到Kubernetes集群"""
        if cluster_info.kubeconfig:
            config.load_kube_config(config_file=cluster_info.kubeconfig)
        else:
            config.load_incluster_config()
        self.core_v1 = client.CoreV1Api()
    
    async def get_pod_status(self, namespace: str, service_name: str) -> list[PodStatus]:
        """获取Pod状态"""
        pods = self.core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"app={service_name}"
        )
        return [self._parse_pod_status(pod) for pod in pods.items]
    
    async def get_pod_logs(
        self,
        pod_name: str,
        namespace: str,
        tail_lines: int = 100
    ) -> str:
        """获取Pod日志"""
        logs = self.core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
        return logs
    
    async def describe_pod(self, pod_name: str, namespace: str) -> PodDescription:
        """获取Pod详情"""
        pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        return self._parse_pod_description(pod)
    
    async def get_events(self, namespace: str) -> list[K8sEvent]:
        """获取集群事件"""
        events = self.core_v1.list_namespaced_event(namespace=namespace)
        return [self._parse_event(e) for e in events.items]
    
    def _parse_pod_status(self, pod: V1Pod) -> PodStatus:
        return PodStatus(
            name=pod.metadata.name,
            phase=pod.status.phase,
            ready=self._is_pod_ready(pod),
            restart_count=pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
        )
    
    def _parse_pod_description(self, pod: V1Pod) -> PodDescription:
        return PodDescription(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            labels=pod.metadata.labels or {},
            status=pod.status.phase,
            created_at=pod.metadata.creation_timestamp
        )
    
    def _parse_event(self, event) -> K8sEvent:
        return K8sEvent(
            type=event.type,
            reason=event.reason,
            message=event.message,
            count=event.count
        )

class PodStatus(BaseModel):
    name: str
    phase: str
    ready: bool
    restart_count: int

class PodDescription(BaseModel):
    name: str
    namespace: str
    labels: dict[str, str]
    status: str
    created_at: datetime | None

class K8sEvent(BaseModel):
    type: str
    reason: str
    message: str
    count: int
```

---

## 6.5 案例库管理

### 案例库接口设计

系统采用可扩展的知识库接口设计，支持本地Markdown文件和远程知识库API两种模式：

```python
class KnowledgeBaseInterface(ABC):
    """知识库检索接口抽象"""
    
    @abstractmethod
    async def search(query: str, symptoms: list[str] | None, 
                     category: str | None, top_k: int) -> list[SearchResult]:
        pass
    
    @abstractmethod
    async def get(case_id: str) -> Case | None:
        pass
    
    @abstractmethod
    async def save(case: Case) -> str:
        pass
    
    @abstractmethod
    async def list_all(category: str | None, limit: int) -> list[Case]:
        pass
    
    @abstractmethod
    async def delete(case_id: str) -> bool:
        pass

class KnowledgeBaseManager:
    """知识库管理器 - 根据配置选择实现"""
    
    def __init__(self, config: KnowledgeBaseConfig):
        match config.mode:
            case "local":
                self.backend = LocalMarkdownKB(config.local)
            case "remote":
                self.backend = RemoteKBClient(config.remote)
```

### 本地Markdown案例库

案例以Markdown文件形式存储在本地目录：

```
cases/
├── database/
│   ├── CASE-001-db-connection-timeout.md
│   └── CASE-002-db-slow-query.md
├── network/
│   └── CASE-010-network-timeout.md
├── performance/
│   └── CASE-020-high-cpu-usage.md
└── service/
    └── CASE-030-service-crash.md
```

**Markdown文件格式**：

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
---

## 问题现象
数据库连接频繁超时，用户登录失败。

## 症状列表
- 连接超时
- 服务响应缓慢

## 分析过程
1. 检查数据库连接状态
2. 分析连接池配置

## 解决方案
1. 增加连接池大小
2. 设置连接超时时间

## 验证结果
问题解决，服务恢复正常。

## 参考资料
- PostgreSQL最佳实践
```

### 远程知识库API

支持对接第三方知识库系统：

```yaml
knowledge_base:
  mode: remote
  remote:
    api_url: https://kb-api.example.com
    api_key: your-api-key
    timeout: 30
```

### 扩展性设计

| 类型 | 实现类 | 说明 |
|------|--------|------|
| local | LocalMarkdownKB | 本地Markdown文件 |
| remote | RemoteKBClient | HTTP API远程知识库 |
| elasticsearch | ESKBClient | Elasticsearch检索 |
| milvus | MilvusKBClient | Milvus向量检索 |

**新增适配器步骤**：
1. 继承 `KnowledgeBaseInterface`
2. 实现所有抽象方法
3. 在配置中添加对应配置项
4. 在 `KnowledgeBaseManager` 中注册新模式

---

## 7. 工作流程

### 7.1 主流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                          问题诊断主流程                               │
└─────────────────────────────────────────────────────────────────────┘

开始
  │
  ▼
┌─────────────────┐
│ 接收用户输入     │ ◄── 问题现象、时间范围、环境信息
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 意图理解与分析   │ ─── 提取关键信息、分类问题类型
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 检索历史案例    │ ─── 向量检索相似案例
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 生成诊断计划    │ ─── 基于问题类型和案例生成检查步骤
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 建立环境连接    │ ─── SSH/K8s连接
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│              执行诊断步骤                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │日志分析 │ │指标检查 │ │配置检查 │ ...    │
│  └─────────┘ └─────────┘ └─────────┘        │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
              ┌───────────┐
              │ 收集完成？ │ ─── 否 ──► 继续执行下一步
              └─────┬─────┘
                    │ 是
                    ▼
         ┌───────────────────┐
         │ 推理分析与假设生成 │ ─── 规则推理 + ML预测
         └─────────┬─────────┘
                   │
                   ▼
         ┌───────────────────┐
         │ 验证假设          │ ─── 进一步检查验证
         └─────────┬─────────┘
                   │
                   ▼
         ┌───────────────────┐
         │ 生成诊断报告      │ ─── 问题原因、解决方案、历史案例
         └─────────┬─────────┘
                   │
                   ▼
                结束
```

### 5.2 诊断执行流程

```python
class DiagnosticWorkflow:
    """诊断工作流"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.reasoning_engine = ReasoningEngine(llm)
        self.case_retriever = CaseRetriever()
    
    async def execute(self, context: DiagnosticContext) -> DiagnosticReport:
        await self._collect_information(context)
        
        hypotheses = await self._generate_hypotheses(context)
        
        validated_hypotheses = await self._validate_hypotheses(context, hypotheses)
        
        report = await self._generate_report(context, validated_hypotheses)
        
        return report
    
    async def _collect_information(self, context: DiagnosticContext):
        tasks = [
            self._collect_logs(context),
            self._collect_metrics(context),
            self._collect_configs(context),
            self._collect_events(context)
        ]
        await asyncio.gather(*tasks)
    
    async def _generate_hypotheses(self, context: DiagnosticContext) -> list[Hypothesis]:
        rule_hypotheses = self.reasoning_engine.apply_rules(context)
        
        case_hypotheses = await self.case_retriever.infer_from_cases(context)
        
        llm_hypotheses = await self.reasoning_engine.analyze(context)
        
        all_hypotheses = rule_hypotheses + case_hypotheses + llm_hypotheses
        return self._merge_and_rank(all_hypotheses)
    
    async def _validate_hypotheses(
        self,
        context: DiagnosticContext,
        hypotheses: list[Hypothesis]
    ) -> list[ValidatedHypothesis]:
        validated = []
        for hypothesis in hypotheses[:5]:
            validation_result = await self._validate_single_hypothesis(context, hypothesis)
            validated.append(ValidatedHypothesis(
                hypothesis=hypothesis,
                validation=validation_result
            ))
        return validated
```

---

## 8. 数据模型设计

### 8.1 核心数据模型 (Python 3.14 类型语法)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ProblemCategory(Enum):
    SERVICE_UNAVAILABLE = "service_unavailable"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_INCONSISTENCY = "data_inconsistency"
    NETWORK_ISSUE = "network_issue"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class NodeInfo(BaseModel):
    host: str
    port: int = 22
    username: str
    auth_type: str = "password"
    password: str | None = None
    ssh_key_path: str | None = None

class ClusterInfo(BaseModel):
    name: str
    type: str
    api_server: str | None = None
    kubeconfig: str | None = None
    nodes: list[NodeInfo] = []

class TimeRange(BaseModel):
    start: datetime
    end: datetime

class DiagnosticContext(BaseModel):
    session_id: str
    problem_description: str
    time_range: TimeRange
    environment: ClusterInfo
    symptoms: list[str] = []
    priority: Severity = Severity.MEDIUM
    category: ProblemCategory | None = None
    
    collected_data: dict[str, object] = {}
    metadata: dict[str, object] = {}

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: dict[str, object] = {}

class Hypothesis(BaseModel):
    id: str
    problem: str
    confidence: float
    evidence: list[str]
    actions: list[str]
    source: str

class ValidatedHypothesis(BaseModel):
    hypothesis: Hypothesis
    validation: dict[str, object]
    confirmed: bool
    additional_evidence: list[str] = []

class Solution(BaseModel):
    description: str
    steps: list[str]
    based_on_case: str | None = None
    confidence: float
    prerequisites: list[str] = []
    risks: list[str] = []

class HistoricalCase(BaseModel):
    case_id: str
    title: str
    symptoms: list[str]
    problem: str
    solution: Solution
    created_at: datetime
    similarity_score: float = 0.0

class DiagnosticReport(BaseModel):
    session_id: str
    generated_at: datetime
    summary: str
    problem_category: ProblemCategory
    severity: Severity
    
    hypotheses: list[ValidatedHypothesis]
    top_hypothesis: ValidatedHypothesis | None
    
    similar_cases: list[HistoricalCase]
    recommended_solutions: list[Solution]
    
    collected_evidence: dict[str, object]
    diagnostic_steps: list[dict[str, object]]
    
    next_steps: list[str]
    escalation_needed: bool = False
```

### 8.2 知识库模型

```python
class DiagnosticRule(BaseModel):
    rule_id: str
    name: str
    description: str
    category: ProblemCategory
    conditions: list[dict[str, object]]
    hypothesis: Hypothesis
    priority: int = 0
    enabled: bool = True

class KnowledgeEntry(BaseModel):
    entry_id: str
    title: str
    content: str
    category: ProblemCategory
    tags: list[str]
    embedding: list[float] | None = None
    created_at: datetime
    updated_at: datetime
```

---

## 7. Agent 核心实现

### 7.1 依赖配置

```toml
[project]
name = "dte-diagnostic-agent"
version = "1.0.0"
requires-python = ">=3.14"

[project.dependencies]
langchain = "2.15.4"
langchain-openai = ">=0.3.0"
langchain-community = ">=0.3.0"
openai = ">=1.0.0"
pydantic = ">=2.0.0"
asyncssh = ">=2.14.0"
asyncpg = ">=0.29.0"
kubernetes = ">=28.0.0"
redis = ">=5.0.0"
elasticsearch = ">=8.0.0"
```

### 9.2 Agent 主类 (LangChain 2.15.4)

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    openai_api_key: str
    openai_base_url: str | None = None
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_iterations: int = 15
    verbose: bool = True

class DTEBaseDiagnosticAgent:
    """DTEBaseService 问题诊断 Agent - 基于 LangChain 2.15.4"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        self.tools = self._init_tools()
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.intent_parser = IntentParser(llm=self.llm)
        self.planner = DiagnosticPlanner(llm=self.llm)
        self.reasoning_engine = ReasoningEngine(llm=self.llm)
        self.case_retriever = CaseRetriever()
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=config.verbose,
            max_iterations=config.max_iterations,
            handle_parsing_errors=True
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一个专业的DTEBaseService运维诊断专家。
        
你的任务是帮助用户定位和诊断服务问题。你可以：
1. 分析用户描述的问题现象
2. 连接到指定的服务器节点进行诊断
3. 检查日志、系统指标、数据库状态
4. 查询历史案例库获取相似案例
5. 基于证据推理问题原因
6. 提供详细的诊断报告和解决方案

请根据用户输入，系统性地执行诊断流程，并输出结构化的分析结果。"""
    
    def _init_tools(self) -> list[StructuredTool]:
        return [
            SSHConnectTool(),
            LogAnalysisTool(),
            DatabaseQueryTool(),
            ResourceMonitorTool(),
            CaseSearchTool(),
            K8sOperationTool(),
            ConfigCheckTool(),
            NetworkDiagTool()
        ]
    
    async def diagnose(self, user_input: UserInput) -> DiagnosticReport:
        context = await self.intent_parser.parse(user_input)
        
        similar_cases = await self.case_retriever.search_similar_cases(
            context.problem_description,
            context.symptoms
        )
        
        plan = await self.planner.generate_plan(context, similar_cases)
        
        for step in plan.steps:
            tool = self._get_tool(step.tool_name)
            result = await tool.ainvoke(step.parameters)
            context.collected_data[step.name] = result
        
        hypotheses = await self.reasoning_engine.analyze(context)
        
        validated = await self._validate_hypotheses(context, hypotheses)
        
        report = self._generate_report(
            context=context,
            hypotheses=validated,
            similar_cases=similar_cases
        )
        
        await self._save_diagnostic_session(report)
        
        return report
    
    def _generate_report(
        self,
        context: DiagnosticContext,
        hypotheses: list[ValidatedHypothesis],
        similar_cases: list[HistoricalCase]
    ) -> DiagnosticReport:
        top_hypothesis = max(hypotheses, key=lambda h: h.hypothesis.confidence)
        
        solutions = self._generate_solutions(top_hypothesis, similar_cases)
        
        return DiagnosticReport(
            session_id=context.session_id,
            generated_at=datetime.now(),
            summary=self._generate_summary(context, top_hypothesis),
            problem_category=context.category,
            severity=context.priority,
            hypotheses=hypotheses,
            top_hypothesis=top_hypothesis,
            similar_cases=similar_cases,
            recommended_solutions=solutions,
            collected_evidence=context.collected_data,
            diagnostic_steps=[],
            next_steps=self._generate_next_steps(top_hypothesis),
            escalation_needed=self._check_escalation(top_hypothesis)
        )
```

### 7.3 工具定义 (LangChain 2.15.4 StructuredTool)

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class SSHConnectInput(BaseModel):
    host: str = Field(description="目标主机IP或域名")
    port: int = Field(default=22, description="SSH端口")
    username: str = Field(description="登录用户名")
    password: str | None = Field(default=None, description="登录密码")
    ssh_key_path: str | None = Field(default=None, description="SSH私钥路径")

async def _ssh_connect(
    host: str,
    port: int = 22,
    username: str,
    password: str | None = None,
    ssh_key_path: str | None = None
) -> str:
    connector = SSHConnector()
    session = await connector.connect(NodeInfo(
        host=host, port=port, username=username,
        password=password, ssh_key_path=ssh_key_path
    ))
    return f"Successfully connected to {host}:{port}"

SSHConnectTool = StructuredTool.from_function(
    coroutine=_ssh_connect,
    name="ssh_connect",
    description="连接到目标服务器节点，用于执行远程命令",
    args_schema=SSHConnectInput
)

class LogAnalysisInput(BaseModel):
    session_id: str = Field(description="SSH会话ID")
    log_path: str = Field(description="日志文件路径")
    start_time: str = Field(description="开始时间")
    end_time: str = Field(description="结束时间")
    patterns: list[str] = Field(default=[], description="搜索模式列表")

async def _log_analysis(
    session_id: str,
    log_path: str,
    start_time: str,
    end_time: str,
    patterns: list[str] = []
) -> str:
    session = _get_session(session_id)
    analyzer = LogAnalyzer()
    
    time_range = TimeRange(
        start=datetime.fromisoformat(start_time),
        end=datetime.fromisoformat(end_time)
    )
    
    logs = await analyzer.fetch_logs(session, log_path, time_range)
    
    if patterns:
        matches = await analyzer.search_patterns(logs, patterns)
        return json.dumps([m.model_dump() for m in matches], indent=2)
    
    anomalies = await analyzer.detect_anomalies(logs)
    return json.dumps([a.model_dump() for a in anomalies], indent=2)

LogAnalysisTool = StructuredTool.from_function(
    coroutine=_log_analysis,
    name="log_analysis",
    description="分析服务日志，查找错误、异常和特定模式",
    args_schema=LogAnalysisInput
)

class DatabaseQueryInput(BaseModel):
    db_host: str = Field(description="数据库主机")
    db_port: int = Field(default=5432, description="数据库端口")
    db_name: str = Field(description="数据库名称")
    db_user: str = Field(description="数据库用户")
    db_password: str = Field(description="数据库密码")
    query_type: str = Field(description="查询类型: connections/slow_queries/locks/replication")

async def _database_query(
    db_host: str,
    db_port: int = 5432,
    db_name: str,
    db_user: str,
    db_password: str,
    query_type: str
) -> str:
    db_config = DBConfig(
        host=db_host, port=db_port, database=db_name,
        user=db_user, password=db_password
    )
    
    db_tool = DatabaseQuery()
    
    match query_type:
        case "connections":
            result = await db_tool.check_connections(db_config)
            return json.dumps(result.model_dump(), indent=2)
        case "slow_queries":
            result = await db_tool.check_slow_queries(db_config)
            return json.dumps([r.model_dump() for r in result], indent=2)
        case "locks":
            result = await db_tool.check_locks(db_config)
            return json.dumps([r.model_dump() for r in result], indent=2)
        case "replication":
            result = await db_tool.check_replication_status(db_config)
            return json.dumps(result.model_dump(), indent=2)
        case _:
            return "Unknown query type"

DatabaseQueryTool = StructuredTool.from_function(
    coroutine=_database_query,
    name="database_query",
    description="查询数据库状态，包括连接数、慢查询、锁状态、复制状态",
    args_schema=DatabaseQueryInput
)

class ResourceMonitorInput(BaseModel):
    session_id: str = Field(description="SSH会话ID")
    metrics: list[str] = Field(
        default=["cpu", "memory", "disk", "network"],
        description="要采集的指标列表"
    )

async def _resource_monitor(
    session_id: str,
    metrics: list[str] = ["cpu", "memory", "disk", "network"]
) -> str:
    session = _get_session(session_id)
    monitor = ResourceMonitor()
    
    result = await monitor.get_system_metrics(session, metrics)
    return json.dumps(result.model_dump(), indent=2)

ResourceMonitorTool = StructuredTool.from_function(
    coroutine=_resource_monitor,
    name="resource_monitor",
    description="采集系统资源指标，包括CPU、内存、磁盘、网络",
    args_schema=ResourceMonitorInput
)

class CaseSearchInput(BaseModel):
    problem_description: str = Field(description="问题描述")
    symptoms: list[str] = Field(description="症状列表")
    top_k: int = Field(default=5, description="返回案例数量")

async def _case_search(
    problem_description: str,
    symptoms: list[str],
    top_k: int = 5
) -> str:
    retriever = CaseRetriever()
    
    cases = await retriever.search_similar_cases(
        problem_description, symptoms, top_k
    )
    return json.dumps([c.model_dump() for c in cases], indent=2)

CaseSearchTool = StructuredTool.from_function(
    coroutine=_case_search,
    name="case_search",
    description="搜索历史维护案例库，查找相似案例",
    args_schema=CaseSearchInput
)
```

---

## 8. Prompt 设计

### 8.1 意图理解 Prompt

```
你是一个专业的运维诊断助手，负责分析用户描述的问题并提取关键信息。

用户输入：
{user_input}

请分析以上输入，提取以下信息并以JSON格式返回：

1. problem_description: 问题现象的详细描述
2. time_range: 问题发生的时间范围
   - start: 开始时间 (格式: YYYY-MM-DD HH:MM:SS)
   - end: 结束时间 (格式: YYYY-MM-DD HH:MM:SS)
3. environment: 环境信息
   - cluster_name: 集群名称
   - node_info: 节点登录信息
   - service_name: 服务名称
   - namespace: 命名空间
4. symptoms: 问题症状列表
5. priority: 优先级 (critical/high/medium/low)
6. category: 问题类别 (service_unavailable/performance_degradation/data_inconsistency/network_issue/resource_exhaustion/configuration_error/unknown)

注意：
- 如果用户未提供某些信息，请合理推断或标记为unknown
- 时间信息要转换为标准格式
- symptoms要提取关键症状关键词
```

### 10.2 诊断规划 Prompt

```
你是一个专业的运维诊断规划专家，需要根据问题场景生成诊断计划。

问题信息：
- 问题描述: {problem_description}
- 问题类别: {category}
- 症状: {symptoms}
- 时间范围: {time_range}

相似历史案例：
{similar_cases}

请生成一个详细的诊断计划，包括：
1. 需要收集的信息
2. 需要检查的组件
3. 需要执行的工具和命令
4. 检查的优先级顺序

以JSON格式返回诊断步骤列表：
{{
  "steps": [
    {{
      "name": "步骤名称",
      "description": "步骤描述",
      "tool": "工具名称",
      "parameters": {{}},
      "priority": 优先级数字
    }}
  ]
}}
```

### 10.3 推理分析 Prompt

```
你是一个专业的运维诊断分析专家，需要根据收集的信息分析问题原因。

问题上下文：
{context}

收集的证据：
{collected_evidence}

请分析以上信息，输出：
1. 可能的问题原因（按可能性排序）
2. 每个原因的支持证据
3. 建议的验证方法
4. 推荐的解决方案

以JSON格式返回：
{{
  "hypotheses": [
    {{
      "problem": "问题描述",
      "confidence": 置信度(0-1),
      "evidence": ["证据1", "证据2"],
      "actions": ["建议操作1", "建议操作2"],
      "validation": "验证方法"
    }}
  ]
}}
```

---

## 9. 安全与权限设计

### 9.1 权限控制

```python
class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.rbac = RBACClient()
        self.audit_logger = AuditLogger()
    
    async def check_permission(
        self,
        user: User,
        action: str,
        resource: str
    ) -> bool:
        """检查用户权限"""
        has_permission = await self.rbac.check(user.id, action, resource)
        
        # 记录审计日志
        await self.audit_logger.log(
            user=user.id,
            action=action,
            resource=resource,
            result=has_permission
        )
        
        return has_permission
    
    async def get_allowed_clusters(self, user: User) -> List[str]:
        """获取用户可访问的集群列表"""
        return await self.rbac.get_user_resources(user.id, "cluster")
```

### 11.2 敏感信息保护

```python
class SecretManager:
    """敏感信息管理"""
    
    def __init__(self, vault_client: VaultClient):
        self.vault = vault_client
        self.cache = TTLCache(maxsize=100, ttl=3600)
    
    async def get_credential(self, cluster_name: str) -> Credential:
        """获取集群凭证"""
        if cluster_name in self.cache:
            return self.cache[cluster_name]
        
        cred = await self.vault.read(f"secret/clusters/{cluster_name}")
        self.cache[cluster_name] = cred
        return cred
    
    async def store_diagnostic_result(
        self,
        session_id: str,
        result: DiagnosticReport
    ) -> None:
        """存储诊断结果（脱敏）"""
        sanitized = self._sanitize(result)
        await self.storage.save(session_id, sanitized)
    
    def _sanitize(self, data: Any) -> Any:
        """脱敏处理"""
        sensitive_fields = ['password', 'ssh_key', 'token', 'secret']
        # 递归处理，替换敏感字段
        ...
```

### 11.3 操作审计

```python
class AuditLogger:
    """操作审计日志"""
    
    async def log(
        self,
        user: str,
        action: str,
        resource: str,
        result: bool,
        details: Dict = None
    ):
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "result": "success" if result else "failure",
            "details": details or {}
        }
        await self.db.insert("audit_logs", audit_entry)
```

---

## 10. 部署架构

### 10.1 本地单机部署方案

系统采用本地单机部署方案，适用于小规模运维场景和快速验证需求。通过systemd服务或直接命令启动，简化部署复杂度。

```
┌─────────────────────────────────────────────────────────────────────┐
│                          本地单机部署架构                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         单机服务进程                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    DTE Diagnostic Agent                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │  │
│  │  │ API Server  │  │   Agent     │  │   Tools     │            │  │
│  │  │  (FastAPI)  │  │   (LangChain)│  │  (SSH/DB等) │            │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         本地数据存储                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ 会话存储     │  │  案例库      │  │  向量存储    │               │
│  │ (本地文件)   │  │  (本地文件)  │  │  (FAISS)     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 systemd服务配置

**服务文件位置**: `/etc/systemd/system/dte-diagnostic-agent.service`

```ini
[Unit]
Description=DTEBaseService Diagnostic Agent
After=network.target

[Service]
Type=simple
User=dte-agent
Group=dte-agent
WorkingDirectory=/opt/dte-diagnostic-agent
ExecStart=/usr/bin/python3.14 -m dte_diagnostic_agent --config /etc/dte-diagnostic-agent/config.yaml
ExecStop=/bin/kill -TERM $MAINPID
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 10.3 安装脚本说明

**install.sh**:

```bash
#!/bin/bash

INSTALL_DIR="/opt/dte-diagnostic-agent"
CONFIG_DIR="/etc/dte-diagnostic-agent"
DATA_DIR="/var/lib/dte-diagnostic-agent"
LOG_DIR="/var/log/dte-diagnostic-agent"

mkdir -p $INSTALL_DIR $CONFIG_DIR $DATA_DIR $LOG_DIR
mkdir -p $DATA_DIR/sessions $DATA_DIR/cases $DATA_DIR/vector_store

cp -r src $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/

pip install -r $INSTALL_DIR/requirements.txt

cp config.yaml.example $CONFIG_DIR/config.yaml

useradd -r -d $DATA_DIR -s /bin/bash dte-agent

chown -R dte-agent:dte-agent $DATA_DIR $LOG_DIR
chmod 750 $DATA_DIR $LOG_DIR

cp systemd/dte-diagnostic-agent.service /etc/systemd/system/
systemctl daemon-reload

echo "安装完成！"
echo "请编辑 $CONFIG_DIR/config.yaml 配置文件"
echo "然后执行 systemctl start dte-diagnostic-agent 启动服务"
```

### 10.4 启动参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | ~/.dte-diag/config.yaml |
| `--port` | 服务监听端口 | 8080 |
| `--host` | 服务监听地址 | 0.0.0.0 |
| `--api-key` | API认证密钥（可覆盖配置） | 从配置文件读取 |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | 从配置文件读取 |
| `--workers` | 工作进程数（单机部署固定为1） | 1 |
| `--dry-run` | 仅验证配置不启动服务 | false |

**命令行启动示例**:

```bash
python3.14 -m dte_diagnostic_agent --config /etc/dte-diagnostic-agent/config.yaml
python3.14 -m dte_diagnostic_agent --port 8080 --log-level DEBUG
python3.14 -m dte_diagnostic_agent --dry-run
```

**systemd管理命令**:

```bash
sudo systemctl start dte-diagnostic-agent
sudo systemctl stop dte-diagnostic-agent
sudo systemctl restart dte-diagnostic-agent
sudo systemctl status dte-diagnostic-agent
sudo journalctl -u dte-diagnostic-agent -f
sudo systemctl enable dte-diagnostic-agent
```

### 10.5 目录结构说明

```
/opt/dte-diagnostic-agent/          # 应用安装目录
├── src/
│   └── dte_diagnostic_agent/
├── config.yaml                      # 默认配置
└── requirements.txt

/etc/dte-diagnostic-agent/           # 系统配置目录
├── config.yaml                      # 主配置文件
└── api-keys.yaml                    # API密钥配置（可选）

/var/lib/dte-diagnostic-agent/       # 数据目录
├── sessions/                        # 诊断会话数据
├── cases/                           # 案例库数据
└── vector_store/                    # 向量存储数据

/var/log/dte-diagnostic-agent/       # 日志目录
├── agent.log                        # 主日志
└── error.log                        # 错误日志
```

---

## 11. 本地部署配置

### 11.1 配置文件结构

**配置文件位置**: `/etc/dte-diagnostic-agent/config.yaml` 或 `~/.dte-diag/config.yaml`

```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 1

llm:
  api_key: your-openai-api-key
  base_url: https://api.openai.com/v1
  model_name: gpt-4o
  temperature: 0.1
  max_iterations: 15

storage:
  session_dir: /var/lib/dte-diagnostic-agent/sessions
  case_dir: /var/lib/dte-diagnostic-agent/cases
  log_dir: /var/log/dte-diagnostic-agent

logging:
  level: INFO
  file: /var/log/dte-diagnostic-agent/agent.log
  max_size: 10MB
  backup_count: 5

auth:
  api_keys:
    - your-api-key-1
    - your-api-key-2

clusters:
  prod-01:
    kubeconfig: /path/to/kubeconfig-prod-01
    ssh_key: ~/.ssh/id_rsa_prod
  prod-02:
    kubeconfig: /path/to/kubeconfig-prod-02
    ssh_key: ~/.ssh/id_rsa_prod
```

### 11.2 配置文件路径优先级

服务启动时按以下优先级查找配置文件：

1. **命令行指定路径**: `--config /path/to/config.yaml`
2. **系统配置目录**: `/etc/dte-diagnostic-agent/config.yaml`
3. **用户配置目录**: `~/.dte-diag/config.yaml`

若配置文件加载失败，服务报错退出并提示配置文件问题。

### 11.3 优雅关闭流程

服务收到SIGTERM信号时执行以下关闭流程：

1. 停止接收新请求
2. 等待现有请求完成（最长30秒）
3. 关闭数据库连接和SSH会话
4. 保存未完成的诊断状态
5. 退出进程

```python
import signal
import asyncio

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        
    def setup_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        self.shutdown_event.set()
    
    async def wait_for_shutdown(self, timeout: int = 30):
        await self.shutdown_event.wait()
        
        pending = asyncio.all_tasks()
        if pending:
            await asyncio.wait(pending, timeout=timeout)
```

---

## 12. 扩展性设计

### 12.1 工具插件机制

```python
from abc import ABC, abstractmethod

class ToolPlugin(ABC):
    """工具插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> type[BaseModel]:
        pass
    
    @abstractmethod
    async def execute(self, params: BaseModel) -> object:
        pass
    
    def to_structured_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            coroutine=self.execute,
            name=self.name,
            description=self.description,
            args_schema=self.input_schema
        )

class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self._tools: dict[str, ToolPlugin] = {}
    
    def register(self, tool: ToolPlugin):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> ToolPlugin | None:
        return self._tools.get(name)
    
    def list_all(self) -> list[ToolPlugin]:
        return list(self._tools.values())
    
    def to_langchain_tools(self) -> list[StructuredTool]:
        return [t.to_structured_tool() for t in self._tools.values()]

class CustomLogInput(BaseModel):
    log_path: str = Field(description="日志路径")
    pattern: str = Field(description="搜索模式")

class CustomLogTool(ToolPlugin):
    @property
    def name(self) -> str:
        return "custom_log_analyzer"
    
    @property
    def description(self) -> str:
        return "自定义日志分析工具"
    
    @property
    def input_schema(self) -> type[BaseModel]:
        return CustomLogInput
    
    async def execute(self, params: CustomLogInput) -> str:
        return f"分析日志 {params.log_path}，模式: {params.pattern}"

registry = ToolRegistry()
registry.register(CustomLogTool())
```

### 12.2 自定义诊断规则

```python
class RulePlugin(ABC):
    """诊断规则插件"""
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        pass
    
    @property
    @abstractmethod
    def category(self) -> ProblemCategory:
        pass
    
    @abstractmethod
    def match(self, context: DiagnosticContext) -> bool:
        pass
    
    @abstractmethod
    def generate_hypothesis(self, context: DiagnosticContext) -> Hypothesis:
        pass

class CustomRule(RulePlugin):
    @property
    def rule_id(self) -> str:
        return "CUSTOM_001"
    
    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.PERFORMANCE_DEGRADATION
    
    def match(self, context: DiagnosticContext) -> bool:
        return "慢查询" in context.symptoms
    
    def generate_hypothesis(self, context: DiagnosticContext) -> Hypothesis:
        return Hypothesis(
            id=f"H_{self.rule_id}",
            problem="数据库索引缺失导致查询性能下降",
            confidence=0.85,
            evidence=["慢查询日志", "高CPU使用率"],
            actions=["检查执行计划", "添加缺失索引"],
            source="custom_rule"
        )
```

---

## 15. 测试策略

### 15.1 单元测试

```python
import pytest
from unittest.mock import AsyncMock, patch
from langchain_openai import ChatOpenAI

class TestDiagnosticAgent:
    
    @pytest.fixture
    def agent_config(self):
        return AgentConfig(
            openai_api_key="test-key",
            model_name="gpt-4o",
            temperature=0.1,
            verbose=True
        )
    
    @pytest.fixture
    def agent(self, agent_config):
        return DTEBaseDiagnosticAgent(agent_config)
    
    @pytest.mark.asyncio
    async def test_intent_parsing(self, agent):
        user_input = UserInput(
            description="服务响应缓慢，用户反馈超时",
            time_range="2024-01-15 10:00:00 到 2024-01-15 11:00:00",
            environment="生产集群 cluster-prod-01，节点192.168.1.100"
        )
        
        context = await agent.intent_parser.parse(user_input)
        
        assert context.problem_description is not None
        assert context.time_range.start is not None
    
    @pytest.mark.asyncio
    async def test_diagnostic_workflow(self, agent):
        context = DiagnosticContext(
            session_id="test-001",
            problem_description="服务不可用",
            time_range=TimeRange(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 11, 0)
            ),
            environment=ClusterInfo(
                name="test-cluster",
                nodes=[NodeInfo(host="192.168.1.100", username="admin")]
            )
        )
        
        with patch.object(agent, '_execute_tools') as mock_tools:
            mock_tools.return_value = {"logs": [], "metrics": {}}
            
            report = await agent.diagnose(context)
            
            assert report is not None
            assert len(report.hypotheses) > 0

class TestTools:
    
    @pytest.mark.asyncio
    async def test_ssh_connect(self):
        connector = SSHConnector()
        
        with patch('asyncssh.connect') as mock_connect:
            mock_connect.return_value = AsyncMock()
            
            node_info = NodeInfo(host="192.168.1.100", username="admin")
            session = await connector.connect(node_info)
            
            assert session is not None
    
    @pytest.mark.asyncio
    async def test_log_analysis(self):
        analyzer = LogAnalyzer()
        
        logs = [
            LogEntry(timestamp=datetime.now(), level="ERROR", message="Connection timeout", source="app"),
            LogEntry(timestamp=datetime.now(), level="INFO", message="Request received", source="app")
        ]
        
        matches = await analyzer.search_patterns(logs, ["timeout"])
        assert len(matches) == 1
    
    @pytest.mark.asyncio
    async def test_database_query(self):
        db_tool = DatabaseQuery()
        
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_conn.fetchval.return_value = 50
            mock_connect.return_value = mock_conn
            
            result = await db_tool.check_connections(mock_conn)
            assert result.active_connections == 50
```

### 15.2 集成测试

```python
class TestIntegration:
    
    @pytest.fixture
    async def test_environment(self):
        env = await TestEnvironment.start()
        yield env
        await env.stop()
    
    @pytest.mark.asyncio
    async def test_full_diagnostic_flow(self, test_environment):
        agent = DTEBaseDiagnosticAgent(test_environment.config)
        
        user_input = UserInput(
            description="数据库连接超时",
            time_range="最近1小时",
            environment="测试集群"
        )
        
        report = await agent.diagnose(user_input)
        
        assert report.problem_category == ProblemCategory.NETWORK_ISSUE
        assert len(report.recommended_solutions) > 0
    
    @pytest.mark.asyncio
    async def test_case_retrieval(self, test_environment):
        retriever = CaseRetriever()
        
        cases = [
            HistoricalCase(
                case_id="CASE_001",
                title="数据库连接超时",
                symptoms=["超时", "连接失败"],
                problem="数据库连接池耗尽",
                solution=Solution(description="增加连接池大小", steps=[], confidence=0.9),
                created_at=datetime.now()
            )
        ]
        
        retriever.load_cases(cases)
        
        results = await retriever.search_similar_cases(
            "连接超时", ["超时"], top_k=1
        )
        
        assert len(results) > 0
```

---

## 14. 总结

### 14.1 核心特性

1. **智能诊断**: 基于LLM的智能推理，结合规则引擎和历史案例
2. **多源数据整合**: 日志、指标、配置、数据库等多维度分析
3. **知识积累**: 历史案例学习和知识图谱构建
4. **安全可控**: 完善的权限控制和审计机制
5. **可扩展**: 插件化设计，支持自定义工具和规则

### 16.2 技术栈 (基于约束要求)

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| 编程语言 | Python | 3.14 |
| Agent框架 | LangChain | 2.15.4 |
| LLM API | OpenAI API | gpt-4o / gpt-4-turbo |
| 向量数据库 | FAISS / Chroma | - |
| 关系数据库 | PostgreSQL | 16+ |
| 缓存 | Redis | 7+ |
| 日志存储 | Elasticsearch | 8+ |
| 容器编排 | Kubernetes | 1.28+ |
| 监控 | Prometheus + Grafana | - |
| SSH库 | asyncssh | 2.14+ |
| 数据库驱动 | asyncpg | 0.29+ |
| K8s客户端 | kubernetes | 28+ |

**LangChain 2.15.4 核心模块使用**:
- `langchain_openai.ChatOpenAI` - OpenAI LLM 接口
- `langchain_core.tools.StructuredTool` - 工具定义
- `langchain_core.prompts.ChatPromptTemplate` - Prompt模板
- `langchain.agents.create_tool_calling_agent` - Agent创建
- `langchain.agents.AgentExecutor` - Agent执行器

### 14.3 实施路线

**第一阶段（MVP）**
- 基础Agent框架搭建
- 核心工具实现（SSH、日志、数据库）
- 基本诊断流程

**第二阶段**
- 知识库建设
- 规则引擎完善
- Web界面开发

**第三阶段**
- 多集群支持
- 高级分析功能
- 性能优化

---

## 15. 项目目录结构

```
dte-diagnostic-agent/
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 项目说明
├── design.md                   # 设计文档
│
├── src/
│   └── dte_diagnostic_agent/
│       ├── __init__.py
│       ├── main.py             # 入口文件
│       ├── config.py           # 配置管理
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── core.py         # Agent主类
│       │   ├── intent_parser.py # 意图解析
│       │   ├── planner.py      # 诊断规划
│       │   └ reasoning.py      # 推理引擎
│       │   └ workflow.py       # 工作流
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── ssh_tool.py     # SSH连接工具
│       │   ├── log_tool.py     # 日志分析工具
│       │   ├── db_tool.py      # 数据库查询工具
│       │   ├── monitor_tool.py # 指标采集工具
│       │   ├── case_tool.py    # 案例检索工具
│       │   ├── k8s_tool.py     # K8s操作工具
│       │   └ registry.py       # 工具注册中心
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── context.py      # 诊断上下文模型
│       │   ├── report.py       # 诊断报告模型
│       │   ├── hypothesis.py   # 假设模型
│       │   └ case.py           # 案例模型
│       │
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── intent_prompt.py # 意图解析Prompt
│       │   ├── plan_prompt.py   # 诊断规划Prompt
│       │   ├── reason_prompt.py # 推理分析Prompt
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── session_store.py # 会话存储
│       │   ├── case_store.py    # 案例存储
│       │   └ vector_store.py    # 向量存储
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py        # API路由
│       │   ├── schemas.py       # API模型
│       │
│       └ utils/
│           ├── __init__.py
│           ├── logger.py        # 日志工具
│           ├── security.py      # 安全工具
│           └ audit.py          # 审计工具
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 测试配置
│   ├── test_agent/
│   │   ├── test_core.py
│   │   ├── test_intent.py
│   │   └ test_planner.py
│   ├── test_tools/
│   │   ├── test_ssh.py
│   │   ├── test_log.py
│   │   ├── test_db.py
│   ├── test_integration/
│       └ test_full_flow.py
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yaml
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│
├── docs/
│   ├── api.md                   # API文档
│   ├── tools.md                 # 工具文档
│   ├── prompts.md               # Prompt文档
│
└── examples/
    ├── sample_cases.json        # 示例案例
    ├── sample_diagnostic.py     # 示例诊断流程
```

---

## 18. 快速启动示例

### 18.1 基本使用

```python
import asyncio
from dte_diagnostic_agent import DTEBaseDiagnosticAgent, AgentConfig

async def main():
    config = AgentConfig(
        openai_api_key="your-api-key",
        openai_base_url="https://api.openai.com/v1",
        model_name="gpt-4o",
        temperature=0.1
    )
    
    agent = DTEBaseDiagnosticAgent(config)
    
    result = await agent.diagnose({
        "description": "DTEBaseService服务响应缓慢，频繁超时",
        "time_range": {
            "start": "2024-01-15 10:00:00",
            "end": "2024-01-15 11:00:00"
        },
        "environment": {
            "cluster_name": "cluster-prod-01",
            "node_info": {
                "host": "192.168.1.100",
                "port": 22,
                "username": "admin",
                "ssh_key_path": "/path/to/key"
            },
            "service_name": "DTEBaseService",
            "namespace": "production"
        }
    })
    
    print(f"问题类型: {result.problem_category}")
    print(f"最可能原因: {result.top_hypothesis.hypothesis.problem}")
    print(f"置信度: {result.top_hypothesis.hypothesis.confidence}")
    print(f"建议方案: {result.recommended_solutions[0].description}")

asyncio.run(main())
```

### 18.2 API服务启动

```python
from fastapi import FastAPI
from dte_diagnostic_agent.api import routes

app = FastAPI(title="DTE Diagnostic Agent API")
app.include_router(routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 17. 总结

### 17.1 核心特性

| 特性 | 描述 |
|------|------|
| 智能诊断 | 基于OpenAI GPT-4o的智能推理，结合规则引擎和历史案例 |
| 多源数据整合 | 日志、指标、配置、数据库等多维度分析 |
| 知识积累 | 使用FAISS向量库进行历史案例检索 |
| 安全可控 | 完善的权限控制和审计机制 |
| 可扩展 | 插件化设计，支持自定义工具和规则 |
| 现代化 | 采用Python 3.14和LangChain 2.15.4最新特性 |

### 19.2 技术亮点

**Python 3.14 新特性应用**:
- 使用 `list[str]` / `dict[str, object]` 替代 `List[str]` / `Dict[str, Any]`
- 使用 `str | None` 替代 `Optional[str]`
- 使用 `match-case` 语句进行模式匹配
- 利用改进的异步性能

**LangChain 2.15.4 最佳实践**:
- `StructuredTool.from_function()` 定义工具
- `create_tool_calling_agent()` 创建Agent
- `ChatPromptTemplate.from_messages()` 构建Prompt
- `AgentExecutor` 执行Agent流程

### 19.3 下一步行动

1. 根据本设计文档创建项目骨架
2. 实现核心Agent类和工具
3. 搭建测试环境验证功能
4. 持续优化和扩展能力