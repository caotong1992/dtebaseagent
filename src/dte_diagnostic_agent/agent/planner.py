"""Diagnostic planner module for generating diagnostic plans."""

import json
import logging
import re
import time

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

from dte_diagnostic_agent.agent.models.context import DiagnosticContext
from dte_diagnostic_agent.agent.models.plan import DiagnosticPlan, DiagnosticStep
from dte_diagnostic_agent.kb.models import Case
from dte_diagnostic_agent.prompts.planning import PLANNING_PROMPT


class DiagnosticPlanner:
    """Generate diagnostic plans based on problem analysis."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def _extract_token_info(self, response) -> str:
        """Extract token usage information from LLM response."""
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
    
    async def generate_plan(
        self,
        context: DiagnosticContext,
        similar_cases: list[Case]
    ) -> DiagnosticPlan:
        """Generate diagnostic plan based on context and historical cases."""
        session_id = context.session_id
        category = context.category.value if context.category else "unknown"
        logger.info(f"[{session_id}] [Planner] 生成诊断计划, 问题类别: {category}")
        
        similar_cases_text = self._format_similar_cases(similar_cases)
        
        prompt = PLANNING_PROMPT.format(
            problem_description=context.problem_description,
            category=category,
            symptoms=", ".join(context.symptoms),
            time_range=f"{context.time_range.start} ~ {context.time_range.end}",
            cluster_name=context.environment.cluster_name if context.environment else "unknown",
            similar_cases=similar_cases_text
        )
        
        prompt_preview = prompt[:5000] + "..." if len(prompt) > 5000 else prompt
        logger.info(f"[{session_id}] [Planner] LLM调用开始, prompt长度: {len(prompt)}")
        logger.info(f"[{session_id}] [Planner] LLM调用输入(prompt前500字符): {prompt_preview}")
        
        start_time = time.perf_counter()
        response = await self.llm.ainvoke(prompt)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        token_info = self._extract_token_info(response)
        response_preview = response.content[:5000] + "..." if len(response.content) > 5000 else response.content
        logger.info(f"[{session_id}] [Planner] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
        logger.info(f"[{session_id}] [Planner] LLM响应: {response_preview}")
        
        parsed_data = self._parse_response(response.content)
        
        steps = self._build_steps(parsed_data.get("steps", []))
        
        if not steps:
            steps = self._get_default_steps(context)
            logger.info(f"[{session_id}] [Planner] 使用默认步骤, 步骤数: {len(steps)}")
        
        logger.info(f"[{session_id}] [Planner] 生成步骤数: {len(steps)}, 步骤: {[s.name for s in steps]}")
        
        return DiagnosticPlan(
            steps=steps,
            estimated_duration=len(steps) * 30
        )
    
    def _format_similar_cases(self, cases: list[Case]) -> str:
        if not cases:
            return "无相似历史案例"
        
        lines = []
        for i, case in enumerate(cases[:5], 1):
            lines.append(f"{i}. [{case.case_id}] {case.title}")
            lines.append(f"   类别: {case.category}")
            lines.append(f"   症状: {', '.join(case.symptoms[:3])}")
            lines.append(f"   分析过程: {case.analysis}")
        
        return "\n".join(lines)
    
    def _parse_response(self, content: str) -> dict:
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _build_steps(self, steps_data: list) -> list[DiagnosticStep]:
        steps = []
        for i, step_data in enumerate(steps_data):
            steps.append(DiagnosticStep(
                name=step_data.get("name", f"step_{i}"),
                description=step_data.get("description", ""),
                tool_name=step_data.get("tool_name", ""),
                parameters=step_data.get("parameters", {}),
                priority=step_data.get("priority", i),
            ))
        return sorted(steps, key=lambda s: s.priority)
    
    def _get_default_steps(self, context: DiagnosticContext) -> list[DiagnosticStep]:
        steps = []
        
        node_host = ""
        if context.environment and context.environment.node_info:
            node_host = context.environment.node_info.host
        
        if node_host:
            steps.append(DiagnosticStep(
                name="connect_server",
                description="连接目标服务器",
                tool_name="ssh_connect",
                parameters={
                    "host": node_host,
                    "port": 22,
                    "username": context.environment.node_info.username or "admin",
                },
                priority=0,
            ))
        
        steps.append(DiagnosticStep(
            name="check_logs",
            description="检查服务日志",
            tool_name="log_analysis",
            parameters={
                "session_id": context.session_id,
                "log_path": "/var/log/dtebaseservice",
                "start_time": context.time_range.start.isoformat(),
                "end_time": context.time_range.end.isoformat(),
                "patterns": ["error", "exception", "timeout", "fail"],
            },
            priority=1,
        ))
        
        steps.append(DiagnosticStep(
            name="check_resources",
            description="检查系统资源",
            tool_name="resource_monitor",
            parameters={
                "session_id": context.session_id,
                "metrics": ["cpu", "memory", "disk"],
            },
            priority=2,
        ))
        
        steps.append(DiagnosticStep(
            name="search_cases",
            description="搜索相似案例",
            tool_name="case_search",
            parameters={
                "query": context.problem_description,
                "symptoms": context.symptoms,
            },
            priority=3,
        ))
        
        return steps