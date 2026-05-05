# Agent核心能力实现 Spec

## Why
基于design.md设计方案，实现完整的DTEBaseService问题定位AI Agent核心能力，包括意图理解、诊断规划、推理决策等核心模块以及SSH连接、日志分析、数据库查询等诊断工具。

## What Changes
- 实现Agent核心模块（意图理解、规划调度、推理决策）
- 实现诊断工具集（SSH、日志、数据库、指标、K8s等）
- 实现Prompt模板
- 实现数据模型
- 集成LangChain 2.15.4 Agent框架

## Impact
- Affected specs: 所有核心模块和工具
- Affected code: src/dte_diagnostic_agent/agent/, src/dte_diagnostic_agent/tools/

## ADDED Requirements

### Requirement: Agent核心模块
系统 SHALL 实现完整的Agent核心能力，包括意图理解、诊断规划、推理决策等模块。

#### Scenario: 意图理解
- **WHEN** 用户提交诊断请求
- **THEN** 系统通过IntentParser解析问题描述、时间范围、环境信息

#### Scenario: 诊断规划
- **WHEN** 完成意图解析后
- **THEN** DiagnosticPlanner基于问题类型和历史案例生成诊断计划

#### Scenario: 推理决策
- **WHEN** 收集诊断证据后
- **THEN** ReasoningEngine分析数据并生成问题假设

### Requirement: 诊断工具集
系统 SHALL 提供完整的诊断工具集，支持连接环境、分析日志、查询数据库等操作。

#### Scenario: SSH连接
- **WHEN** 工具调用ssh_connect
- **THEN** 成功建立SSH连接并返回会话

#### Scenario: 日志分析
- **WHEN** 工具调用log_analysis
- **THEN** 获取指定时间范围的日志并分析异常

#### Scenario: 数据库查询
- **WHEN** 工具调用database_query
- **THEN** 返回连接状态、慢查询、锁状态等信息

### Requirement: Prompt模板
系统 SHALL 定义完整的Prompt模板用于LLM交互。

#### Scenario: 意图解析Prompt
- **WHEN** 调用意图解析
- **THEN** 使用预定义的意图理解Prompt引导LLM输出结构化信息

#### Scenario: 推理分析Prompt
- **WHEN** 执行推理分析
- **THEN** 使用推理Prompt引导LLM生成问题假设

### Requirement: Agent集成
系统 SHALL 将所有模块集成到DTEBaseDiagnosticAgent主类中。

#### Scenario: Agent初始化
- **WHEN** 创建Agent实例
- **THEN** 加载LLM、工具、Prompt模板并创建AgentExecutor

#### Scenario: 诊断流程
- **WHEN** 调用diagnose方法
- **THEN** 完整执行意图解析→案例检索→规划→工具执行→推理→报告生成流程

---

## 详细实现范围

### 1. Agent核心模块

#### 1.1 意图理解模块 (IntentParser)
```python
class IntentParser:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def parse(self, user_input: UserInput) -> DiagnosticContext:
        # 解析问题描述、时间范围、环境信息
        # 返回DiagnosticContext
```

#### 1.2 规划调度模块 (DiagnosticPlanner)
```python
class DiagnosticPlanner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def generate_plan(
        self,
        context: DiagnosticContext,
        similar_cases: list[Case]
    ) -> DiagnosticPlan:
        # 基于问题类型生成诊断步骤
```

#### 1.3 推理决策模块 (ReasoningEngine)
```python
class ReasoningEngine:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.rules: list[DiagnosticRule] = []
    
    async def analyze(self, context: DiagnosticContext) -> list[Hypothesis]:
        # 规则推理 + LLM推理
        # 返回问题假设列表
```

### 2. 诊断工具集

| 工具名称 | 功能 | 输入参数 |
|---------|------|----------|
| SSHConnectTool | SSH连接 | host, port, username, password/ssh_key |
| LogAnalysisTool | 日志分析 | session_id, log_path, time_range, patterns |
| DatabaseQueryTool | 数据库查询 | db_host, db_port, db_name, query_type |
| ResourceMonitorTool | 指标采集 | session_id, metrics |
| CaseSearchTool | 案例检索 | query, symptoms, category |
| K8sOperationTool | K8s操作 | namespace, pod_name, action |
| ConfigCheckTool | 配置检查 | session_id, config_path |
| NetworkDiagTool | 网络诊断 | session_id, target_host |

### 3. Prompt模板

#### 3.1 意图理解Prompt
```
你是一个专业的运维诊断助手，负责分析用户描述的问题并提取关键信息。

用户输入：
{user_input}

请分析以上输入，提取以下信息并以JSON格式返回：
1. problem_description: 问题现象的详细描述
2. time_range: 问题发生的时间范围
3. environment: 环境信息
...
```

#### 3.2 诊断规划Prompt
```
你是一个专业的运维诊断规划专家...

问题信息：
- 问题描述: {problem_description}
- 问题类别: {category}
...

请生成一个详细的诊断计划...
```

#### 3.3 推理分析Prompt
```
你是一个专业的运维诊断分析专家...

问题上下文：
{context}

收集的证据：
{collected_evidence}

请分析以上信息，输出：
1. 可能的问题原因
2. 每个原因的支持证据
...
```

### 4. 数据模型

#### 4.1 DiagnosticContext
```python
class DiagnosticContext(BaseModel):
    session_id: str
    problem_description: str
    time_range: TimeRange
    environment: ClusterInfo
    symptoms: list[str]
    priority: Severity
    category: ProblemCategory | None
    collected_data: dict[str, object]
```

#### 4.2 Hypothesis
```python
class Hypothesis(BaseModel):
    id: str
    problem: str
    confidence: float
    evidence: list[str]
    actions: list[str]
    source: str
```

#### 4.3 DiagnosticPlan
```python
class DiagnosticPlan(BaseModel):
    steps: list[DiagnosticStep]

class DiagnosticStep(BaseModel):
    name: str
    tool_name: str
    parameters: dict[str, object]
    priority: int
```

### 5. Agent主类集成

```python
class DTEBaseDiagnosticAgent:
    def __init__(self, config: AgentConfig):
        self.llm = ChatOpenAI(...)
        self.tools = self._init_tools()
        self.intent_parser = IntentParser(llm=self.llm)
        self.planner = DiagnosticPlanner(llm=self.llm)
        self.reasoning_engine = ReasoningEngine(llm=self.llm)
        self.case_retriever = KnowledgeBaseManager(...)
        self.agent_executor = AgentExecutor(...)
    
    async def diagnose(self, user_input: UserInput) -> DiagnosticReport:
        # 1. 意图解析
        context = await self.intent_parser.parse(user_input)
        # 2. 案例检索
        similar_cases = await self.case_retriever.search(...)
        # 3. 生成计划
        plan = await self.planner.generate_plan(context, similar_cases)
        # 4. 执行工具
        for step in plan.steps:
            result = await self._execute_tool(step)
        # 5. 推理分析
        hypotheses = await self.reasoning_engine.analyze(context)
        # 6. 生成报告
        report = self._generate_report(...)
        return report
```