# 案例库管理方式 Spec

## Why
简化案例库管理方式，采用本地Markdown文件存储案例，便于人工编辑和维护；同时设计可扩展的知识库接口，支持未来接入第三方知识库API，实现本地模式和远程知识库模式的兼容切换。

## What Changes
- 定义本地Markdown文件格式的案例存储方案
- 设计统一的知识库检索接口抽象层
- 实现本地Markdown案例库适配器
- 定义第三方知识库API适配器接口规范
- 支持配置切换两种案例库模式

## Impact
- Affected specs: 案例库存储模块、知识库检索接口
- Affected code: CaseRetriever类、案例存储模块、配置文件

## ADDED Requirements

### Requirement: 本地Markdown案例库
系统 SHALL 支持通过本地Markdown文件管理案例库，文件存储在指定目录下。

#### Scenario: 案例文件存储格式
- **WHEN** 用户在案例目录下创建Markdown文件
- **THEN** 系统按预定义格式解析案例内容

#### Scenario: 案例目录结构
- **WHEN** 系统加载本地案例库
- **THEN** 从配置的案例目录读取所有.md文件并解析

#### Scenario: 案例文件命名规范
- **WHEN** 用户创建新案例文件
- **THEN** 文件名遵循 `CASE-{id}-{title-slug}.md` 格式

### Requirement: 知识库检索接口抽象
系统 SHALL 提供统一的知识库检索接口，支持多种后端实现。

#### Scenario: 接口定义
- **WHEN** 系统需要检索案例
- **THEN** 通过统一的KnowledgeBaseInterface调用，不依赖具体实现

#### Scenario: 模式切换
- **WHEN** 配置文件指定知识库模式为local或remote
- **THEN** 系统自动使用对应的适配器实现

### Requirement: 第三方知识库API适配
系统 SHALL 支持通过API接口对接第三方知识库系统。

#### Scenario: 远程知识库查询
- **WHEN** 配置为remote模式且提供API地址
- **THEN** 通过HTTP请求查询第三方知识库

#### Scenario: 认证配置
- **WHEN** 第三方知识库需要认证
- **THEN** 从配置读取认证信息（API Key或Token）

### Requirement: 模式兼容性
系统 SHALL 保证本地模式和远程模式的功能对等性。

#### Scenario: 相同接口返回格式
- **WHEN** 使用不同模式检索案例
- **THEN** 返回相同的数据结构格式

#### Scenario: 无缝切换
- **WHEN** 用户修改配置切换模式
- **THEN** 无需修改代码，重启服务即可生效

## MODIFIED Requirements

### Requirement: 案例库存储方式（原CaseRetriever类）
案例库存储从向量存储改为可配置的双模式方案。

原实现：
```python
class CaseRetriever:
    def __init__(self, embeddings: OpenAIEmbeddings | None = None):
        self.vector_store: FAISS | None = None
```

修改后实现：
```python
class KnowledgeBaseInterface:
    """知识库检索接口抽象"""
    async def search(query: str, top_k: int) -> list[Case]
    async def get(case_id: str) -> Case | None
    async def save(case: Case) -> str

class LocalMarkdownKB(KnowledgeBaseInterface):
    """本地Markdown文件案例库"""

class RemoteKBClient(KnowledgeBaseInterface):
    """远程知识库API客户端"""
```

---

## 详细设计

### 1. 本地Markdown案例文件格式

**文件命名**: `CASE-{id}-{title-slug}.md`

例如: `CASE-001-db-connection-timeout.md`

**文件内容格式**:
```markdown
---
case_id: CASE-001
title: 数据库连接超时问题解决
category: database
severity: high
created_at: 2024-01-15T10:30:00
updated_at: 2024-01-15T11:00:00
tags:
  - database
  - connection
  - timeout
cluster: prod-01
service: DTEBaseService
---

## 问题现象

数据库连接频繁超时，用户登录失败，服务响应缓慢。

## 症状列表

- 连接超时
- 服务响应缓慢
- 用户登录失败

## 问题原因

数据库连接池配置不足，默认连接数设置为50，高峰期实际需求超过100。

## 分析过程

1. 检查数据库连接状态：`SELECT count(*) FROM pg_stat_activity`
2. 检查连接池配置：发现max_connections=50
3. 分析连接持有时间：发现长事务存在

## 解决方案

### 步骤1: 增加连接池大小
修改配置文件，将连接池大小从50调整为150。

### 步骤2: 优化连接管理
- 设置连接超时时间为30秒
- 启用连接健康检查
- 定期清理空闲连接

### 步骤3: 监控告警
- 配置连接数超过80%时告警
- 配置连接等待时间超过5秒告警

## 验证结果

修改后连接超时问题消失，高峰期连接数维持在100左右，用户登录正常。

## 参考资料

- PostgreSQL连接池最佳实践
- DTEBaseService配置手册

## 关联案例

- CASE-002: 服务响应缓慢
- CASE-005: 数据库锁等待
```

### 2. 案例目录结构

```
/var/lib/dte-diagnostic-agent/cases/
├── database/
│   ├── CASE-001-db-connection-timeout.md
│   ├── CASE-002-db-lock-wait.md
│   └── CASE-003-db-slow-query.md
├── network/
│   ├── CASE-010-network-timeout.md
│   └── CASE-011-dns-resolution-fail.md
├── performance/
│   ├── CASE-020-high-cpu-usage.md
│   └── CASE-021-memory-leak.md
├── service/
│   ├── CASE-030-service-crash.md
│   └── CASE-031-service-start-fail.md
└── index.yaml    # 案例索引文件（可选，加速检索）
```

### 3. 知识库接口抽象设计

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from datetime import datetime

class Case(BaseModel):
    case_id: str
    title: str
    category: str
    severity: str
    symptoms: list[str]
    problem: str
    analysis: str
    solution: list[str]
    verification: str
    references: list[str]
    related_cases: list[str]
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    cluster: str | None
    service: str | None

class SearchResult(BaseModel):
    case: Case
    similarity: float
    match_reason: str

class KnowledgeBaseInterface(ABC):
    """知识库检索接口抽象"""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """搜索相关案例"""
        pass
    
    @abstractmethod
    async def get(self, case_id: str) -> Case | None:
        """获取指定案例"""
        pass
    
    @abstractmethod
    async def save(self, case: Case) -> str:
        """保存新案例"""
        pass
    
    @abstractmethod
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        """列出所有案例"""
        pass
    
    @abstractmethod
    async def delete(self, case_id: str) -> bool:
        """删除案例"""
        pass

class KnowledgeBaseManager:
    """知识库管理器 - 根据配置选择实现"""
    
    def __init__(self, config: KnowledgeBaseConfig):
        self.backend: KnowledgeBaseInterface
        
        match config.mode:
            case "local":
                self.backend = LocalMarkdownKB(config.local)
            case "remote":
                self.backend = RemoteKBClient(config.remote)
            case _:
                raise ValueError(f"Unknown KB mode: {config.mode}")
    
    async def search(self, query: str, **kwargs) -> list[SearchResult]:
        return await self.backend.search(query, **kwargs)
```

### 4. 本地Markdown适配器实现

```python
import os
import re
from pathlib import Path
from datetime import datetime
import yaml
import frontmatter

class LocalMarkdownKB(KnowledgeBaseInterface):
    """本地Markdown文件案例库"""
    
    def __init__(self, config: LocalKBConfig):
        self.case_dir = Path(config.case_dir)
        self.index: dict[str, Case] = {}
        self._load_index()
    
    def _load_index(self):
        """加载所有案例文件"""
        for md_file in self.case_dir.glob("**/*.md"):
            try:
                case = self._parse_case_file(md_file)
                self.index[case.case_id] = case
            except Exception as e:
                print(f"Failed to parse {md_file}: {e}")
    
    def _parse_case_file(self, file_path: Path) -> Case:
        """解析Markdown案例文件"""
        post = frontmatter.load(str(file_path))
        
        content = post.content
        sections = self._parse_sections(content)
        
        return Case(
            case_id=post.get("case_id", ""),
            title=post.get("title", ""),
            category=post.get("category", "unknown"),
            severity=post.get("severity", "medium"),
            symptoms=sections.get("symptoms", []),
            problem=sections.get("problem", ""),
            analysis=sections.get("analysis", ""),
            solution=sections.get("solution", []),
            verification=sections.get("verification", ""),
            references=sections.get("references", []),
            related_cases=post.get("related_cases", []),
            created_at=post.get("created_at", datetime.now()),
            updated_at=post.get("updated_at", datetime.now()),
            tags=post.get("tags", []),
            cluster=post.get("cluster"),
            service=post.get("service"),
        )
    
    def _parse_sections(self, content: str) -> dict[str, object]:
        """解析Markdown内容章节"""
        sections = {}
        pattern = r"##\s+([\w\u4e00-\u9fa5]+)\s*\n(.*?)(?=##\s|$)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for title, body in matches:
            title = title.strip()
            body = body.strip()
            
            if title in ["症状列表", "解决方案", "参考资料"]:
                items = [line.strip().lstrip("- ") for line in body.split("\n") if line.strip().startswith("-")]
                sections[self._translate_section(title)] = items
            else:
                sections[self._translate_section(title)] = body
        
        return sections
    
    def _translate_section(self, chinese_title: str) -> str:
        """中文章节名映射"""
        mapping = {
            "问题现象": "problem",
            "症状列表": "symptoms",
            "问题原因": "problem",
            "分析过程": "analysis",
            "解决方案": "solution",
            "验证结果": "verification",
            "参考资料": "references",
        }
        return mapping.get(chinese_title, chinese_title.lower())
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """关键词搜索案例"""
        results = []
        query_lower = query.lower()
        
        for case in self.index.values():
            if category and case.category != category:
                continue
            
            score = 0
            match_reasons = []
            
            if query_lower in case.title.lower():
                score += 10
                match_reasons.append("标题匹配")
            
            if query_lower in case.problem.lower():
                score += 5
                match_reasons.append("问题描述匹配")
            
            for symptom in (symptoms or []):
                if symptom.lower() in [s.lower() for s in case.symptoms]:
                    score += 3
                    match_reasons.append(f"症状匹配: {symptom}")
            
            for tag in case.tags:
                if query_lower in tag.lower():
                    score += 2
                    match_reasons.append(f"标签匹配: {tag}")
            
            if score > 0:
                results.append(SearchResult(
                    case=case,
                    similarity=score / 20,
                    match_reason="; ".join(match_reasons)
                ))
        
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:top_k]
    
    async def get(self, case_id: str) -> Case | None:
        return self.index.get(case_id)
    
    async def save(self, case: Case) -> str:
        """保存案例为Markdown文件"""
        category_dir = self.case_dir / case.category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        title_slug = re.sub(r"[^\w\u4e00-\u9fa5]", "-", case.title.lower())
        file_name = f"{case.case_id}-{title_slug}.md"
        file_path = category_dir / file_name
        
        frontmatter_dict = {
            "case_id": case.case_id,
            "title": case.title,
            "category": case.category,
            "severity": case.severity,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "tags": case.tags,
            "cluster": case.cluster,
            "service": case.service,
        }
        
        content = self._build_content(case)
        post = frontmatter.Post(content, **frontmatter_dict)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        
        self.index[case.case_id] = case
        return str(file_path)
    
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        cases = list(self.index.values())
        if category:
            cases = [c for c in cases if c.category == category]
        return cases[:limit]
    
    async def delete(self, case_id: str) -> bool:
        if case_id not in self.index:
            return False
        
        case = self.index[case_id]
        category_dir = self.case_dir / case.category
        title_slug = re.sub(r"[^\w\u4e00-\u9fa5]", "-", case.title.lower())
        file_path = category_dir / f"{case_id}-{title_slug}.md"
        
        if file_path.exists():
            file_path.unlink()
        
        del self.index[case_id]
        return True
```

### 5. 远程知识库适配器实现

```python
import httpx
from datetime import datetime

class RemoteKBConfig(BaseModel):
    api_url: str
    api_key: str | None = None
    timeout: int = 30
    headers: dict[str, str] = {}

class RemoteKBClient(KnowledgeBaseInterface):
    """远程知识库API客户端"""
    
    def __init__(self, config: RemoteKBConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.api_url,
            timeout=config.timeout,
            headers=self._build_headers()
        )
    
    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.headers)
        return headers
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """调用远程API搜索案例"""
        response = await self.client.post(
            "/api/v1/kb/search",
            json={
                "query": query,
                "symptoms": symptoms,
                "category": category,
                "top_k": top_k
            }
        )
        response.raise_for_status()
        
        data = response.json()
        return [
            SearchResult(
                case=self._parse_remote_case(item["case"]),
                similarity=item["similarity"],
                match_reason=item.get("match_reason", "")
            )
            for item in data.get("results", [])
        ]
    
    async def get(self, case_id: str) -> Case | None:
        response = await self.client.get(f"/api/v1/kb/cases/{case_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._parse_remote_case(response.json())
    
    async def save(self, case: Case) -> str:
        response = await self.client.post(
            "/api/v1/kb/cases",
            json=case.model_dump()
        )
        response.raise_for_status()
        return response.json().get("case_id")
    
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        response = await self.client.get(
            "/api/v1/kb/cases",
            params={"category": category, "limit": limit}
        )
        response.raise_for_status()
        return [
            self._parse_remote_case(item)
            for item in response.json().get("items", [])
        ]
    
    async def delete(self, case_id: str) -> bool:
        response = await self.client.delete(f"/api/v1/kb/cases/{case_id}")
        return response.status_code == 200
    
    def _parse_remote_case(self, data: dict) -> Case:
        """解析远程API返回的案例数据"""
        return Case(
            case_id=data.get("case_id", ""),
            title=data.get("title", ""),
            category=data.get("category", "unknown"),
            severity=data.get("severity", "medium"),
            symptoms=data.get("symptoms", []),
            problem=data.get("problem", ""),
            analysis=data.get("analysis", ""),
            solution=data.get("solution", []),
            verification=data.get("verification", ""),
            references=data.get("references", []),
            related_cases=data.get("related_cases", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            tags=data.get("tags", []),
            cluster=data.get("cluster"),
            service=data.get("service"),
        )
```

### 6. 配置文件扩展

在config.yaml中添加知识库配置：

```yaml
knowledge_base:
  # 模式选择: local / remote
  mode: local
  
  # 本地Markdown模式配置
  local:
    case_dir: /var/lib/dte-diagnostic-agent/cases
    
  # 远程知识库模式配置（当mode为remote时使用）
  remote:
    api_url: https://kb-api.example.com
    api_key: your-kb-api-key
    timeout: 30
    headers:
      X-Custom-Header: custom-value
```

### 7. API端点适配

现有API端点 `/api/v1/cases` 需适配KnowledgeBaseManager：

```python
from fastapi import APIRouter, Depends
from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager

router = APIRouter(prefix="/cases", tags=["cases"])

def get_kb_manager() -> KnowledgeBaseManager:
    return app_state.kb_manager

@router.get("/search")
async def search_cases(
    query: str,
    symptoms: str | None = None,
    category: str | None = None,
    limit: int = 10,
    kb: KnowledgeBaseManager = Depends(get_kb_manager)
):
    symptoms_list = symptoms.split(",") if symptoms else None
    results = await kb.search(query, symptoms=symptoms_list, category=category, top_k=limit)
    return {"total": len(results), "items": [r.model_dump() for r in results]}
```

### 8. CLI命令适配

CLI命令 `dte-diag case` 需适配新接口：

```python
# dte-diag case show CASE-001
# dte-diag case list --category database
# dte-diag case save <session_id> --title "..." --tags "..."
```

---

## 扩展性设计

### 未来支持的知识库类型

| 类型 | 实现类 | 说明 |
|------|--------|------|
| local | LocalMarkdownKB | 本地Markdown文件 |
| remote | RemoteKBClient | HTTP API远程知识库 |
| elasticsearch | ESKBClient | Elasticsearch检索 |
| milvus | MilvusKBClient | Milvus向量检索 |
| confluent | ConfluentKBClient | Confluence知识库 |

### 新增适配器步骤

1. 继承 `KnowledgeBaseInterface`
2. 实现所有抽象方法
3. 在配置中添加对应配置项
4. 在 `KnowledgeBaseManager` 中注册新模式