"""Case step parser for converting case analysis to diagnostic steps."""

import json
import logging
import re
import time

from langchain_openai import ChatOpenAI

from dte_diagnostic_agent.agent.models.parsed_step import ParsedAnalysis, ParsedStep, StepActionType
from dte_diagnostic_agent.agent.models.plan import DiagnosticStep
from dte_diagnostic_agent.kb.models import Case
from dte_diagnostic_agent.prompts.case_step import CASE_STEP_PARSE_PROMPT

logger = logging.getLogger(__name__)


class CaseStepParser:
    """Parser for converting case analysis process to structured diagnostic steps."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._cache: dict[str, ParsedAnalysis] = {}

    def _extract_token_info(self, response) -> str:
        """从LLM响应中提取token使用信息"""
        try:
            metadata = getattr(response, 'response_metadata', {}) or {}
            token_usage = metadata.get('token_usage', {})
            
            if token_usage:
                prompt_tokens = token_usage.get('prompt_tokens', 0)
                completion_tokens = token_usage.get('completion_tokens', 0)
                total_tokens = token_usage.get('total_tokens', 0)
                return f"prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
            
            usage = metadata.get('usage', {})
            if usage:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                return f"prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
            
            return "N/A"
        except Exception:
            return "N/A"

    async def parse_case_analysis(self, case: Case, session_id: str = "") -> ParsedAnalysis:
        if case.case_id in self._cache:
            logger.info(f"[{session_id}] [CaseStepParser] 案例 {case.case_id} 缓存命中")
            return self._cache[case.case_id]

        if not case.analysis:
            logger.info(f"[{session_id}] [CaseStepParser] 案例 {case.case_id} 无分析过程")
            parsed = ParsedAnalysis(case_id=case.case_id, steps=[], has_iterative_search=False)
            self._cache[case.case_id] = parsed
            return parsed

        prompt = CASE_STEP_PARSE_PROMPT.format(
            case_id=case.case_id,
            title=case.title,
            analysis_text=case.analysis
        )

        logger.info(f"[{session_id}] [CaseStepParser] LLM调用开始, 案例ID: {case.case_id}, prompt长度: {len(prompt)}")
        prompt_preview = prompt[:5000] + "..." if len(prompt) > 300 else prompt
        logger.info(f"[{session_id}] [CaseStepParser] LLM调用输入: {prompt_preview}")

        try:
            start_time = time.time()
            response = await self.llm.ainvoke(prompt)
            elapsed_ms = (time.time() - start_time) * 1000
            
            result_text = response.content.strip()
            token_info = self._extract_token_info(response)
            
            logger.info(f"[{session_id}] [CaseStepParser] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
            result_preview = result_text[:5000] + "..." if len(result_text) > 500 else result_text
            logger.info(f"[{session_id}] [CaseStepParser] LLM响应: {result_preview}")

            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                data = json.loads(json_match.group())
                steps = [ParsedStep(**s) for s in data.get("steps", [])]
                parsed = ParsedAnalysis(
                    case_id=case.case_id,
                    steps=steps,
                    has_iterative_search=data.get("has_iterative_search", False)
                )
                logger.info(f"[{session_id}] [CaseStepParser] 解析成功, 步骤数: {len(parsed.steps)}, 迭代检索: {parsed.has_iterative_search}")
            else:
                logger.warning(f"[{session_id}] [CaseStepParser] No JSON found in response for case {case.case_id}")
                parsed = ParsedAnalysis(case_id=case.case_id, steps=[], has_iterative_search=False)
        except json.JSONDecodeError as e:
            logger.warning(f"[{session_id}] [CaseStepParser] JSON decode error for case {case.case_id}: {e}")
            parsed = ParsedAnalysis(case_id=case.case_id, steps=[], has_iterative_search=False)
        except Exception as e:
            logger.error(f"[{session_id}] [CaseStepParser] Error parsing case {case.case_id}: {e}")
            parsed = ParsedAnalysis(case_id=case.case_id, steps=[], has_iterative_search=False)

        self._cache[case.case_id] = parsed
        return parsed

    def to_diagnostic_steps(
        self,
        parsed: ParsedAnalysis,
        collected_data: dict[str, object] = None
    ) -> list[DiagnosticStep]:
        if collected_data is None:
            collected_data = {}
        steps = []
        for ps in parsed.steps:
            step = DiagnosticStep(
                name=f"step_{ps.step_number}_{ps.tool_name or 'action'}",
                description=ps.description,
                tool_name=ps.tool_name or "unknown",
                parameters=ps.parameters,
                priority=ps.step_number,
                dependencies=[],
                template_vars=ps.template_vars,
                output_vars=ps.output_vars,
                extract_rules=ps.extract_rules
            )
            steps.append(step)

        return steps

    def _replace_template_vars(
        self,
        params: dict[str, object],
        collected_data: dict[str, object]
    ) -> dict[str, object]:
        result = {}
        for key, value in params.items():
            if isinstance(value, str):
                replaced_value = value
                for var_name, var_value in collected_data.items():
                    if var_value is not None:
                        replaced_value = replaced_value.replace(f"{{{var_name}}}", str(var_value))
                result[key] = replaced_value
            else:
                result[key] = value
        return result

    def detect_iterative_search(self, parsed: ParsedAnalysis) -> bool:
        if parsed.has_iterative_search:
            return True

        for step in parsed.steps:
            if step.action_type == StepActionType.CASE_SEARCH:
                params_str = str(step.parameters)
                for var in step.template_vars:
                    if f"{{{var}}}" in params_str:
                        return True

        return False