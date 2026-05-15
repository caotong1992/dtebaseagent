"""DTEBaseDiagnosticAgent core implementation."""

from datetime import datetime
import json
import uuid

from langchain_openai import ChatOpenAI

from dte_diagnostic_agent.agent.intent_parser import IntentParser
from dte_diagnostic_agent.agent.planner import DiagnosticPlanner
from dte_diagnostic_agent.agent.reasoning import ReasoningEngine
from dte_diagnostic_agent.agent.case_step_parser import CaseStepParser
from dte_diagnostic_agent.agent.info_extractor import KeyInfoExtractor, ResultExtractor
from dte_diagnostic_agent.agent.models.input import UserInput
from dte_diagnostic_agent.agent.models.context import DiagnosticContext, ProblemCategory, Severity
from dte_diagnostic_agent.agent.models.plan import DiagnosticPlan, DiagnosticStep
from dte_diagnostic_agent.agent.models.hypothesis import ValidatedHypothesis
from dte_diagnostic_agent.agent.models.parsed_step import ParsedAnalysis, StepActionType
from dte_diagnostic_agent.agent.models.report import DiagnosticReport, Solution
from dte_diagnostic_agent.kb.models import Case, SearchResult
from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager
from dte_diagnostic_agent.kb.query_processor import QueryProcessor
from dte_diagnostic_agent.kb.translator import TranslatorService
from dte_diagnostic_agent.kb.config import QueryProcessorConfig
from dte_diagnostic_agent.tools.ssh import SSHConnectTool
from dte_diagnostic_agent.tools.log import LogAnalysisTool
from dte_diagnostic_agent.tools.resource import ResourceMonitorTool
from dte_diagnostic_agent.tools.database import DatabaseQueryTool
from dte_diagnostic_agent.tools.case import create_case_search_tool, MockCaseSearchTool
from dte_diagnostic_agent.tools.network import NetworkDiagTool
from dte_diagnostic_agent.tools.k8s import K8sOperationTool
from dte_diagnostic_agent.tools.config import ConfigCheckTool
import logging


class DTEBaseDiagnosticAgent:
    """DTEBaseService problem diagnostic agent."""
    
    STATIC_TOOLS = {
        "ssh_connect": SSHConnectTool,
        "log_analysis": LogAnalysisTool,
        "resource_monitor": ResourceMonitorTool,
        "database_query": DatabaseQueryTool,
        "network_diag": NetworkDiagTool,
        "k8s_operation": K8sOperationTool,
        "config_check": ConfigCheckTool,
    }
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model_name: str = "gpt-4o",
        temperature: float = 0.1,
        kb_manager: KnowledgeBaseManager | None = None,
        query_processor_config: QueryProcessorConfig | None = None,
        case_step_parser: CaseStepParser | None = None
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
        self.case_step_parser = case_step_parser or CaseStepParser(self.llm)
        self.info_extractor = KeyInfoExtractor()
        self.result_extractor = ResultExtractor()
        
        self._case_search_tool = None
        
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
    
    def _get_case_search_tool(self):
        if self._case_search_tool is None:
            if self.kb_manager:
                self._case_search_tool = create_case_search_tool(self.kb_manager)
                self.logger.info("[Agent] 创建 case_search 工具, 使用知识库管理器")
            else:
                self._case_search_tool = MockCaseSearchTool
                self.logger.info("[Agent] 创建 case_search 工具, 使用 Mock 实现")
        return self._case_search_tool
    
    def _get_tool(self, tool_name: str):
        if tool_name == "case_search":
            return self._get_case_search_tool()
        return self.STATIC_TOOLS.get(tool_name)
    
    async def diagnose(self, user_input: UserInput, session_id: str | None = None) -> DiagnosticReport:
        description = user_input.description or ""
        
        context = await self.intent_parser.parse(user_input, session_id=session_id)
        session_id = context.session_id
        
        self.logger.info(f"[{session_id}] [Agent] 诊断开始, 问题描述: {description[:100]}")
        category = context.category.value if context.category else "未知"
        self.logger.info(f"[{session_id}] [Agent] 意图解析完成, 类别: {category}")
        
        similar_cases = await self._search_similar_cases(context, session_id)
        
        parsed_analyses: list[ParsedAnalysis] = []
        for result in similar_cases:
            case = result.case
            if case.analysis:
                parsed = await self.case_step_parser.parse_case_analysis(case, session_id)
                parsed_analyses.append(parsed)
                self.logger.info(f"[{session_id}] [Agent] 解析案例 {case.case_id}, 步骤数: {len(parsed.steps)}, 迭代检索: {parsed.has_iterative_search}")
        
        iterative_parsed = [p for p in parsed_analyses if p.has_iterative_search]
        
        if iterative_parsed:
            self.logger.info(f"[{session_id}] [Agent] 检测到迭代检索需求，使用案例 {[p.case_id for p in iterative_parsed]}")
            
            selected_parsed = iterative_parsed[0]
            selected_result = next((r for r in similar_cases if r.case.case_id == selected_parsed.case_id), similar_cases[0])
            selected_case = selected_result.case
            
            self.logger.info(f"[{session_id}] [Agent] 选择案例 {selected_parsed.case_id} 作为引导案例")
            
            plan = await self._execute_iterative_flow(selected_case, selected_parsed, context, session_id)
        else:
            cases_for_plan = [r.case for r in similar_cases]
            plan = await self.planner.generate_plan(context, cases_for_plan)
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
    
    async def _execute_iterative_flow(
        self,
        initial_case: Case,
        parsed: ParsedAnalysis,
        context: DiagnosticContext,
        session_id: str
    ) -> DiagnosticPlan:
        self.logger.info(f"[{session_id}] [Agent] 开始迭代诊断流程, 引导案例: {initial_case.case_id}")
        
        self._extract_initial_vars(context, session_id)
        
        initial_steps = self.case_step_parser.to_diagnostic_steps(parsed, context.collected_data)
        self.logger.info(f"[{session_id}] [Agent] 引导案例步骤: {[s.name for s in initial_steps]}")
        
        plan = DiagnosticPlan(
            session_id=session_id,
            steps=initial_steps
        )
        
        processed_case_ids = {initial_case.case_id}
        
        for step in plan.get_ordered_steps():
            if step.template_vars:
                step.parameters = self._replace_template_vars(step.parameters, context.collected_data)
                self.logger.info(f"[{session_id}] [Agent] 步骤 {step.name} 模板变量替换后参数: {step.parameters}")
            
            self.logger.info(f"[{session_id}] [Agent] 执行引导步骤: {step.name}, 工具: {step.tool_name}")
            result = await self._execute_step(context, step, session_id)
            context.collected_data[step.name] = result
            
            output_vars = getattr(step, 'output_vars', [])
            extract_rules = getattr(step, 'extract_rules', {})
            
            if output_vars:
                extract_rules_dict = self._convert_extract_rules(extract_rules)
                extracted = self.result_extractor.extract(result, output_vars, extract_rules_dict, session_id)
                for var_name, var_value in extracted.items():
                    if var_value is not None:
                        self.logger.info(f"[{session_id}] [Agent] 提取变量: {var_name}={var_value}")
                        context.collected_data[var_name] = var_value
            
            if step.tool_name == "case_search":
                found_cases = self._extract_cases_from_search_result(result, session_id)
                if found_cases:
                    self.logger.info(f"[{session_id}] [Agent] case_search 找到案例: {[c['case_id'] for c in found_cases]}")
                    
                    new_case_ids = [c['case_id'] for c in found_cases if c['case_id'] not in processed_case_ids]
                    if new_case_ids:
                        self.logger.info(f"[{session_id}] [Agent] 发现新案例: {new_case_ids}")
                        
                        new_case = await self.kb_manager.get(new_case_ids[0])
                        if new_case and new_case.analysis:
                            processed_case_ids.add(new_case.case_id)
                            
                            new_parsed = await self.case_step_parser.parse_case_analysis(new_case, session_id)
                            new_steps = self.case_step_parser.to_diagnostic_steps(new_parsed, context.collected_data)
                            
                            base_priority = len(plan.steps)
                            for i, s in enumerate(new_steps):
                                s.priority = base_priority + i
                                s.name = f"{new_case.case_id}_step_{i+1}_{s.tool_name}"
                            
                            all_steps = list(plan.steps) + new_steps
                            plan = DiagnosticPlan(session_id=session_id, steps=all_steps)
                            self.logger.info(f"[{session_id}] [Agent] 更新计划, 新增步骤: {[s.name for s in new_steps]}")
                            
                            for s in new_steps:
                                self.logger.info(f"[{session_id}] [Agent] 执行新案例步骤: {s.name}")
                                r = await self._execute_step(context, s, session_id)
                                context.collected_data[s.name] = r
        
        return plan
    
    def _convert_extract_rules(self, extract_rules: dict) -> dict:
        from dte_diagnostic_agent.agent.models.parsed_step import ExtractRule as ExtractRuleModel
        
        result = {}
        for var_name, rule in extract_rules.items():
            if isinstance(rule, ExtractRuleModel):
                rule_dict = {
                    "method": rule.type.value,
                    "source": rule.source,
                    "params": {}
                }
                if rule.type.value == "field":
                    rule_dict["params"]["field_name"] = rule.value
                elif rule.type.value == "regex":
                    rule_dict["params"]["pattern"] = rule.value
                elif rule.type.value == "json_path":
                    rule_dict["params"]["path"] = rule.value
                result[var_name] = rule_dict
            elif isinstance(rule, dict):
                converted = {
                    "method": rule.get("type", rule.get("method", "")),
                    "source": rule.get("source", ""),
                    "params": {}
                }
                rule_type = rule.get("type", rule.get("method", ""))
                rule_value = rule.get("value", "")
                if rule_type == "field":
                    converted["params"]["field_name"] = rule_value
                elif rule_type == "regex":
                    converted["params"]["pattern"] = rule_value
                elif rule_type == "json_path":
                    converted["params"]["path"] = rule_value
                result[var_name] = converted
        return result
    
    def _replace_template_vars(self, params: dict, collected_data: dict) -> dict:
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
    
    def _extract_initial_vars(self, context: DiagnosticContext, session_id: str):
        """从用户输入提取初始模板变量"""
        extractor = KeyInfoExtractor()
        
        task_id = extractor.extract_task_id(context, session_id)
        if task_id:
            context.collected_data["task_id"] = task_id
            self.logger.info(f"[{session_id}] [Agent] 提取初始变量: task_id={task_id}")
    
    def _extract_cases_from_search_result(self, result: dict, session_id: str) -> list[dict]:
        cases = result.get("cases", [])
        if cases:
            self.logger.info(f"[{session_id}] [Agent] 从搜索结果提取 {len(cases)} 个案例")
        return cases
    
    async def _search_similar_cases(self, context: DiagnosticContext, session_id: str) -> list[SearchResult]:
        if not self.kb_manager:
            self.logger.info(f"[{session_id}] [Agent] 知识库查询跳过, 未配置知识库管理器")
            return []
        
        query = context.problem_description
        keywords = None
        
        if self.query_processor and query:
            self.logger.info(f"[{session_id}] [QueryProcessor] 开始查询预处理, 原始查询: {query[:100] if query else ''}")
            preprocessed = await self.query_processor.process(query, session_id)
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
        self.logger.info(f"[{session_id}] [Agent] 知识库查询完成, 返回案例数: {len(results)}, 案例ID: {[r.case.case_id for r in results]}")
        
        return results
    
    async def _execute_step(self, context: DiagnosticContext, step, session_id: str) -> dict:
        self.logger.info(f"[{session_id}] [Agent] 执行步骤: {step.name}, 工具: {step.tool_name}")
        
        tool = self._get_tool(step.tool_name)
        if not tool:
            self.logger.warning(f"[{session_id}] [Agent] 未知工具: {step.tool_name}")
            return {"error": f"Unknown tool: {step.tool_name}", "executed": False}
        
        args = self._build_tool_args(step.tool_name, context, step, session_id)
        self.logger.info(f"[{session_id}] [Agent] 工具参数: {args}")
        
        try:
            result_str = await tool.ainvoke(args)
            
            try:
                tool_result = json.loads(result_str)
            except json.JSONDecodeError:
                tool_result = {"raw_result": result_str}
            
            tool_result["executed"] = True
            tool_result["tool"] = step.tool_name
            
            result_summary = self._get_result_summary(tool_result)
            self.logger.info(f"[{session_id}] [Agent] 执行步骤: {step.name}, 结果摘要: {result_summary}")
            
            return tool_result
        except Exception as e:
            self.logger.error(f"[{session_id}] [Agent] 工具执行失败: {e}")
            return {"error": str(e), "executed": False, "tool": step.tool_name}
    
    def _build_tool_args(self, tool_name: str, context: DiagnosticContext, step, session_id: str = "") -> dict:
        """Build tool arguments from context and step parameters."""
        env = context.environment
        params = step.parameters if hasattr(step, 'parameters') else {}
        node = env.node_info if env else None
        
        match tool_name:
            case "ssh_connect":
                return {
                    "host": node.host if node else params.get("host", "localhost"),
                    "port": node.port if node else params.get("port", 22),
                    "username": node.username if node else params.get("username", "root"),
                    "password": node.password if node else params.get("password"),
                    "ssh_key_path": node.ssh_key_path if node else params.get("ssh_key_path")
                }
            case "log_analysis":
                return {
                    "om_ip": node.host if node else params.get("om_ip", "localhost"),
                    "command": params.get("command", "")
                }
            case "resource_monitor":
                return {
                    "session_id": context.session_id,
                    "metrics": params.get("metrics", ["cpu", "memory", "disk"])
                }
            case "database_query":
                return {
                    "om_ip": node.host if node else params.get("om_ip", "localhost"),
                    "db_name": params.get("db_name", "rmtaskmgmtdb"),
                    "sql": params.get("sql", "")
                }
            case "case_search":
                query_value = params.get("query", context.problem_description)
                self.logger.info(f"[{session_id}] [Agent] case_search 参数: query={query_value}, params={params}")
                return {
                    "session_id": session_id,
                    "query": query_value,
                    "symptoms": params.get("symptoms", context.symptoms),
                    "category": params.get("category", context.category.value if context.category else None),
                    "limit": params.get("limit", 5)
                }
            case "network_diag":
                return {
                    "session_id": context.session_id,
                    "target_host": node.host if node else params.get("target_host", "localhost"),
                    "test_type": params.get("test_type", "ping")
                }
            case "k8s_operation":
                return {
                    "namespace": params.get("namespace", "default"),
                    "pod_name": params.get("pod_name"),
                    "action": params.get("action", "status")
                }
            case "config_check":
                return {
                    "session_id": context.session_id,
                    "config_path": params.get("config_path", "/etc/dtebaseservice/config.yaml"),
                    "check_type": params.get("check_type", "yaml")
                }
            case _:
                return {}
    
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
        similar_cases: list[SearchResult]
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
        
        cases_for_report = [r.case for r in similar_cases]
        
        return DiagnosticReport(
            session_id=context.session_id,
            generated_at=datetime.now(),
            summary=summary,
            problem_category=context.category or ProblemCategory.UNKNOWN,
            severity=context.priority or Severity.MEDIUM,
            hypotheses=hypotheses,
            top_hypothesis=top_hypothesis,
            similar_cases=cases_for_report,
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
    
    async def _search_similar_cases_by_keyword(self, keyword: str, session_id: str) -> list[Case]:
        if not self.kb_manager:
            return []
        
        self.logger.info(f"[{session_id}] [Agent] 关键词检索: {keyword}")
        
        results = await self.kb_manager.search(
            query=keyword,
            keywords=[keyword],
            top_k=3
        )
        cases = [r.case for r in results]
        self.logger.info(f"[{session_id}] [Agent] 关键词检索完成, 返回案例数: {len(cases)}, 案例ID: {[c.case_id for c in cases]}")
        
        return cases