# 分析知识库查询返回 0 的原因

## 问题现象

日志显示：
```
知识库查询开始, 关键词: ['采集任务失败', '任务ID', 'Collection task failed', 'taskid']
知识库查询完成, 返回案例数: 0
```

但 CASE-020 的 title 正是 "采集任务失败"，应该能匹配关键词 "采集任务失败"。

## 问题分析

### 1. 案例文件已正确修复

- CASE-020: 格式已修复，使用 `---` 分隔符，YAML 键无转义字符
- CASE-021: 格式已修复，使用 `---` 分隔符，YAML 键无转义字符

### 2. QueryProcessor 已正确初始化

日志显示：
```
2026-05-09 15:13:42 - QueryProcessor initialized, enabled=True, use_llm_translation=True
```

关键词提取正常工作。

### 3. 检索逻辑分析

根据 [local_kb.py:179](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/local_kb.py#L179)：

```python
if term_lower in case.title.lower():
    score += 10
```

关键词 "采集任务失败" 应该匹配 CASE-020 的 title "采集任务失败"。

### 4. 根本原因：LocalMarkdownKB 缺少加载日志

检查 [local_kb.py:21-32](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/local_kb.py#L21-L32) 发现：

```python
def _load_index(self) -> None:
    if not self.case_dir.exists():
        return
    
    for md_file in self.case_dir.glob("**/*.md"):
        try:
            case = self._parse_case_file(md_file)
            if case and case.case_id:
                self.index[case.case_id] = case
        except Exception as e:
            print(f"Warning: Failed to parse {md_file}: {e}")
```

**问题**：
1. **没有日志输出**：无法确认案例是否正确加载
2. **print 语句**：而非 logging，日志文件无法记录解析警告
3. **无加载统计**：不知道最终加载了多少案例

### 5. 可能的问题

1. **case_dir 路径问题**：服务启动时 `case_dir` 可能不是 "./cases"
2. **案例未被加载**：`index` 为空导致所有查询返回 0
3. **诊断 Agent 延迟初始化**：第一次请求时才创建 Agent，可能配置未正确传递

## 实施步骤

### Step 1: 添加 LocalMarkdownKB 加载日志

修改 `src/dte_diagnostic_agent/kb/local_kb.py`：

```python
import logging

class LocalMarkdownKB(KnowledgeBaseInterface):
    def __init__(self, config: LocalKBConfig):
        self.logger = logging.getLogger(__name__)
        self.case_dir = Path(config.case_dir)
        self.index: dict[str, Case] = {}
        self._load_index()
    
    def _load_index(self) -> None:
        if not self.case_dir.exists():
            self.logger.warning(f"Case directory does not exist: {self.case_dir}")
            return
        
        self.logger.info(f"Loading cases from directory: {self.case_dir}")
        
        loaded_count = 0
        failed_count = 0
        
        for md_file in self.case_dir.glob("**/*.md"):
            try:
                case = self._parse_case_file(md_file)
                if case and case.case_id:
                    self.index[case.case_id] = case
                    loaded_count += 1
                    self.logger.debug(f"Loaded case: {case.case_id} - {case.title}")
            except Exception as e:
                failed_count += 1
                self.logger.warning(f"Failed to parse {md_file}: {e}")
        
        self.logger.info(f"Knowledge base loaded: {loaded_count} cases, {failed_count} failed")
```

### Step 2: 添加 KnowledgeBaseManager 初始化日志

修改 `src/dte_diagnostic_agent/kb/manager.py`：

```python
import logging

class KnowledgeBaseManager:
    def __init__(self, config: KnowledgeBaseConfig):
        self.logger = logging.getLogger(__name__)
        config.validate_config()
        self.config = config
        
        match config.mode:
            case "local":
                self.backend = LocalMarkdownKB(config.local)
                self.logger.info(f"Knowledge base initialized with local backend, case_dir={config.local.case_dir}")
            ...
```

### Step 3: 重启服务并检查日志

确认日志输出：
```
Loading cases from directory: ./cases
Loaded case: CASE-001 - 数据库连接超时问题解决
Loaded case: CASE-002 - 数据库慢查询性能优化
Loaded case: CASE-010 - 网络连接超时排查
Loaded case: CASE-020 - 采集任务失败
Loaded case: CASE-021 - 采集任务失败,last_error_code为:csm.loading.error
Knowledge base loaded: 5 cases, 0 failed
```

### Step 4: 测试检索功能

再次创建诊断任务，确认知识库查询返回非 0。

## 验证清单

- [x] LocalMarkdownKB 添加 logging 模块导入
- [x] _load_index 添加加载统计日志
- [x] KnowledgeBaseManager 添加初始化日志
- [x] 修复 _parse_case_file 中 None 值处理（使用 `or []` 替代默认值）
- [x] 重启服务后日志显示 Knowledge base loaded: X cases
- [x] 知识库查询返回案例数 > 0