# DTE Diagnostic Agent API 接口文档

## 目录

- [1. API 概述](#1-api-概述)
- [2. 认证方式](#2-认证方式)
- [3. API 端点详细说明](#3-api-端点详细说明)
  - [3.1 诊断接口](#31-诊断接口)
  - [3.2 案例库接口](#32-案例库接口)
  - [3.3 集群管理接口](#33-集群管理接口)
  - [3.4 健康检查接口](#34-健康检查接口)
- [4. 错误处理](#4-错误处理)
- [5. 使用示例](#5-使用示例)

---

## 1. API 概述

DTE Diagnostic Agent API 是 DTEBaseService 问题诊断 AI Agent 的 RESTful API 接口，提供智能诊断能力。

### 基础信息

| 项目 | 值 |
|------|-----|
| 基础 URL | `http://localhost:8080` |
| API 前缀 | `/api/v1` |
| API 版本 | `v1` |
| 服务版本 | `0.1.0` |
| 文档地址 | `/docs` (Swagger UI) |
| ReDoc 地址 | `/redoc` |
| OpenAPI 规范 | `/openapi.json` |

### 支持的功能

- **诊断会话**: 提交、跟踪和取消诊断请求
- **案例管理**: 搜索和管理历史诊断案例
- **集群管理**: 监控和管理集群状态
- **健康检查**: 服务健康状态和就绪检查

---

## 2. 认证方式

### 认证机制

API 使用 API Key 进行认证。大多数端点需要认证，健康检查端点为公开访问。

### 认证方式

支持两种方式提供 API Key：

#### 方式一：Authorization Header（推荐）

```http
Authorization: Bearer <api_key>
```

#### 方式二：X-API-Key Header

```http
X-API-Key: <api_key>
```

### 公开端点

以下端点无需认证：

| 端点 | 说明 |
|------|------|
| `/` | 根路径，返回 API 信息 |
| `/docs` | Swagger UI 文档 |
| `/redoc` | ReDoc 文档 |
| `/openapi.json` | OpenAPI 规范 |
| `/api/v1/health` | 健康检查 |
| `/api/v1/ready` | 就绪检查 |

### 认证错误响应

#### 缺少 API Key

```json
{
  "error": "authentication_required",
  "message": "API key required. Provide via Authorization header (Bearer token) or X-API-Key header."
}
```

**HTTP 状态码**: `401 Unauthorized`

#### 无效 API Key

```json
{
  "error": "invalid_api_key",
  "message": "Invalid API key"
}
```

**HTTP 状态码**: `401 Unauthorized`

---

## 3. API 端点详细说明

### 3.1 诊断接口

#### POST /api/v1/diagnose

提交诊断请求。

**请求体**:

```json
{
  "description": "string - 问题描述，必填",
  "time_range": {
    "start": "string - ISO8601 时间格式，可选，默认最近 1 小时",
    "end": "string - ISO8601 时间格式，可选，默认当前时间"
  },
  "environment": {
    "cluster_name": "string - 集群名称，必填",
    "node_info": {
      "host": "string - 节点 IP 或域名，可选",
      "port": "integer - SSH 端口，默认 22",
      "username": "string - 登录用户名，可选",
      "auth_type": "string - 认证类型: password/ssh_key",
      "password": "string - 密码，可选",
      "ssh_key_path": "string - SSH 密钥路径，可选"
    },
    "service_name": "string - 服务名称，默认 DTEBaseService",
    "namespace": "string - K8s 命名空间，可选"
  },
  "symptoms": ["string - 症状列表，可选"],
  "priority": "string - 优先级: critical/high/medium/low，默认 medium",
  "options": {
    "timeout": "integer - 超时时间(秒)，默认 300",
    "dry_run": "boolean - 仅生成计划不执行，默认 false",
    "verbose": "boolean - 详细输出，默认 false"
  }
}
```

**请求示例**:

```json
{
  "description": "数据库连接超时，用户无法登录",
  "time_range": {
    "start": "2024-01-15T09:00:00Z",
    "end": "2024-01-15T10:00:00Z"
  },
  "environment": {
    "cluster_name": "prod-01",
    "node_info": {
      "host": "192.168.1.100",
      "port": 22,
      "username": "admin",
      "auth_type": "ssh_key",
      "ssh_key_path": "~/.ssh/id_rsa"
    },
    "service_name": "DTEBaseService",
    "namespace": "production"
  },
  "symptoms": ["连接超时", "响应缓慢"],
  "priority": "high",
  "options": {
    "timeout": 600,
    "verbose": true
  }
}
```

**响应**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_duration": 300
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功创建诊断任务 |
| 400 | 请求参数无效 |
| 401 | 认证失败 |
| 403 | 无权限访问指定集群 |
| 500 | 服务内部错误 |

---

#### GET /api/v1/diagnose/{session_id}

查询诊断结果。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| format | string | json | 输出格式: json/markdown/text |
| include_evidence | boolean | false | 是否包含收集的证据 |

**响应（进行中）**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "status": "running",
  "progress": {
    "current_step": "collect_evidence",
    "completed_steps": ["initializing"],
    "remaining_steps": ["analyze", "hypothesize", "report"],
    "percentage": 25
  }
}
```

**响应（已完成）**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "status": "completed",
  "generated_at": "2024-01-15T10:35:00Z",
  "summary": "数据库连接池配置不足导致连接超时",
  "problem_category": "database_connection",
  "severity": "high",
  "hypotheses": [
    {
      "id": "h1",
      "problem": "数据库连接池配置不足",
      "confidence": 0.85,
      "evidence": [
        "连接池使用率达到 98%",
        "等待连接数持续增长"
      ],
      "actions": [
        "增加连接池大小",
        "优化连接持有时间"
      ]
    },
    {
      "id": "h2",
      "problem": "存在连接泄漏",
      "confidence": 0.60,
      "evidence": [
        "活跃连接数与业务请求不匹配"
      ],
      "actions": [
        "检查连接释放逻辑",
        "添加连接泄漏检测"
      ]
    }
  ],
  "top_hypothesis": {
    "problem": "数据库连接池配置不足",
    "confidence": 0.85
  },
  "recommended_solutions": [
    {
      "description": "调整数据库连接池配置",
      "steps": [
        "增加最大连接数至 100",
        "调整连接超时时间为 30 秒",
        "启用连接池监控"
      ],
      "confidence": 0.90
    }
  ],
  "similar_cases": [
    {
      "case_id": "CASE-001",
      "title": "数据库连接池耗尽解决方案",
      "similarity": 0.92
    }
  ],
  "next_steps": [
    "应用连接池配置变更",
    "监控系统性能指标",
    "24 小时后复查效果"
  ],
  "escalation_needed": false
}
```

**响应（失败）**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "status": "failed",
  "error": "无法连接到目标节点: Connection refused"
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回结果 |
| 404 | 会话不存在 |
| 410 | 会话已过期 |

---

#### DELETE /api/v1/diagnose/{session_id}

取消诊断任务。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "status": "cancelled",
  "cancelled_at": "2024-01-15T10:31:00Z"
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 任务取消成功 |
| 400 | 无法取消已完成/失败/已取消的任务 |
| 404 | 会话不存在 |

---

#### GET /api/v1/diagnose/list

列出诊断历史。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 20 | 返回数量，范围 1-100 |
| offset | integer | 0 | 偏移量 |
| status | string | all | 状态筛选: all/pending/running/completed/failed/cancelled |
| cluster | string | - | 集群名称筛选 |
| start_date | string | - | 开始日期筛选 |
| end_date | string | - | 结束日期筛选 |

**响应**:

```json
{
  "total": 50,
  "items": [
    {
      "session_id": "diag-20240115103000-a1b2c3d4",
      "description": "数据库连接超时",
      "cluster_name": "prod-01",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z"
    },
    {
      "session_id": "diag-20240115110000-e5f6g7h8",
      "description": "服务响应缓慢",
      "cluster_name": "prod-02",
      "status": "running",
      "created_at": "2024-01-15T11:00:00Z",
      "completed_at": null
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回列表 |

---

### 3.2 案例库接口

#### GET /api/v1/cases/search

搜索历史案例。

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索关键词 |
| symptoms | string | 否 | - | 症状筛选，逗号分隔 |
| category | string | 否 | - | 问题类别筛选 |
| limit | integer | 否 | 10 | 返回数量，范围 1-100 |

**请求示例**:

```
GET /api/v1/cases/search?query=连接超时&symptoms=慢查询,高延迟&limit=5
```

**响应**:

```json
{
  "total": 3,
  "items": [
    {
      "case_id": "CASE-001",
      "title": "数据库连接超时",
      "symptoms": ["connection_timeout", "slow_response"],
      "problem": "数据库连接池耗尽",
      "solution_summary": "增加连接池大小并优化连接处理",
      "similarity": 0.85,
      "created_at": "2024-01-10T08:00:00Z"
    },
    {
      "case_id": "CASE-002",
      "title": "API 响应延迟",
      "symptoms": ["high_latency", "timeout"],
      "problem": "网络带宽不足",
      "solution_summary": "升级网络配置，增加带宽",
      "similarity": 0.72,
      "created_at": "2024-01-12T14:30:00Z"
    }
  ]
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回搜索结果 |

---

#### POST /api/v1/cases

创建新案例（从诊断结果保存）。

**请求体**:

```json
{
  "session_id": "diag-20240115103000-a1b2c3d4",
  "title": "数据库连接池耗尽解决方案",
  "tags": ["database", "connection", "pool"]
}
```

**响应**:

```json
{
  "case_id": "CASE-ABC12345",
  "created_at": "2024-01-15T10:40:00Z"
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 201 | 成功创建案例 |
| 400 | 请求参数无效 |
| 404 | 诊断会话不存在 |

---

#### GET /api/v1/cases/{case_id}

获取案例详情。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| case_id | string | 案例 ID |

**响应**:

```json
{
  "case_id": "CASE-001",
  "title": "数据库连接池耗尽解决方案",
  "symptoms": ["connection_timeout", "slow_response"],
  "problem": "数据库连接池配置不足导致连接超时",
  "solution": {
    "description": "调整数据库连接池配置并优化连接管理",
    "steps": [
      "增加最大连接数至 100",
      "调整连接超时时间为 30 秒",
      "启用连接池监控",
      "优化连接释放逻辑"
    ]
  },
  "metadata": {
    "cluster": "prod-01",
    "service": "DTEBaseService",
    "created_at": "2024-01-10T08:00:00Z"
  }
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回案例详情 |
| 404 | 案例不存在 |

---

### 3.3 集群管理接口

#### GET /api/v1/clusters

列出可用集群。

**响应**:

```json
{
  "clusters": [
    {
      "name": "prod-01",
      "type": "k8s",
      "status": "available",
      "services": ["DTEBaseService", "PostgreSQL", "Redis"],
      "nodes": [
        {"host": "192.168.1.10", "status": "healthy"},
        {"host": "192.168.1.11", "status": "healthy"},
        {"host": "192.168.1.12", "status": "healthy"}
      ]
    },
    {
      "name": "prod-02",
      "type": "k8s",
      "status": "available",
      "services": ["DTEBaseService", "MySQL"],
      "nodes": [
        {"host": "192.168.2.10", "status": "healthy"},
        {"host": "192.168.2.11", "status": "healthy"}
      ]
    },
    {
      "name": "dev-01",
      "type": "standalone",
      "status": "available",
      "services": ["DTEBaseService"],
      "nodes": [
        {"host": "10.0.0.100", "status": "healthy"}
      ]
    }
  ]
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回集群列表 |

---

#### GET /api/v1/clusters/{cluster_name}/status

获取集群状态。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| cluster_name | string | 集群名称 |

**响应**:

```json
{
  "cluster_name": "prod-01",
  "status": "available",
  "nodes": [
    {
      "host": "192.168.1.10",
      "cpu_usage": 45.5,
      "memory_usage": 62.3,
      "disk_usage": 35.0,
      "status": "healthy"
    },
    {
      "host": "192.168.1.11",
      "cpu_usage": 38.2,
      "memory_usage": 55.1,
      "disk_usage": 42.5,
      "status": "healthy"
    },
    {
      "host": "192.168.1.12",
      "cpu_usage": 52.8,
      "memory_usage": 71.4,
      "disk_usage": 38.9,
      "status": "healthy"
    }
  ],
  "services": [
    {
      "name": "DTEBaseService",
      "status": "running",
      "pods": ["dtebaseservice-0", "dtebaseservice-1", "dtebaseservice-2"]
    },
    {
      "name": "PostgreSQL",
      "status": "running",
      "pods": ["postgresql-0"]
    },
    {
      "name": "Redis",
      "status": "running",
      "pods": ["redis-master-0", "redis-replica-0"]
    }
  ]
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回集群状态 |
| 404 | 集群不存在 |

---

### 3.4 健康检查接口

以下端点为公开访问，无需认证。

#### GET /api/v1/health

服务健康检查。

**响应**:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "llm": "available",
    "database": "available",
    "vector_store": "available"
  }
}
```

**组件状态值**:

| 状态 | 说明 |
|------|------|
| available | 组件正常可用 |
| unavailable | 组件不可用 |
| degraded | 组件降级运行 |

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 服务健康 |

---

#### GET /api/v1/ready

服务就绪检查。

**响应**:

```json
{
  "ready": true
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 服务就绪 |

---

#### GET /api/v1/config

获取当前配置。

**响应**:

```json
{
  "model_name": "gpt-4",
  "temperature": 0.7,
  "max_iterations": 10,
  "timeout": 300,
  "available_tools": [
    "log_analyzer",
    "metric_collector",
    "service_checker",
    "database_probe",
    "network_diagnostic"
  ]
}
```

**状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功返回配置 |

---

## 4. 错误处理

### 标准错误响应格式

```json
{
  "error": "error_type",
  "message": "详细错误信息",
  "details": {
    "field": "额外错误详情"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 请求参数无效 |
| 401 | 认证失败 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 410 | 资源已过期 |
| 500 | 服务内部错误 |

### 常见错误示例

#### 参数验证错误 (400)

```json
{
  "error": "validation_error",
  "message": "请求参数验证失败",
  "details": {
    "description": "该字段为必填项",
    "environment.cluster_name": "该字段为必填项"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 资源不存在 (404)

```json
{
  "error": "not_found",
  "message": "Session diag-xxx not found",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 内部服务器错误 (500)

```json
{
  "error": "internal_error",
  "message": "服务内部错误，请稍后重试",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 5. 使用示例

### Python 示例

#### 提交诊断请求

```python
import requests

API_URL = "http://localhost:8080/api/v1"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 提交诊断请求
diagnose_request = {
    "description": "数据库连接超时，用户无法登录",
    "environment": {
        "cluster_name": "prod-01",
        "service_name": "DTEBaseService"
    },
    "priority": "high"
}

response = requests.post(
    f"{API_URL}/diagnose",
    json=diagnose_request,
    headers=headers
)

result = response.json()
session_id = result["session_id"]
print(f"诊断会话已创建: {session_id}")
```

#### 查询诊断结果

```python
import time

# 轮询查询诊断结果
while True:
    response = requests.get(
        f"{API_URL}/diagnose/{session_id}",
        headers=headers
    )
    result = response.json()
    
    if result["status"] == "completed":
        print("诊断完成!")
        print(f"问题摘要: {result['summary']}")
        print(f"置信度: {result['top_hypothesis']['confidence']}")
        break
    elif result["status"] == "failed":
        print(f"诊断失败: {result['error']}")
        break
    else:
        print(f"进度: {result['progress']['percentage']}%")
        time.sleep(5)
```

#### 搜索案例

```python
# 搜索历史案例
response = requests.get(
    f"{API_URL}/cases/search",
    params={
        "query": "连接超时",
        "limit": 5
    },
    headers=headers
)

cases = response.json()
for case in cases["items"]:
    print(f"案例: {case['title']} (相似度: {case['similarity']})")
```

### cURL 示例

#### 提交诊断请求

```bash
curl -X POST "http://localhost:8080/api/v1/diagnose" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "数据库连接超时",
    "environment": {
      "cluster_name": "prod-01"
    },
    "priority": "high"
  }'
```

#### 查询诊断状态

```bash
curl -X GET "http://localhost:8080/api/v1/diagnose/diag-20240115103000-a1b2c3d4" \
  -H "Authorization: Bearer your-api-key"
```

#### 列出诊断历史

```bash
curl -X GET "http://localhost:8080/api/v1/diagnose/list?limit=10&status=completed" \
  -H "Authorization: Bearer your-api-key"
```

#### 取消诊断任务

```bash
curl -X DELETE "http://localhost:8080/api/v1/diagnose/diag-20240115103000-a1b2c3d4" \
  -H "Authorization: Bearer your-api-key"
```

#### 搜索案例

```bash
curl -X GET "http://localhost:8080/api/v1/cases/search?query=连接超时&limit=5" \
  -H "Authorization: Bearer your-api-key"
```

#### 获取集群状态

```bash
curl -X GET "http://localhost:8080/api/v1/clusters/prod-01/status" \
  -H "Authorization: Bearer your-api-key"
```

#### 健康检查（无需认证）

```bash
curl -X GET "http://localhost:8080/api/v1/health"
```

### JavaScript/TypeScript 示例

```typescript
const API_URL = "http://localhost:8080/api/v1";
const API_KEY = "your-api-key";

const headers = {
  "Authorization": `Bearer ${API_KEY}`,
  "Content-Type": "application/json"
};

// 提交诊断请求
async function submitDiagnosis() {
  const response = await fetch(`${API_URL}/diagnose`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      description: "数据库连接超时",
      environment: {
        cluster_name: "prod-01"
      },
      priority: "high"
    })
  });
  
  return response.json();
}

// 查询诊断结果
async function getDiagnosisResult(sessionId: string) {
  const response = await fetch(`${API_URL}/diagnose/${sessionId}`, {
    headers
  });
  
  return response.json();
}

// 轮询直到完成
async function waitForDiagnosis(sessionId: string): Promise<any> {
  while (true) {
    const result = await getDiagnosisResult(sessionId);
    
    if (result.status === "completed" || result.status === "failed") {
      return result;
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}
```

---

## 附录

### 数据类型定义

#### DiagnoseStatus（诊断状态）

| 值 | 说明 |
|------|------|
| pending | 等待处理 |
| running | 正在执行 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

#### Priority（优先级）

| 值 | 说明 |
|------|------|
| critical | 紧急 |
| high | 高 |
| medium | 中 |
| low | 低 |

#### ComponentStatus（组件状态）

| 值 | 说明 |
|------|------|
| available | 可用 |
| unavailable | 不可用 |
| degraded | 降级 |

### 版本信息

- API 版本: v1
- 服务版本: 0.1.0
- 文档更新日期: 2026-05-04