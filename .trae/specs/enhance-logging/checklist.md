# Checklist

## LLM调用日志
- [x] intent_parser.py 记录LLM调用耗时
- [x] intent_parser.py 记录token使用量
- [x] planner.py 记录LLM调用输入输出
- [x] reasoning.py 记录LLM推理调用详情

## 任务状态转换日志
- [x] diagnose.py 记录PENDING → RUNNING状态转换
- [x] diagnose.py 记录RUNNING → COMPLETED状态转换
- [x] diagnose.py 记录RUNNING → FAILED状态转换
- [x] diagnose.py 记录任务取消状态转换

## 错误处理日志
- [x] diagnose.py 记录完整的异常堆栈跟踪
- [x] diagnose.py 记录失败阶段的上下文信息

## 诊断流程日志
- [x] core.py 记录诊断流程开始
- [x] core.py 记录各步骤执行情况
- [x] core.py 记录知识库查询结果

## 日志格式规范
- [x] 所有日志包含session_id（如适用）
- [x] 所有日志包含模块名称
- [x] 耗时类日志使用毫秒为单位
