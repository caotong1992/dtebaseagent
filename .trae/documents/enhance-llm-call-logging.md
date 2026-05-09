# 增强 LLM 调用日志输出

## 问题现象

生成任务计划日志较少，缺少对大模型输入输出的详细信息记录，难以调试和追踪 LLM 调用过程。

## 当前日志情况分析

| 模块 | 文件 | 当前日志状态 |
|------|------|-------------|
| IntentParser | intent_parser.py | ✅ 较完善：session_id、prompt长度、token信息、响应预览 |
| DiagnosticPlanner | planner.py | ⚠️ 不足：无session_id、prompt/debug级别、无token信息 |
| ReasoningEngine | reasoning.py | ⚠️ 不足：无session_id、无prompt记录、无token信息 |
| TranslatorService | translator.py | ❌ 缺失：完全无日志 |

### 详细分析

**IntentParser** 已有的日志（作为参考模板）：
```python
logger.info(f"[{session_id}] [IntentParser] LLM调用开始, prompt长度: {len(prompt)}")
logger.info(f"[{session_id}] [IntentParser] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
logger.info(f"[{session_id}] [IntentParser] LLM响应: {response.content[:500]}...")
```

**DiagnosticPlanner** 缺少的日志：
- 第 45 行：`logger.debug(f"[Planner] LLM调用输入...` → 应改为 INFO 级别
- 无 session_id 关联
- 无 token 信息提取

**ReasoningEngine** 缺少的日志：
- `_llm_reasoning` 方法无 prompt 记录
- 无响应内容预览
- 无 token 信息

**TranslatorService** 缺少的日志：
- 完全没有日志输出
- 无法追踪翻译调用过程

## 实施步骤

### Step 1: 增强 DiagnosticPlanner 日志

修改 `src/dte_diagnostic_agent/agent/planner.py`：

1. 添加 session_id 参数传递
2. 添加 token 信息提取方法（复用 IntentParser 的 `_extract_token_info`）
3. 将 debug 级别改为 info 级别
4. 增加 prompt 完整内容日志（可选截断）

```python
async def generate_plan(
    self,
    context: DiagnosticContext,
    similar_cases: list[Case]
) -> DiagnosticPlan:
    session_id = context.session_id
    
    # 记录 prompt 信息
    logger.info(f"[{session_id}] [Planner] LLM调用开始, prompt长度: {len(prompt)}")
    
    # 提取 token 信息
    token_info = self._extract_token_info(response)
    logger.info(f"[{session_id}] [Planner] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
    
    # 记录响应内容
    logger.info(f"[{session_id}] [Planner] LLM响应: {response.content[:500]}...")
```

### Step 2: 增强 ReasoningEngine 日志

修改 `src/dte_diagnostic_agent/agent/reasoning.py`：

1. 添加 session_id 关联（从 context 获取）
2. 添加 prompt 和响应内容日志
3. 添加 token 信息提取

```python
async def _llm_reasoning(self, context: DiagnosticContext) -> list[Hypothesis]:
    session_id = context.session_id
    
    # 记录 prompt 信息
    logger.info(f"[{session_id}] [Reasoning] LLM调用开始, prompt长度: {len(prompt)}")
    
    # 提取 token 信息
    token_info = self._extract_token_info(response)
    logger.info(f"[{session_id}] [Reasoning] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
    
    # 记录响应内容
    logger.info(f"[{session_id}] [Reasoning] LLM响应: {response.content[:500]}...")
```

### Step 3: 增强 TranslatorService 日志

修改 `src/dte_diagnostic_agent/kb/translator.py`：

1. 添加 logging 模块
2. 记录翻译调用的输入输出
3. 记录耗时和缓存命中情况

```python
import logging
import time

class TranslatorService:
    def __init__(self, llm: ChatOpenAI | None = None, cache_size: int = 100):
        self.logger = logging.getLogger(__name__)
        ...
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        # 缓存命中日志
        if cache_key in self._cache:
            self.logger.debug(f"[Translator] 缓存命中: {text[:30]} -> {source_lang}:{target_lang}")
            return self._cache[cache_key]
        
        # LLM调用日志
        self.logger.info(f"[Translator] LLM调用开始, 翻译: {text[:50]} ({source_lang}->{target_lang})")
        
        start_time = time.time()
        response = await self.llm.ainvoke(prompt)
        elapsed_ms = (time.time() - start_time) * 1000
        
        self.logger.info(f"[Translator] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, 结果: {result[:50]}")
```

### Step 4: 统一 token 信息提取工具

创建 `src/dte_diagnostic_agent/utils/llm_logger.py`：

```python
"""LLM logging utilities."""

import logging
import time

logger = logging.getLogger(__name__)


def extract_token_info(response) -> str:
    """从LLM响应中提取token使用信息"""
    ...

def log_llm_call(
    session_id: str,
    module: str,
    prompt: str,
    response,
    elapsed_ms: float
) -> None:
    """统一的LLM调用日志记录"""
    ...
```

## 验证清单

- [x] DiagnosticPlanner 添加 session_id 关联
- [x] DiagnosticPlanner 添加 token 信息提取
- [x] DiagnosticPlanner 将日志级别改为 INFO
- [x] ReasoningEngine 添加 prompt 和响应日志
- [x] ReasoningEngine 添加 token 信息
- [x] TranslatorService 添加 logging 模块
- [x] TranslatorService 添加调用日志
- [x] 重启服务后日志显示完整的 LLM 输入输出信息