"""DTEBaseDiagnosticAgent core implementation."""

from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI

from dte_diagnostic_agent.agent.intent_parser import IntentParser
from dte_diagnostic_agent.agent.planner import DiagnosticPlanner
from dte_diagnostic_agent.agent.reasoning import ReasoningEngine
from dte_diagnostic_agent.agent.models.input import UserInput
from dte_diagnostic_agent.agent.models.context import DiagnosticContext
from dte_diagnostic_agent.agent.models.plan import DiagnosticPlan
from dte_diagnostic_agent.agent.models.hypothesis import ValidatedHypothesis
from dte_diagnostic_agent.agent.models.report import DiagnosticReport, Solution
from dte_diagnostic_agent.kb.models import Case
from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager
from dte_diagnostic_agent.kb.query_processor import QueryProcessor
from dte_diagnostic_agent.kb.translator import TranslatorService
from dte_diagnostic_agent.kb.config import QueryProcessorConfig
import logging


class DTEBaseDiagnosticAgent:
    """DTEBaseService problem diagnostic agent."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model_name: str = "gpt-4o",
        temperature: float = 0.1,
        kb_manager: KnowledgeBaseManager | None = None,
        query_processor_config: QueryProcessorConfig | None = None
    ):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing DTEBaseDiagnosticAgent with model: {model_name}, temperature: {temperature}")
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url
        )
        
        self.intent_parser = IntentParser(llm=self.llm)
        self.planner = DiagnosticPlanner(llm=self.llm)
        self.reasoning_engine = ReasoningEngine(llm=self.llm)
        self.kb_manager = kb_manager
        
        if query_processor_config and query_processor_config.enabled:
            translator = TranslatorService(
                llm=self.llm,
                cache_size=query_processor_config.cache_size
            )
            self.query_processor = QueryProcessor(
                translator=translator,
                config=query_processor_config
            )
            self.logger.info(f"QueryProcessor initialized, enabled={query_processor_config.enabled}, use_llm_translation={query_processor_config.use_llm_translation}")
        else:
            self.query_processor = None
            self.logger.info("QueryProcessor disabled or not configured")
    
    async def diagnose(self, user_input: UserInput) -> DiagnosticReport:
        session_id = str(uuid.uuid4())
        description = user_input.description or ""
        self.logger.info(f"[{session_id}] [Agent] 诊断开始, 问题描述: {description[:100]}")
        
        context = await self.intent_parser.parse(user_input)
        context.session_id = session_id
        category = context.category.value if context.category else "未知"
        self.logger.info(f"[{session_id}] [Agent] 意图解析完成, 类别: {category}")
        
        similar_cases = await self._search_similar_cases(context, session_id)
        
        plan = await self.planner.generate_plan(context, similar_cases)
        self.logger.info(f"[{session_id}] [Agent] 计划生成完成, 步骤数: {len(plan.steps)}")
        
        for step in plan.get_ordered_steps():
            result = await self._execute_step(context, step, session_id)
            context.collected_data[step.name] = result
        
        hypotheses = await self.reasoning_engine.analyze(context)
        self.logger.info(f"[{session_id}] [Agent] 推理完成, 假设数: {len(hypotheses)}")
        
        validated = await self.reasoning_engine.validate_hypotheses(context, hypotheses)
        
        report = self._generate_report(context, validated, similar_cases)
        
        top_confidence = 0.0
        if validated:
            top_confidence = max(h.hypothesis.confidence for h in validated)
        self.logger.info(f"[{session_id}] [Agent] 诊断完成, 最高置信度: {top_confidence:.2f}")
        
        return report
    
    async def _search_similar_cases(self, context: DiagnosticContext, session_id: str) -> list[Case]:
        if not self.kb_manager:
            self.logger.info(f"[{session_id}] [Agent] 知识库查询跳过, 未配置知识库管理器")
            return []
        
        query = context.problem_description
        keywords = None
        
        if self.query_processor and query:
            self.logger.info(f"[{session_id}] [QueryProcessor] 开始查询预处理, 原始查询: {query[:100] if query else ''}")
            preprocessed = await self.query_processor.process(query)
            keywords = preprocessed.all_keywords
            self.logger.info(f"[{session_id}] [QueryProcessor] 预处理完成, 中文关键词: {preprocessed.chinese_keywords}")
            self.logger.info(f"[{session_id}] [QueryProcessor] 预处理完成, 英文关键词: {preprocessed.english_keywords}")
            self.logger.info(f"[{session_id}] [QueryProcessor] 预处理完成, 合并关键词: {keywords}")
        
        self.logger.info(f"[{session_id}] [Agent] 知识库查询开始, 关键词: {keywords[:5] if keywords else query[:50] if query else ''}")
        
        results = await self.kb_manager.search(
            query=query,
            keywords=keywords,
            symptoms=context.symptoms,
            top_k=5
        )
        cases = [r.case for r in results]
        self.logger.info(f"[{session_id}] [Agent] 知识库查询完成, 返回案例数: {len(cases)}")
        
        return cases
    
    async def _execute_step(self, context: DiagnosticContext, step, session_id: str) -> dict:
        self.logger.info(f"[{session_id}] [Agent] 执行步骤: {step.name}, 工具: {step.tool_name}")
        
        tool_result = {"executed": True, "tool": step.tool_name}
        
        match step.tool_name:
            case "ssh_connect":
                tool_result["status"] = "simulated_connection"
            case "log_analysis":
                tool_result["logs"] = []
                tool_result["anomalies"] = []
            case "resource_monitor":
                tool_result["cpu"] = 50.0
                tool_result["memory"] = 60.0
                tool_result["disk"] = 70.0
            case "database_query":
                tool_result["connections"] = 50
                tool_result["slow_queries"] = []
            case "case_search":
                tool_result["cases_found"] = len(context.symptoms)
            case _:
                tool_result["result"] = "executed"
        
        result_summary = self._get_result_summary(tool_result)
        self.logger.info(f"[{session_id}] [Agent] 执行步骤: {step.name}, 结果: {result_summary}")
        
        return tool_result
    
    def _get_result_summary(self, result: dict) -> str:
        if "status" in result:
            return f"status={result['status']}"
        if "anomalies" in result:
            return f"logs={len(result.get('logs', []))}, anomalies={len(result['anomalies'])}"
        if "cpu" in result:
            return f"cpu={result['cpu']}%, memory={result['memory']}%, disk={result['disk']}%"
        if "connections" in result:
            return f"connections={result['connections']}, slow_queries={len(result.get('slow_queries', []))}"
        if "cases_found" in result:
            return f"cases_found={result['cases_found']}"
        if "result" in result:
            return f"result={result['result']}"
        return "completed"
    
    def _generate_report(
        self,
        context: DiagnosticContext,
        hypotheses: list[ValidatedHypothesis],
        similar_cases: list[Case]
    ) -> DiagnosticReport:
        top_hypothesis = max(hypotheses, key=lambda h: h.hypothesis.confidence) if hypotheses else None
        
        solutions = []
        if top_hypothesis:
            solutions = self.reasoning_engine.generate_solutions(
                top_hypothesis.hypothesis,
                similar_cases
            )
        
        summary = self._generate_summary(context, top_hypothesis)
        
        next_steps = self._generate_next_steps(top_hypothesis)
        
        return DiagnosticReport(
            session_id=context.session_id,
            generated_at=datetime.now(),
            summary=summary,
            problem_category=context.category or None,
            severity=context.priority,
            hypotheses=hypotheses,
            top_hypothesis=top_hypothesis,
            similar_cases=similar_cases,
            recommended_solutions=solutions,
            collected_evidence=context.collected_data,
            diagnostic_steps=[{"step": s, "result": "executed"} for s in context.collected_data.keys()],
            next_steps=next_steps,
            escalation_needed=self._check_escalation(top_hypothesis)
        )
    
    def _generate_summary(
        self,
        context: DiagnosticContext,
        top_hypothesis: ValidatedHypothesis | None
    ) -> str:
        if top_hypothesis:
            return f"问题诊断完成，最可能原因是: {top_hypothesis.hypothesis.problem}"
        return f"问题诊断完成，已收集证据分析"
    
    def _generate_next_steps(self, top_hypothesis: ValidatedHypothesis | None) -> list[str]:
        if top_hypothesis:
            return top_hypothesis.hypothesis.actions[:5]
        return ["进一步收集证据", "人工介入分析"]
    
    def _check_escalation(self, top_hypothesis: ValidatedHypothesis | None) -> bool:
        if not top_hypothesis:
            return True
        return top_hypothesis.hypothesis.confidence < 0.5