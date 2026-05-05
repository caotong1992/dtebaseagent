# 修复DTEBaseDiagnosticAgent初始化从config.yaml获取配置

## 问题分析

### 当前问题

**diagnose.py中的`get_diagnostic_agent()`**（第44-51行）：
```python
def get_diagnostic_agent() -> DTEBaseDiagnosticAgent:
    global _diagnostic_agent
    if _diagnostic_agent is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        _diagnostic_agent = DTEBaseDiagnosticAgent(api_key=api_key)
    return _diagnostic_agent
```

**问题**：
1. 只从环境变量`OPENAI_API_KEY`获取api_key
2. 没有使用config.yaml中的完整LLM配置
3. `base_url`、`model_name`、`temperature`等参数未传递

**config.yaml中的LLM配置**（第6-11行）：
```yaml
llm:
  api_key: sk-c36a8aa43c3d430aba3212a4efadc406
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model_name: qwen-plus
  temperature: 0.1
  max_iterations: 15
```

**DTEBaseDiagnosticAgent初始化参数**（core.py第23-30行）：
```python
def __init__(
    self,
    api_key: str,
    base_url: str | None = None,
    model_name: str = "gpt-4o",
    temperature: float = 0.1,
    kb_manager: KnowledgeBaseManager | None = None
):
```

## 修复方案

### 方案概述

将`AppConfig`传递给`diagnose.py`，让`get_diagnostic_agent()`使用配置中的LLM参数。

### 流程修改

```
__main__.py加载config.yaml → 创建AppConfig
         ↓
    api/main.py create_app(config)
         ↓
    diagnose.py set_diagnostic_agent_config(config.llm)
         ↓
    get_diagnostic_agent()使用config.llm参数初始化Agent
```

## 实施步骤

### 步骤1: 修改diagnose.py添加配置存储

在`api/routes/diagnose.py`添加：
```python
from dte_diagnostic_agent.__main__ import LLMConfig

_llm_config: LLMConfig | None = None

def set_llm_config(config: LLMConfig) -> None:
    global _llm_config
    _llm_config = config

def get_llm_config() -> LLMConfig:
    global _llm_config
    if _llm_config is None:
        raise RuntimeError("LLM config not set")
    return _llm_config
```

### 步骤2: 修改get_diagnostic_agent使用配置

```python
def get_diagnostic_agent() -> DTEBaseDiagnosticAgent:
    global _diagnostic_agent
    if _diagnostic_agent is None:
        config = get_llm_config()
        if not config.api_key:
            raise RuntimeError("LLM API key not configured")
        _diagnostic_agent = DTEBaseDiagnosticAgent(
            api_key=config.api_key,
            base_url=config.base_url,
            model_name=config.model_name,
            temperature=config.temperature
        )
    return _diagnostic_agent
```

### 步骤3: 修改api/main.py传递配置

在`create_app`函数中添加：
```python
from dte_diagnostic_agent.api.routes.diagnose import set_llm_config

def create_app(api_keys, session_dir, config: AppConfig = None) -> FastAPI:
    if config and config.llm:
        set_llm_config(config.llm)
    ...
```

### 步骤4: 修改__main__.py传递完整配置

修改`run_server`函数：
```python
app = create_app(
    api_keys=config.auth.api_keys or None,
    session_dir=config.storage.session_dir,
    config=config
)
```

## 涉及文件

| 文件 | 修改内容 |
|------|----------|
| api/routes/diagnose.py | 添加LLMConfig存储、修改get_diagnostic_agent |
| api/main.py | 传递AppConfig给diagnose路由 |
| __main__.py | run_server传递完整config |

## 测试验证

1. 启动服务使用config.yaml
2. 检查日志确认使用的LLM配置（base_url应为dashscope.aliyuncs.com）
3. 发送诊断请求验证Agent正常工作