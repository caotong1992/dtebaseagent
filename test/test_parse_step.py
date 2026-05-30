import pytest
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dte_diagnostic_agent.agent.case_step_parser import CaseStepParser
from dte_diagnostic_agent.agent.models.plan import DiagnosticPlan
from dte_diagnostic_agent.kb.models import Case
from dte_diagnostic_agent.agent.models.context import DiagnosticContext

handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=handlers,
)

MODEL_RESPONSE_EXAMPLE = '''
{
  "steps": [
    {
      "step_number": 1,
      "action_type": "tool_execute",
      "tool_name": "database_query",
      "parameters": {
        "om_ip": "{om_ip}",
        "db_name": "rmtaskmgmtdb",
        "sql": "select last_result,last_error_code,last_fail_reason from tbl_task_info where task_id={task_id}"
      },
      "description": "查询数据库获取任务错误码",
      "next_step": 2,
      "template_vars": ["task_id", "om_ip"],
      "output_vars": ["last_result", "last_error_code", "last_fail_reason"],
      "extract_rules": {
        "last_result": {
          "source": "rows",
          "type": "field",
          "value": "last_result"
        },
        "last_error_code": {
          "source": "rows",
          "type": "field",
          "value": "last_error_code"
        },
        "last_fail_reason": {
          "source": "rows",
          "type": "field",
          "value": "last_fail_reason"
        }
      }
    },
    {
      "step_number": 2,
      "action_type": "keyword_extract",
      "description": "解析last_fail_reason，提取jobId和errorMsg",
      "next_step": 3,
      "template_vars": ["last_fail_reason"],
      "output_vars": ["errorMsg"],
      "extract_rules": {
        "errorMsg": {
          "source": "last_fail_reason",
          "type": "json_path",
          "value": "$[*].errorMsg[*]"
        }
      }
    },
    {
      "step_number": 3,
      "action_type": "decision",
      "description": "判断errorMsg是否不为空",
      "condition": "len(errorMsg) > 0",
      "next_step_if_true": 4,
      "next_step_if_false": 7
    },
    {
      "step_number": 4,
      "action_type": "tool_execute",
      "tool_name": "case_search",
      "parameters": {
        "query": "{errorMsg}"
      },
      "description": "在知识库检索errorMsg相关案例",
      "next_step": 5,
      "template_vars": ["errorMsg"],
      "output_vars": ["cases"],
      "extract_rules": {
        "cases": {
          "source": "result",
          "type": "field",
          "value": "cases"
        }
      }
    },
    {
      "step_number": 5,
      "action_type": "decision",
      "description": "判断是否检索到相关案例",
      "condition": "len(cases) > 0",
      "next_step_if_true": 6,
      "next_step_if_false": 7
    },
    {
      "step_number": 6,
      "action_type": "case_analysis",
      "description": "根据检索到的案例进行分析",
      "next_step": null
    },
    {
      "step_number": 7,
      "action_type": "tool_execute",
      "tool_name": "case_search",
      "parameters": {
        "query": "{last_error_code}"
      },
      "description": "在知识库检索last_error_code相关错误处理流程",
      "next_step": 8,
      "template_vars": ["last_error_code"],
      "output_vars": ["last_error_cases"],
      "extract_rules": {
        "last_error_cases": {
          "source": "result",
          "type": "field",
          "value": "cases"
        }
      }
    },
    {
      "step_number": 8,
      "action_type": "case_analysis",
      "description": "按照处理流程处理",
      "next_step": null
    }
  ]
}
'''
import asyncio

async def test_list_all_category_filter():
    """T506: List by category."""
    parser = CaseStepParser(llm=None)
    case = Case(case_id="123", title="测试案例")
    parsed = parser.parse_json_to_parsed_analysis("testsession", case, MODEL_RESPONSE_EXAMPLE)
    steps = parser.to_diagnostic_steps(parsed, {})
    plan = DiagnosticPlan(session_id="testsession", steps=steps)
    # plan.print_overview()
    excutor = plan.get_executor()
    context = DiagnosticContext(session_id="testsession", problem_description="测试问题")
    await excutor.execute(context)



print("Hello, World!")
os.environ['mock_mode']='1'
asyncio.run(test_list_all_category_filter())
print("Done!")