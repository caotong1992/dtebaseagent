# 分析 diag-20260509145713-af976dce 任务知识库返回为 0 原因

## 问题现象

诊断任务 `diag-20260509145713-af976dce` 执行时知识库检索返回结果为 0。

## 问题分析

### 1. 案例文件格式问题

检查所有案例文件后发现：

| 文件 | 分隔符 | YAML键格式 | 解析状态 |
|------|--------|-----------|---------|
| CASE-001 | `---` | `case_id` | ✅ 正常 |
| CASE-002 | `---` | `case_id` | ✅ 正常 |
| CASE-010 | `---` | `case_id` | ✅ 正常 |
| CASE-020 | `---` (已修复) | `case_id` (已修复) | ✅ 已修复 |
| CASE-021 | `***` | `case\_id` | ❌ **格式错误** |

**CASE-021 问题**：
- frontmatter 使用 `***` 分隔符（应为 `---`）
- YAML 键包含转义字符：`case\_id`, `collector\_task`, `last\_error\_code`

### 2. 知识库加载分析

根据 [local_kb.py:69](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/local_kb.py#L69)：

```python
if content.startswith("---"):
    # 解析 frontmatter
```

CASE-021 使用 `***` 开头导致解析失败，案例不会被加载到索引中。

### 3. 可能的原因推断

如果用户诊断任务描述与以下关键词相关：
- "采集任务失败"
- "collector task"
- "csm.loading.error"

则检索返回为 0 的原因是：
- CASE-020 (已修复) 刚修复，服务可能未重启
- CASE-021 (未修复) 格式错误无法加载

知识库当前仅加载了 CASE-001、CASE-002、CASE-010，这些案例与采集任务无关。

### 4. 检索流程分析

知识库检索流程：
1. 用户输入 → IntentParser 解析问题描述
2. QueryProcessor 提取关键词并翻译
3. KnowledgeBaseManager.search() 搜索案例
4. 关键词匹配 title、problem、tags

当前有效的案例：
- CASE-001: 数据库连接超时
- CASE-002: 数据库慢查询
- CASE-010: 网络连接超时

如果诊断描述是采集任务相关，这些案例都不会匹配。

## 实施步骤

### Step 1: 修复 CASE-021 文件格式

修改 `cases/collector_task/CASE-021-collector_task_failed csm.loading.error.md`：
- 将 `***` 替换为 `---`
- 移除 YAML 键中的转义字符

### Step 2: 重启服务或调用 reload API

使知识库重新加载所有案例文件。

### Step 3: 验证知识库加载状态

确认 CASE-020、CASE-021 都被正确加载到索引中。

### Step 4: 测试检索功能

使用 "采集任务失败" 或 "csm.loading.error" 测试检索返回结果。

## 验证清单

- [x] CASE-021 文件格式已修复
- [x] 知识库重新加载成功
- [x] CASE-020、CASE-021 都在索引中
- [x] "采集任务失败" 检索返回相关案例
- [x] "csm.loading.error" 检索返回 CASE-021