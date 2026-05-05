# 用户交互接口规范 Spec

## Why
DTEBaseService问题定位AI Agent需要明确的用户交互方式，通过API接口和CLI工具提供服务访问能力，不提供Web UI以简化部署和维护，专注于自动化运维场景的集成需求。

## What Changes
- 定义RESTful API接口规范
- 定义CLI工具命令和参数规范
- 移除Web UI相关设计（从design.md中）
- 明确用户输入数据结构

## Impact
- Affected specs: 用户交互层架构
- Affected code: API路由、CLI入口、输入模型

## ADDED Requirements

### Requirement: API接口服务
系统 SHALL 提供RESTful API接口用于诊断服务调用，支持异步诊断流程。

#### Scenario: 提交诊断请求
- **WHEN** 用户通过POST /api/v1/diagnose提交诊断请求
- **THEN** 系统返回session_id和诊断任务状态

#### Scenario: 查询诊断结果
- **WHEN** 用户通过GET /api/v1/diagnose/{session_id}查询结果
- **THEN** 系统返回完整诊断报告或当前进度

#### Scenario: 列出历史诊断
- **WHEN** 用户通过GET /api/v1/diagnose/list查询历史记录
- **THEN** 系统返回诊断历史列表

### Requirement: CLI工具
系统 SHALL 提供命令行工具dte-diag用于交互式诊断操作。

#### Scenario: 执行诊断命令
- **WHEN** 用户执行 dte-diag diagnose --cluster <cluster_name> --node <node_ip>
- **THEN** 系统启动诊断并输出结果

#### Scenario: 查看历史记录
- **WHEN** 用户执行 dte-diag history --limit 10
- **THEN** 系统输出最近10条诊断记录

#### Scenario: 搜索案例库
- **WHEN** 用户执行 dte-diag search --query "连接超时"
- **THEN** 系统输出匹配的历史案例

### Requirement: 用户输入数据结构
系统 SHALL 定义标准化的诊断请求输入格式。

#### Scenario: 最小输入
- **WHEN** 用户仅提供问题描述和环境名称
- **THEN** 系统尝试基于默认配置进行诊断

#### Scenario: 完整输入
- **WHEN** 用户提供完整的问题描述、时间范围、节点信息、服务名称
- **THEN** 系统执行精确诊断

## MODIFIED Requirements

### Requirement: 用户交互层架构（原设计文档第2节）
用户交互层仅包含CLI工具和API接口两种方式，移除Web UI组件。

原架构：
```
用户交互层: Web UI + CLI工具 + API接口
```

修改后架构：
```
用户交互层: CLI工具 + API接口
```

## REMOVED Requirements

### Requirement: Web UI组件
**Reason**: 简化系统架构，专注于API集成和CLI自动化场景，减少前端维护成本
**Migration**: 用户可通过API接口集成到现有运维平台，或使用CLI工具进行交互式操作

---

## 详细API接口设计

### 1. 诊断接口

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

### 2. 案例库接口

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

### 3. 集群管理接口

#### GET /api/v1/clusters
列出可用集群

**响应**:
```json
{
  "clusters": [
    {
      "name": "string",
      "type": "string - k8s/standalone",
      "status": "string - available/unavailable",
      "services": ["string"],
      "nodes": [
        {
          "host": "string",
          "status": "string"
        }
      ]
    }
  ]
}
```

#### GET /api/v1/clusters/{cluster_name}/status
获取集群状态

**响应**:
```json
{
  "cluster_name": "string",
  "status": "string",
  "nodes": [
    {
      "host": "string",
      "cpu_usage": "float",
      "memory_usage": "float",
      "disk_usage": "float",
      "status": "string"
    }
  ],
  "services": [
    {
      "name": "string",
      "status": "string",
      "pods": ["string"]
    }
  ]
}
```

### 4. 健康检查接口

#### GET /api/v1/health
服务健康检查

**响应**:
```json
{
  "status": "string - healthy/unhealthy",
  "version": "string",
  "components": {
    "llm": "string - available/unavailable",
    "database": "string",
    "vector_store": "string"
  }
}
```

#### GET /api/v1/ready
服务就绪检查

**响应**:
```json
{
  "ready": "boolean"
}
```

### 5. 配置接口

#### GET /api/v1/config
获取当前配置

**响应**:
```json
{
  "model_name": "string",
  "temperature": "float",
  "max_iterations": "integer",
  "timeout": "integer",
  "available_tools": ["string"]
}
```

---

## 详细CLI参数设计

### CLI工具名称: dte-diag

### 全局选项
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

### 主命令

#### 1. diagnose - 执行诊断
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

#### 2. status - 查询诊断状态
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

#### 3. history - 查看历史记录
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

#### 4. cancel - 取消诊断
```
dte-diag cancel <session_id>
```

**示例**:
```bash
dte-diag cancel diag-20240115-001
```

#### 5. search - 搜索案例库
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

#### 6. case - 案例管理
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

#### 7. cluster - 集群管理
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

#### 8. config - 配置管理
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

### 输出格式示例

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

### 配置文件格式

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