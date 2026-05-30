"""Diagnostic plan models."""
from re import L
from dte_diagnostic_agent.tools.database import DatabaseQueryTool
from pydantic import BaseModel, Field

from dte_diagnostic_agent.agent.models.parsed_step import ExtractRule
from dte_diagnostic_agent.agent.models.context import DiagnosticContext
from dte_diagnostic_agent.agent.info_extractor import ResultExtractor
from dte_diagnostic_agent.tools import STATIC_TOOLS
import logging
import json

logger = logging.getLogger(__name__)

class DiagnosticStepModel(BaseModel):
    step_number: int = Field(description="Step number")
    name: str = Field(description="Step name")
    description: str = Field(default="", description="Step description")
    tool_name: str = Field(description="Tool name to execute")
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")
    priority: int = Field(default=0, description="Step priority")
    dependencies: list[str] = Field(default_factory=list, description="Dependent step names")
    template_vars: list[str] = Field(default_factory=list, description="Template variables in parameters")
    output_vars: list[str] = Field(default_factory=list, description="Output variable names")
    extract_rules: dict[str, ExtractRule] = Field(default_factory=dict, description="Extraction rules for output variables")
    next_step: int | None = Field(default=None, description="Next step index")
    next_step_if_true: int | None = Field(default=None, description="Next step index if condition is True")
    next_step_if_false: int | None = Field(default=None, description="Next step index if condition is False")
    condition: str | None = Field(default="", description="Condition to evaluate")
    action_type: str = Field(default="", description="Action type")

class DiagnosticStep(BaseModel):
    name: str = Field(default="", description="Step name")
    description: str = Field(default="", description="Step description")
    template_vars: list[str] = Field(default_factory=list, description="Template variables in parameters")
    output_vars: list[str] = Field(default_factory=list, description="Output variable names")
    extract_rules: dict[str, ExtractRule] = Field(default_factory=dict, description="Extraction rules for output variables")
    next_step: DiagnosticStepModel = Field(default=None, description="New step")

    def __init__(self, **data):
        super().__init__(**data)

    def from_model(self, model: DiagnosticStepModel) -> None:
        self.name = model.name
        self.description = model.description
        self.template_vars = model.template_vars
        self.output_vars = model.output_vars
        self.extract_rules = model.extract_rules

    async def execute(self, context: DiagnosticContext, session_id: str) -> Any:
        '''Execute the step based on the condition.'''
        raise NotImplementedError("execute method not implemented")
    
    def get_next_step(self) -> DiagnosticStepModel:
        return self.next_step
    
    def print_tree_node(self, indent: int = 0):
        '''Print the step details'''
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        print(f"{indent_str}{symbol} [步骤] {self.name}")
        if self.description:
            print(f"{indent_str}    └─ 描述: {self.description[:50]}..." if len(self.description) > 50 else f"{indent_str}    └─ 描述: {self.description}")
    
    def print_tree(self, indent: int = 0):
        '''Print the step details'''
        self.print_tree_node(indent)
        if self.next_step:
            self.next_step.print_tree(indent + 1)

class DecisionDiagnosticStep(DiagnosticStep):
    condition: str = Field(default="", description="Condition to evaluate")
    next_step_if_true: DiagnosticStepModel = Field(default=None, description="Next step if condition is True")
    next_step_if_false: DiagnosticStepModel = Field(default=None, description="Next step if condition is False")

    def from_model(self, model: DiagnosticStepModel) -> None:
        super().from_model(model)
        self.condition = model.condition
        self.next_step_if_true = None
        self.next_step_if_false = None
    
    def get_next_step(self) -> DiagnosticStepModel:
        return self.next_step
    
    def print_tree_node(self, indent: int = 0):
        '''Print the step details'''
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        condition_display = self.condition if self.condition else "条件判断"
        print(f"{indent_str}{symbol} [决策节点] {self.description}")
        print(f"{indent_str}    └─ 条件: {condition_display}")

    
    def print_tree(self, indent: int = 0):
        indent_str = "  " * indent
        self.print_tree_node(indent)
        if self.next_step_if_true:
            print(f"{indent_str}  │")
            print(f"{indent_str}  ├─ [True] ")
            self.next_step_if_true.print_tree(indent + 2)
        if self.next_step_if_false: 
            print(f"{indent_str}  │")
            print(f"{indent_str}  └─ [False] ")
            self.next_step_if_false.print_tree(indent + 2)
    
    async def execute(self, context: DiagnosticContext, session_id: str) -> Any:
        '''Execute the step based on the condition.'''
        logger.info(f"[{session_id}] [Agent] 执行步骤: {self.name}, 条件: {self.condition}")
        if self.condition:
            condition = self._evaluate_condition(self.condition, context, session_id)
            if condition:
                return self.next_step_if_true
            else:
                return self.next_step_if_false
        else:
            return self.next_step_if_true
        
    def _evaluate_condition(self, condition: str, context: DiagnosticContext, session_id: str) -> bool:
        '''Evaluate the condition using the context variables.'''
        logger.info(f"[{session_id}] [Agent] 评估条件: {condition}")
        try:
            result = eval(condition, context)
            logger.info(f"[{session_id}] [Agent] 条件评估结果: {result}")
            return result
        except Exception as e:
            logger.error(f"[{session_id}] [Agent] 条件评估错误: {e}")
            return False
        except NameError:
            logger.error(f"[{session_id}] [Agent] 条件评估错误: 未定义的变量")
            return False
    

    
class ToolCallDiagnosticStep(DiagnosticStep):
    tool_name: str = Field(default="", description="Tool name to execute")
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")
    

    def from_model(self, model: DiagnosticStepModel) -> None:
        super().from_model(model)
        self.tool_name = model.tool_name
        self.parameters = model.parameters
    
    async def execute(self, context: DiagnosticContext, session_id: str) -> Any:
        '''Execute the step based on the condition.'''
        logger.info(f"[{session_id}] [Agent] 执行步骤: {self.name}, 工具: {self.tool_name}")
        
        tool = self._get_tool(self.tool_name)
        if not tool:
            logger.warning(f"[{session_id}] [Agent] 未知工具: {self.tool_name}")
            return {"error": f"Unknown tool: {self.tool_name}", "executed": False}
        
        args = self._build_tool_args(self.tool_name, context, self, session_id)
        logger.info(f"[{session_id}] [Agent] 工具参数: {args}")
        return await self._call_tool(tool, args, context, self, session_id)
    
    def _get_case_search_tool(self):
        if self._case_search_tool is None:
            if self.kb_manager:
                self._case_search_tool = create_case_search_tool(self.kb_manager)
                logger.info("[Agent] 创建 case_search 工具, 使用知识库管理器")
            else:
                self._case_search_tool = MockCaseSearchTool
                logger.info("[Agent] 创建 case_search 工具, 使用 Mock 实现")
        return self._case_search_tool

    def _get_tool(self, tool_name: str):
        return STATIC_TOOLS.get(tool_name)
    
    async def _call_tool(self, tool, args: dict, context: DiagnosticContext, step, session_id: str = "") -> dict:
        """Call a tool with the given name and parameters."""
        try:
            result_str = await tool.ainvoke(args)
            try:
                tool_result = json.loads(result_str)
            except json.JSONDecodeError:
                tool_result = {"raw_result": result_str}
            
            tool_result["executed"] = True
            tool_result["tool"] = step.tool_name
            
            result_summary = self._get_result_summary(tool_result)
            logger.info(f"[{session_id}] [Agent] 执行步骤: {step.name}, 结果摘要: {result_summary}")
            return tool_result
        except Exception as e:
            logger.error(f"[{session_id}] [Agent] 工具执行失败: {e}")
            return {"error": str(e), "executed": False, "tool": step.tool_name}



    def _build_tool_args(self, tool_name: str, context: DiagnosticContext, step, session_id: str = "") -> dict:
        """Build tool arguments from context and step parameters."""
        env = context.environment
        params = step.parameters if hasattr(step, 'parameters') else {}
        node = env.node_info[0] if env else None
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
                    "command": params.get("command", ""),
                    "root_pwd": node.root_password if node else params.get("root_pwd"),
                    "sopuser_pwd": node.password if node else params.get("sopuser_pwd"),
                    "ossadm_pwd": node.password if node else params.get("ossadm_pwd"),
                    "ssh_user": node.username if node else params.get("sshUser"),
                }
            case "resource_monitor":
                return {
                    "session_id": context.session_id,
                    "metrics": params.get("metrics", ["cpu", "memory", "disk"])
                }
            case "database_query":
                return {
                    "om_ip": node.host if node else params.get("om_ip", "localhost"),
                    "db_name": params.get("db_name", ""),
                    "sql": params.get("sql", ""),
                    "root_pwd": node.root_password if node else params.get("root_pwd"),
                    "sopuser_pwd": node.password if node else params.get("sopuser_pwd"),
                    "ossadm_pwd": node.password if node else params.get("ossadm_pwd"),
                    "ssh_user": node.username if node else params.get("sshUser"),
                }
            case "case_search":
                query_value = params.get("query", context.problem_description)
                logger.info(f"[{session_id}] [Agent] case_search 参数: query={query_value}, params={params}")
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
        if "rows" in result:
            return f"rows={result['rows'][:50]}"
        return "completed"
    
    def print_tree_node(self, indent: int = 0):
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())[:50]
        if len(str(self.parameters)) > 50:
            params_str += "..."
        print(f"{indent_str}{symbol} [工具调用] {self.name}")
        print(f"{indent_str}    ├─ 步骤说明: {self.description}")
        print(f"{indent_str}    ├─ 工具: {self.tool_name}")
        print(f"{indent_str}    ├─ 参数: {params_str}")
        print(f"{indent_str}    ├─ 模板变量: {', '.join(self.template_vars) if self.template_vars else '无'}")
        print(f"{indent_str}    └─ 输出变量: {', '.join(self.output_vars) if self.output_vars else '无'}")

class CaseSearchDiagnosticStep(DiagnosticStep):
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")

    def from_model(self, model: DiagnosticStepModel) -> None:
        super().from_model(model)
        self.parameters = model.parameters
    
    def print_tree_node(self, indent: int = 0):
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        query = self.parameters.get("query", "")[:30] + "..." if len(str(self.parameters.get("query", ""))) > 30 else self.parameters.get("query", "")
        category = self.parameters.get("category", "无")
        print(f"{indent_str}{symbol} [案例检索] {self.name}")
        print(f"{indent_str}    ├─ 查询: {query}")
        print(f"{indent_str}    ├─ 分类: {category}")
        print(f"{indent_str}    └─ 输出变量: {', '.join(self.output_vars) if self.output_vars else '无'}")

        

class CaseAnalysisDiagnosticStep(DiagnosticStep):
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")

    def from_model(self, model: DiagnosticStepModel) -> None:
        super().from_model(model)
        self.parameters = model.parameters

    def print_tree_node(self, indent: int = 0):
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        print(f"{indent_str}{symbol} [案例分析] {self.name}")
        if self.description:
            print(f"{indent_str}    └─ 描述: {self.description[:50]}..." if len(self.description) > 50 else f"{indent_str}    └─ 描述: {self.description}")
        else:
            print(f"{indent_str}    └─ 输出变量: {', '.join(self.output_vars) if self.output_vars else '无'}")
        
    async def execute(self, context: DiagnosticContext, session_id: str) -> dict:
        '''Execute the case analysis step.'''
        logger.info(f"开始执行案例分析步骤 {self.name}")
        result = await self._execute_tool(context, session_id)
        return result

class KeywordExtractDiagnosticStep(DiagnosticStep):
    parameters: dict[str, object] = Field(default_factory=dict, description="Tool parameters")

    def from_model(self, model: DiagnosticStepModel) -> None:
        super().from_model(model)
        self.parameters = model.parameters
    
    def print_tree_node(self, indent: int = 0):
        indent_str = "  " * indent
        symbol = "├─" if indent > 0 else "●"
        print(f"{indent_str}{symbol} [关键词提取器] {self.name}")
        print(f"{indent_str}    └─ 描述: {self.description[:50]}..." if len(self.description) > 50 else f"{indent_str}    └─ 描述: {self.description}")
        print(f"{indent_str}    └─ 输入变量: {', '.join(self.template_vars) if self.template_vars else '无'}")
        print(f"{indent_str}    └─ 输出变量: {', '.join(self.output_vars) if self.output_vars else '无'}")
        
    async def execute(self, context: DiagnosticContext, session_id: str) -> dict:
        '''Execute the keyword extract step.'''
        logger.info(f"开始执行关键词提取器步骤 {self.name}")
        logger.info(f"输入变量: {self.template_vars}")
        logger.info(f"输出变量: {self.output_vars}")
        logger.info(f"提取规则: {self.extract_rules}")
        
        result = {}
        for var_name in self.template_vars:
            var_value = context.get_var_value(var_name)
            logger.info(f"变量 {var_name} 的值: {var_value}")
        for var_name, rule in self.extract_rules.items():
            logger.info(f"变量 {var_name} 的提取规则: {rule}")
            if rule.type == "field":
                logger.info(f"从 {rule.source} 中提取字段 {rule.value}")
            elif rule.type == "regex":
                logger.info(f"从 {rule.source} 中提取正则表达式 {rule.value}")
            elif rule.type == "json_path":
                logger.info(f"从 {rule.source} 中提取 JSON 路径 {rule.value}")
                result[var_name] = self._extract_var_from_json(var_name, var_value)
            else:
                logger.error(f"未知提取类型 {rule.type}")
                
        return result

    def _extract_var_from_json(self, var_name: str, json_str: str) -> list[object]:
        '''Extract a variable from JSON string using JSON path.'''
        logger.info(f"从 JSON 字符串 {json_str} 中提取 JSON 路径 {var_name} 的值")
        try:
            data = json.loads(json_str)
            value = self._extract_var_from_dict(var_name, data)
            logger.info(f"提取到的值: {value}")
            return value
        except (json.JSONDecodeError) as e:
            logger.error(f"提取 JSON 路径 {var_name} 时出错: {e}")
            return None
    
    def _extract_var_from_dict(self, var_name: str, data: Any) -> list[object]:
        '''Extract a variable from regex string using regex pattern.'''
        result = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k == var_name:
                    result.append(v)
                else:
                    result.extend(self._extract_var_from_dict(var_name, v))
        elif isinstance(data, list):
            for item in data:
                result.extend(self._extract_var_from_dict(var_name, item))
        return result


class DiagnosticPlan:

    def __init__(self, session_id: str, steps: list[DiagnosticStepModel], estimated_duration: int = 300):
        self.session_id = session_id
        self.estimated_duration = estimated_duration
        self.root_step = self._generate_diagnostic_tree(steps)
        self.current_step = self.root_step
    

    def _generate_diagnostic_tree(self, steps: list[DiagnosticStepModel]) -> DiagnosticStep:
        '''Generate the diagnostic tree from the steps.'''
        logger.info(f"开始生成诊断计划树，共 {len(steps)} 个步骤")
        sorted_steps = sorted(steps, key=lambda s: s.priority)
        converted_steps_map: dict[int, DiagnosticStep] = {}
        for step in sorted_steps:
            converted_step = None
            if step.action_type == "tool_execute":
                converted_step=ToolCallDiagnosticStep()
            elif step.action_type == "decision":
                converted_step=DecisionDiagnosticStep()
            elif step.action_type == "case_search":
                converted_step=CaseSearchDiagnosticStep()
            elif step.action_type == "case_analysis":
                converted_step=CaseAnalysisDiagnosticStep()
            elif step.action_type == "keyword_extract":
                converted_step=KeywordExtractDiagnosticStep()
            else:
                raise ValueError(f"未知的步骤类型: {step.action_type}")
            converted_step.from_model(step)
            converted_steps_map[step.step_number] = converted_step
        
        logger.info(f"开始生成诊断计划树，共 {len(sorted_steps)} 个步骤")
        root_step = None
        for i in range(len(sorted_steps)):
            step = sorted_steps[i]
            if root_step is None:
                root_step = converted_steps_map[step.step_number]
            logger.info(f"当前步骤: {step.step_number}, 类型: {step.action_type}")
            if step.action_type == "decision":
                if step.next_step_if_true:
                    converted_steps_map[step.step_number].next_step_if_true = converted_steps_map[step.next_step_if_true]
                if step.next_step_if_false:
                    converted_steps_map[step.step_number].next_step_if_false = converted_steps_map[step.next_step_if_false]
            else:
                if step.next_step:
                    converted_steps_map[step.step_number].next_step = converted_steps_map[step.next_step]
        logger.info(f"诊断计划树生成完成, root_step={root_step.description}")
        return root_step

    def has_next_step(self) -> bool:
        return self.current_step is not None

    def next_step(self) -> DiagnosticStep:
        '''Get the next step in the plan.'''
        next_step = self.current_step
        self.current_step = self.current_step.get_next_step()
        return next_step

    def _print_diagnostic_tree(self, step: DiagnosticStep, indent: int = 0, prefix: str = ""):
        '''Print the diagnostic tree starting from the given step.'''
        step.print_tree(indent)

    def print_overview(self):
        '''Print diagnostic plan overview'''
        logger.info("开始打印诊断计划概览")
        self._print_diagnostic_tree(self.root_step)
        logger.info("诊断计划概览打印完成")

    def get_executor(self) -> DiagnosticPlanExecutor:
        return DiagnosticPlanExecutor(self.session_id, self)


class DiagnosticPlanExecutor:

    def __init__(self, session_id: str, plan: DiagnosticPlan):
        self.session_id = session_id
        self.result_extractor = ResultExtractor()
        self.plan = plan

    async def execute(self, context: DiagnosticContext):
        '''Execute the diagnostic plan.'''
        logger.info("开始执行诊断计划")
        self.plan.print_overview()
        results = {}
        while self.plan.has_next_step():
            step = self.plan.next_step()
            logger.info(f"[{self.session_id}] [Agent] 执行步骤: {step.description}")
            self._set_step_vars(context, step, self.session_id)
            result = await step.execute(context, self.session_id)
            context.collected_data[step.name] = result
            results[step.name] = result
            self._update_context_params(context, step, self.session_id, result)

    def _set_step_vars(self, context: DiagnosticContext, step: DiagnosticStep, session_id: str):
        '''
        设置步骤参数中的模板变量
        '''
        if not step.template_vars:
            return
        step.parameters = self._replace_template_vars(step.parameters, context.collected_data)
        logger.info(f"[{session_id}] [Agent] 步骤 {step.name} 模板变量替换后参数: {step.parameters}")

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
    
    def _update_context_params(self, context: DiagnosticContext, step: DiagnosticStep, session_id: str, result: dict):
        '''
        更新上下文参数
        '''
        output_vars = getattr(step, 'output_vars', [])
        extract_rules = getattr(step, 'extract_rules', {})
        if not output_vars:
            return
        extract_rules_dict = self._convert_extract_rules(extract_rules)
        extracted = self.result_extractor.extract(result, output_vars, extract_rules_dict, session_id)
        for var_name, var_value in extracted.items():
            if var_value is not None:
                logger.info(f"[{session_id}] [Agent] 提取变量: {var_name}={var_value}")
                context.set_var(var_name, var_value)
    
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