# 服务日志增强 Spec

## Why
当前服务日志不够完善，缺少关键的调试和运维信息，如大模型调用的输入输出、任务状态转换过程、失败原因等，导致问题排查困难，服务可维护性不足。

## What Changes
- 在LLM调用模块中添加详细的输入输出日志
- 在诊断任务执行流程中添加状态转换日志
- 在异常处理中添加详细的错误信息和堆栈跟踪
- 添加关键业务操作的审计日志

## Impact
- Affected specs: 无
- Affected code: 
  - `agent/core.py` - 诊断流程主入口
  - `agent/intent_parser.py` - 意图解析
  - `agent/planner.py` - 诊断计划生成
  - `agent/reasoning.py` - 推理引擎
  - `api/routes/diagnose.py` - API路由和任务执行

## ADDED Requirements

### Requirement: LLM调用日志
系统应当在所有LLM调用处记录完整的输入输出信息，以便调试和审计。

#### Scenario: 记录LLM调用详情
- **WHEN** 系统调用大模型进行推理
- **THEN** 应记录以下信息：
  - 调用模块名称
  - 完整的prompt内容
  - 模型响应内容
  - 调用耗时
  - token使用量（如可用）

### Requirement: 任务状态转换日志
系统应当记录诊断任务的所有状态转换过程。

#### Scenario: 记录状态转换
- **WHEN** 诊断任务状态发生变化
- **THEN** 应记录以下信息：
  - session_id
  - 原状态 → 新状态
  - 触发转换的操作
  - 时间戳

#### Scenario: 记录任务失败详情
- **WHEN** 诊断任务失败
- **THEN** 应记录以下信息：
  - session_id
  - 失败阶段
  - 完整错误信息
  - 堆栈跟踪
  - 相关上下文信息

### Requirement: 诊断流程日志
系统应当在诊断流程的关键步骤添加日志记录。

#### Scenario: 记录诊断步骤执行
- **WHEN** 执行诊断流程中的某个步骤
- **THEN** 应记录以下信息：
  - session_id
  - 步骤名称
  - 步骤描述
  - 执行结果摘要
  - 执行耗时

### Requirement: 知识库查询日志
系统应当记录知识库查询的详细信息。

#### Scenario: 记录案例搜索
- **WHEN** 系统搜索相似历史案例
- **THEN** 应记录以下信息：
  - 查询关键词
  - 症状列表
  - 返回结果数量
  - 查询耗时
