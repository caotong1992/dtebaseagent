# 修复知识库案例文件格式问题 Spec

## Why

知识库检索返回为0，原因是 CASE-020 案例文件格式错误导致解析失败，无法被检索到。

## 问题分析

### 问题现象
- 用户输入诊断任务描述："采集任务失败"
- 知识库检索返回结果为 0
- 实际存在 `CASE-020-collector_task_failed.md` 描述采集任务失败场景

### 根本原因

**CASE-020 文件存在两处格式错误**：

1. **错误的 frontmatter 分隔符**
   - 当前使用：`***`
   - 应该使用：`---`

2. **YAML 键中的转义字符**
   - 当前：`case\_id`, `created\_at`, `updated\_at`, `collector\_task`
   - 应该：`case_id`, `created_at`, `updated_at`, `collector_task`

### 代码层面分析

[local_kb.py:69](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/local_kb.py#L69) 中的 `_parse_frontmatter` 方法：

```python
if content.startswith("---"):
    # 解析 frontmatter
```

由于 CASE-020 使用 `***` 开头，条件检查失败，导致：
- `frontmatter` 返回空字典
- `case_id` 被设置为空字符串
- [local_kb.py:29](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/local_kb.py#L29) 的检查 `if case and case.case_id:` 失败
- 案例未被加载到索引中

### 对比其他案例文件

| 文件 | 分隔符 | YAML键格式 | 状态 |
|------|--------|-----------|------|
| CASE-001 | `---` | `case_id` | 正常 |
| CASE-002 | `---` | `case_id` | 正常 |
| CASE-020 | `***` | `case\_id` | **错误** |

## What Changes

- 修复 `cases/collector_task/CASE-020-collector_task_failed.md` 文件格式
  - 将 `***` 替换为 `---`
  - 移除 YAML 键中的转义字符 `\`
- 增强 `_parse_frontmatter` 方法，支持更宽松的分隔符解析（可选）

## Impact

- Affected code: 
  - `cases/collector_task/CASE-020-collector_task_failed.md`
  - `src/dte_diagnostic_agent/kb/local_kb.py` (可选增强)

## ADDED Requirements

### Requirement: Case File Format Validation

案例文件 SHALL 遵循以下格式规范：

#### Scenario: Frontmatter 格式
- **WHEN** 创建或编辑案例文件
- **THEN** frontmatter 必须使用 `---` 作为分隔符
- **AND** YAML 键不得包含转义字符

#### Scenario: 正确格式示例
```markdown
---
case_id: CASE-020
title: 采集任务失败
category: collector_task
---
```

### Requirement: Parser Robustness Enhancement (Optional)

解析器 MAY 支持更宽松的格式解析：

#### Scenario: 容错解析
- **WHEN** frontmatter 使用 `***` 分隔符
- **THEN** 解析器应尝试识别并解析
- **AND** 记录警告日志提示格式错误