"""Intent parser module for understanding user input."""

import json
import re
import time
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI

from dte_diagnostic_agent.agent.models.context import (
    DiagnosticContext,
    TimeRange,
    ClusterInfo,
    NodeInfo,
    Severity,
    ProblemCategory,
)
from dte_diagnostic_agent.agent.models.input import UserInput
from dte_diagnostic_agent.prompts.intent import INTENT_PROMPT

import logging
logger = logging.getLogger(__name__)


class IntentParser:
    """Parse user input to extract diagnostic context."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def parse(self, user_input: UserInput) -> DiagnosticContext:
        """Parse user input and return DiagnosticContext."""
        session_id = f"diag-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        input_text = self._format_input(user_input)
        
        prompt = INTENT_PROMPT.format(user_input=input_text)
        logger.info(f"[{session_id}] [IntentParser] LLM调用开始, prompt长度: {len(prompt)}")
        
        start_time = time.time()
        response = await self.llm.ainvoke(prompt)
        elapsed_ms = (time.time() - start_time) * 1000
        
        token_info = self._extract_token_info(response)
        logger.info(f"[{session_id}] [IntentParser] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
        logger.debug(f"[{session_id}] [IntentParser] LLM响应: {response.content[:500]}...")
        
        parsed_data = self._parse_response(response.content)
        
        time_range = self._build_time_range(
            user_input.time_range_start,
            user_input.time_range_end,
            parsed_data
        )
        
        environment = self._build_environment(user_input.environment, parsed_data)
        
        return DiagnosticContext(
            session_id=session_id,
            problem_description=parsed_data.get("problem_description", user_input.description),
            time_range=time_range,
            environment=environment,
            symptoms=parsed_data.get("symptoms", user_input.symptoms),
            priority=Severity(parsed_data.get("priority", "medium")),
            category=self._parse_category(parsed_data.get("category")),
            collected_data={},
            metadata={"raw_input": user_input.model_dump()},
        )
    
    def _format_input(self, user_input: UserInput) -> str:
        lines = [f"问题描述: {user_input.description}"]
        
        if user_input.time_range_start:
            lines.append(f"开始时间: {user_input.time_range_start.isoformat()}")
        if user_input.time_range_end:
            lines.append(f"结束时间: {user_input.time_range_end.isoformat()}")
        
        if user_input.environment:
            lines.append(f"集群名称: {user_input.environment.cluster_name}")
            if user_input.environment.node_info:
                lines.append(f"节点: {user_input.environment.node_info.host}")
            lines.append(f"服务: {user_input.environment.service_name}")
        
        if user_input.symptoms:
            lines.append(f"症状: {', '.join(user_input.symptoms)}")
        
        lines.append(f"优先级: {user_input.priority}")
        
        return "\n".join(lines)
    
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
    
    def _parse_response(self, content: str) -> dict:
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _build_time_range(
        self,
        start: datetime | None,
        end: datetime | None,
        parsed_data: dict
    ) -> TimeRange:
        now = datetime.now()
        
        if start and end:
            return TimeRange(start=start, end=end)
        
        parsed_range = parsed_data.get("time_range", {})
        
        try:
            parsed_start = datetime.fromisoformat(parsed_range.get("start", ""))
        except (ValueError, TypeError):
            parsed_start = now - timedelta(hours=1)
        
        try:
            parsed_end = datetime.fromisoformat(parsed_range.get("end", ""))
        except (ValueError, TypeError):
            parsed_end = now
        
        return TimeRange(start=parsed_start, end=parsed_end)
    
    def _build_environment(
        self,
        env: ClusterInfo | None,
        parsed_data: dict
    ) -> ClusterInfo:
        if env:
            return env
        
        parsed_env = parsed_data.get("environment", {})
        parsed_node = parsed_env.get("node_info", {})
        
        return ClusterInfo(
            cluster_name=parsed_env.get("cluster_name", "unknown"),
            cluster_type=parsed_env.get("cluster_type", "standalone"),
            node_info=NodeInfo(
                host=parsed_node.get("host", ""),
                port=parsed_node.get("port", 22),
                username=parsed_node.get("username", ""),
                auth_type=parsed_node.get("auth_type", "password"),
            ) if parsed_node.get("host") else None,
            service_name=parsed_env.get("service_name", "DTEBaseService"),
            namespace=parsed_env.get("namespace"),
        )
    
    def _parse_category(self, category: str | None) -> ProblemCategory | None:
        if not category:
            return None
        try:
            return ProblemCategory(category)
        except ValueError:
            return ProblemCategory.UNKNOWN


from datetime import timedelta