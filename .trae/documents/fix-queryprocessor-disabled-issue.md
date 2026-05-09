# 修复 QueryProcessor disabled or not configured 问题

## 问题现象

日志显示 `QueryProcessor disabled or not configured`，导致知识库检索时未启用查询预处理功能（关键词提取和翻译）。

## 问题分析

### 配置文件已正确配置

[config.yaml](file:///d:/code/dtebaseagent/config.yaml) 中已配置：

```yaml
knowledge_base:
  mode: local
  query_processor:
    enabled: true
    use_llm_translation: true
    cache_size: 100
```

### 问题根源：配置未传递到 Agent

检查代码发现两处遗漏：

**1. [main.py:117-131](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/api/main.py#L117-L131)** 创建 `KnowledgeBaseConfig` 时未传递 `query_processor`：

```python
kb_config = KnowledgeBaseConfig(
    mode=config.knowledge_base.get("mode", "local"),
    local=LocalKBConfig(
        case_dir=config.knowledge_base.get("local", {}).get("case_dir", "./cases")
    )
)
# 缺少 query_processor 参数！
```

**2. [diagnose.py:105-111](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/api/routes/diagnose.py#L105-L111)** 创建 Agent 时未传递 `query_processor_config`：

```python
_diagnostic_agent = DTEBaseDiagnosticAgent(
    api_key=api_key,
    base_url=config.base_url,
    model_name=config.model_name,
    temperature=config.temperature,
    kb_manager=kb_manager
)
# 缺少 query_processor_config 参数！
```

### 代码执行流程分析

1. `load_config()` 加载 YAML → `AppConfig.knowledge_base` 包含 `query_processor` 配置
2. `create_app()` 创建 `KnowledgeBaseConfig` → **遗漏** `query_processor` 传递
3. `get_diagnostic_agent()` 创建 `DTEBaseDiagnosticAgent` → **遗漏** `query_processor_config` 传递
4. Agent 初始化检查 `query_processor_config` 为 None → 输出 "QueryProcessor disabled or not configured"

## 实施步骤

### Step 1: 修复 main.py - 传递 query_processor 配置

修改 `src/dte_diagnostic_agent/api/main.py` 中 `KnowledgeBaseConfig` 创建逻辑：

```python
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig, LocalKBConfig, RemoteKBConfig, QueryProcessorConfig

# 在 create_app 函数中
query_processor_cfg = None
if config.knowledge_base.get("query_processor"):
    qp = config.knowledge_base["query_processor"]
    query_processor_cfg = QueryProcessorConfig(
        enabled=qp.get("enabled", True),
        use_llm_translation=qp.get("use_llm_translation", True),
        cache_size=qp.get("cache_size", 100)
    )

kb_config = KnowledgeBaseConfig(
    mode=config.knowledge_base.get("mode", "local"),
    local=LocalKBConfig(...),
    query_processor=query_processor_cfg
)
```

### Step 2: 修复 diagnose.py - 传递 query_processor_config 给 Agent

修改 `src/dte_diagnostic_agent/api/routes/diagnose.py` 中 `get_diagnostic_agent()` 函数：

```python
def get_diagnostic_agent() -> DTEBaseDiagnosticAgent:
    kb_config = get_kb_config()
    query_processor_config = kb_config.query_processor if kb_config else None
    
    _diagnostic_agent = DTEBaseDiagnosticAgent(
        api_key=api_key,
        base_url=config.base_url,
        model_name=config.model_name,
        temperature=config.temperature,
        kb_manager=kb_manager,
        query_processor_config=query_processor_config
    )
```

### Step 3: 重启服务验证

重启服务并检查日志，确认输出：
- `QueryProcessor initialized, enabled=true, use_llm_translation=true`

### Step 4: 测试检索功能

创建诊断任务，验证日志输出：
- `[QueryProcessor] 开始查询预处理, 原始查询: ...`
- `[QueryProcessor] 预处理完成, 中文关键词: ...`
- `[QueryProcessor] 预处理完成, 英文关键词: ...`

## 验证清单

- [x] main.py 中 QueryProcessorConfig 导入和创建
- [x] main.py 中 KnowledgeBaseConfig 包含 query_processor
- [x] diagnose.py 中传递 query_processor_config 给 Agent
- [x] 重启服务后日志显示 QueryProcessor initialized
- [x] 诊断任务日志显示 QueryProcessor 处理关键词