"""Reasoning engine module for analyzing diagnostic data."""

import json
import logging
import re
import time
import uuid

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

from dte_diagnostic_agent.agent.models.context import DiagnosticContext
from dte_diagnostic_agent.agent.models.hypothesis import Hypothesis, ValidatedHypothesis
from dte_diagnostic_agent.agent.models.report import Solution
from dte_diagnostic_agent.prompts.reasoning import REASONING_PROMPT


class DiagnosticRule:
    """Diagnostic rule for pattern-based reasoning."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        conditions: dict,
        hypothesis: Hypothesis
    ):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.hypothesis = hypothesis
    
    def match(self, context: DiagnosticContext) -> bool:
        if "symptoms" in self.conditions:
            for symptom in self.conditions["symptoms"]:
                if symptom.lower() not in [s.lower() for s in context.symptoms]:
                    return False
        
        if "category" in self.conditions:
            if context.category and context.category.value != self.conditions["category"]:
                return False
        
        return True


class ReasoningEngine:
    """Analyze diagnostic data and generate hypotheses."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.rules: list[DiagnosticRule] = self._load_rules()
    
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
    
    def _load_rules(self) -> list[DiagnosticRule]:
        return [
            DiagnosticRule(
                rule_id="RULE_001",
                name="数据库连接超时",
                conditions={"symptoms": ["超时", "连接失败", "timeout"]},
                hypothesis=Hypothesis(
                    id="H_RULE_001",
                    problem="数据库连接池配置不足或连接泄漏",
                    confidence=0.75,
                    evidence=["症状包含超时和连接失败"],
                    actions=["检查连接池配置", "分析连接持有时间"],
                    source="rule"
                )
            ),
            DiagnosticRule(
                rule_id="RULE_002",
                name="性能下降",
                conditions={"symptoms": ["慢", "性能", "响应缓慢"]},
                hypothesis=Hypothesis(
                    id="H_RULE_002",
                    problem="系统资源不足或存在性能瓶颈",
                    confidence=0.70,
                    evidence=["症状包含性能下降"],
                    actions=["检查CPU/内存使用率", "分析慢查询"],
                    source="rule"
                )
            ),
            DiagnosticRule(
                rule_id="RULE_003",
                name="服务不可用",
                conditions={"symptoms": ["不可用", "宕机", "crash"]},
                hypothesis=Hypothesis(
                    id="H_RULE_003",
                    problem="服务进程异常退出或配置错误",
                    confidence=0.80,
                    evidence=["症状包含服务不可用"],
                    actions=["检查进程状态", "查看错误日志"],
                    source="rule"
                )
            ),
        ]
    
    async def analyze(self, context: DiagnosticContext) -> list[Hypothesis]:
        """Analyze context and generate hypotheses."""
        session_id = context.session_id
        logger.info(f"[{session_id}] [Reasoning] 开始分析, 症状: {context.symptoms}")
        
        hypotheses = []
        
        for rule in self.rules:
            if rule.match(context):
                hypotheses.append(rule.hypothesis)
        
        matched_rules = [rule.name for rule in self.rules if rule.match(context)]
        logger.info(f"[{session_id}] [Reasoning] 规则匹配完成, 匹配规则数: {len(matched_rules)}, 规则: {matched_rules}")
        
        llm_hypotheses = await self._llm_reasoning(context)
        hypotheses.extend(llm_hypotheses)
        
        ranked = self._rank_hypotheses(hypotheses)
        logger.info(f"[{session_id}] [Reasoning] 分析完成, 总假设数: {len(ranked)}, 排序后置信度: {[h.confidence for h in ranked[:3]]}")
        
        return ranked
    
    async def _llm_reasoning(self, context: DiagnosticContext) -> list[Hypothesis]:
        session_id = context.session_id
        evidence_text = self._format_evidence(context.collected_data)
        
        prompt = REASONING_PROMPT.format(
            context=self._format_context(context),
            collected_evidence=evidence_text
        )
        
        prompt_preview = prompt[:5000] + "..." if len(prompt) > 500 else prompt
        logger.info(f"[{session_id}] [Reasoning] LLM调用开始, prompt长度: {len(prompt)}")
        logger.info(f"[{session_id}] [Reasoning] LLM调用输入(prompt前500字符): {prompt_preview}")
        
        start_time = time.perf_counter()
        response = await self.llm.ainvoke(prompt)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        token_info = self._extract_token_info(response)
        response_preview = response.content[:5000] + "..." if len(response.content) > 500 else response.content
        logger.info(f"[{session_id}] [Reasoning] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
        logger.info(f"[{session_id}] [Reasoning] LLM响应: {response_preview}")
        
        parsed_data = self._parse_response(response.content)
        
        hypotheses = []
        for i, h_data in enumerate(parsed_data.get("hypotheses", [])):
            hypotheses.append(Hypothesis(
                id=h_data.get("id", f"H_LLM_{i}"),
                problem=h_data.get("problem", ""),
                confidence=h_data.get("confidence", 0.5),
                evidence=h_data.get("evidence", []),
                actions=h_data.get("actions", []),
                source=h_data.get("source", "llm")
            ))
        
        logger.info(f"[{session_id}] [Reasoning] LLM推理生成假设数: {len(hypotheses)}")
        
        return hypotheses
    
    def _format_context(self, context: DiagnosticContext) -> str:
        lines = [
            f"问题描述: {context.problem_description}",
            f"问题类别: {context.category.value if context.category else 'unknown'}",
            f"症状: {', '.join(context.symptoms)}",
            f"时间范围: {context.time_range.start} ~ {context.time_range.end}",
            f"集群: {context.environment.cluster_name if context.environment else 'unknown'}",
        ]
        return "\n".join(lines)
    
    def _format_evidence(self, collected_data: dict) -> str:
        if not collected_data:
            return "暂无收集的证据数据"
        
        lines = []
        for key, value in collected_data.items():
            if isinstance(value, dict):
                lines.append(f"【{key}】")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"【{key}】")
                for item in value[:10]:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"【{key}】: {value}")
        
        return "\n".join(lines)
    
    def _parse_response(self, content: str) -> dict:
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _rank_hypotheses(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        return sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
    
    async def validate_hypotheses(
        self,
        context: DiagnosticContext,
        hypotheses: list[Hypothesis]
    ) -> list[ValidatedHypothesis]:
        validated = []
        for hypothesis in hypotheses[:5]:
            validated.append(ValidatedHypothesis(
                hypothesis=hypothesis,
                validation={"method": "llm_analysis"},
                confirmed=False,
                additional_evidence=[]
            ))
        return validated
    
    def generate_solutions(
        self,
        hypothesis: Hypothesis,
        similar_cases: list
    ) -> list[Solution]:
        solutions = []
        
        solutions.append(Solution(
            description=f"解决 {hypothesis.problem}",
            steps=hypothesis.actions,
            confidence=hypothesis.confidence,
        ))
        
        for result in similar_cases[:3]:
            case = result.case
            if case.solution:
                solutions.append(Solution(
                    description=f"基于案例 {case.case_id}: {case.title}",
                    steps=case.solution,
                    based_on_case=case.case_id,
                    confidence=result.similarity,
                ))
        
        return solutions