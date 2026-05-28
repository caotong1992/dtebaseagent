"""Case step parsing prompt template."""

CASE_STEP_PARSE_PROMPT = """你是一个诊断步骤解析器。请分析以下案例的"分析过程"章节，提取结构化的执行步骤。

## 案例信息
- 案例ID: {case_id}
- 案例标题: {title}

## 分析过程原文
{analysis_text}

## 输出要求
请输出 JSON 格式的步骤列表，每个步骤包含：
1. step_number: 步骤序号
2. action_type: 动作类型，可选值：
   - tool_execute: 执行工具（如查询数据库、SSH执行命令）
   - case_search: 知识库检索（用新信息检索其他案例）
   - manual_check: 手动检查（需要人工介入）
   - decision: 条件判断（根据结果决定下一步）
3. tool_name: 工具名称（action_type 为 tool_execute 时必填）
   - 可选值: database_query, ssh_connect, log_analysis, case_search, network_diag, k8s_operation, config_check, resource_monitor
4. parameters: 参数字典，支持模板变量如 {{task_id}}, {{last_error_code}}
5. description: 步骤描述原文
6. next_action: 下一步指引（如果有）
7. template_vars: 模板变量列表
8. output_vars: 该步骤产出的变量名列表（如 ["last_error_code", "task_id"]）
9. extract_rules: 变量提取规则字典，key为output_vars中的变量名，每个规则包含：
   - source: 数据来源字段名，常用值：
     - "rows": 从结果数组中提取（database_query工具返回格式）
     - "result": 从顶层结果直接提取
   - type: 提取类型，可选值：field（字段提取）、regex（正则匹配）、json_path（JSON路径）
   - value: 提取值（字段名、正则表达式或JSON路径）

## 输出示例
```json
{{
  "steps": [
    {{
      "step_number": 1,
      "action_type": "tool_execute",
      "tool_name": "database_query",
      "parameters": {{
        "db_name": "rmtaskmgmtdb",
        "sql": "select last_result,last_error_code,last_fail_reason from tbl_task_info where task_id={{task_id}}"
      }},
      "description": "查询数据库获取任务错误码",
      "next_action": "用 last_error_code 检索案例",
      "template_vars": ["task_id"],
      "output_vars": ["last_error_code"],
      "extract_rules": {{
        "last_error_code": {{
          "source": "rows",
          "type": "field",
          "value": "last_error_code"
        }}
      }}
    }},
    {{
      "step_number": 2,
      "action_type": "case_search",
      "tool_name": "case_search",
      "parameters": {{
        "query": "{{last_error_code}}",
        "category": "collector_task"
      }},
      "description": "在知识库检索last_error_code相关错误处理流程",
      "next_action": null,
      "template_vars": ["last_error_code"]
    }}
  ]
}}
```

请仅输出 JSON，不要包含其他内容。
"""