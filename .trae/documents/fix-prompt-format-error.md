# 修复诊断任务失败问题

## 问题分析

### 错误日志
```
KeyError: '\n  "steps"'
Traceback (most recent call last):
  File "planner.py", line 35, in generate_plan
    prompt = PLANNING_PROMPT.format(...)
```

### 根因分析
prompt模板（planning.py、reasoning.py）包含JSON示例，使用了花括号 `{}` 表示JSON结构。当调用Python的`.format()`方法时，这些花括号被误认为是占位符，导致`KeyError`。

**问题示例**：
```python
PLANNING_PROMPT = """
请以JSON格式返回：
{
  "steps": [...]   # 这里的 { 被误认为是占位符
}
"""
PLANNING_PROMPT.format(problem_description="...")  # KeyError: '\n  "steps"'
```

### 涉及文件
| 文件 | 是否需要修复 | 原因 |
|------|-------------|------|
| prompts/planning.py | ✅ 需要 | 使用`.format()`，JSON示例花括号未转义 |
| prompts/reasoning.py | ✅ 需要 | 使用`.format()`，JSON示例花括号未转义 |
| prompts/intent.py | ❌ 不需要 | 只有一个占位符 `{user_input}`，JSON在说明文字中无花括号 |

## 修复方案

### 步骤1: 修改 planning.py
将JSON示例中的花括号转义为双花括号：
- `{` → `{{`（非占位符的花括号）
- `}` → `}}`（非占位符的花括号）
- 保留 `{problem_description}`, `{category}`, `{symptoms}`, `{time_range}`, `{cluster_name}`, `{similar_cases}` 不变

**修改内容**：
```python
PLANNING_PROMPT = """...
请以JSON格式返回诊断步骤列表：
{{    # 转义
  "steps": [    # 无花括号，无需转义
    {{          # 转义
      "name": "步骤名称",
      ...
    }}          # 转义
  ]
}}              # 转义
..."""
```

### 步骤2: 修改 reasoning.py
同样转义JSON示例中的花括号：
- 保留 `{context}`, `{collected_evidence}` 不变
- 其他花括号转义

### 步骤3: 重启服务验证
重启服务后发送诊断请求验证修复效果。

## 修改示例

### planning.py 修改
```python
# 原代码（第30-43行）
请以JSON格式返回诊断步骤列表：
{
  "steps": [
    {
      "name": "步骤名称",
      ...
    }
  ]
}

# 修改后
请以JSON格式返回诊断步骤列表：
 {{
  "steps": [
    {{
      "name": "步骤名称",
      ...
    }}
  ]
}}
```

### reasoning.py 修改
```python
# 原代码（第17-37行）
以JSON格式返回：
{
  "hypotheses": [
    {
      ...
    }
  ],
  ...
}

# 修改后
以JSON格式返回：
 {{
  "hypotheses": [
    {{
      ...
    }}
  ],
  ...
}}
```