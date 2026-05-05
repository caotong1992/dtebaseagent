"""Diagnostic planning prompt template."""

PLANNING_PROMPT = """你是一个专业的运维诊断规划专家，需要根据问题场景生成诊断计划。

问题信息：
- 问题描述: {problem_description}
- 问题类别: {category}
- 症状列表: {symptoms}
- 时间范围: {time_range}
- 集群名称: {cluster_name}

相似历史案例：
{similar_cases}

请生成一个详细的诊断计划，包括：
1. 需要收集的信息
2. 需要检查的组件
3. 需要执行的工具和命令
4. 检查的优先级顺序

可用诊断工具：
- ssh_connect: SSH连接到目标服务器
- log_analysis: 分析日志文件，搜索错误和异常
- database_query: 查询数据库状态、连接数、慢查询等
- resource_monitor: 采集系统资源指标(CPU、内存、磁盘)
- k8s_operation: K8s集群操作(Pod状态、日志)
- config_check: 检查服务配置文件
- network_diag: 网络连通性测试

请以JSON格式返回诊断步骤列表：
 {{
  "steps": [
    {{
      "name": "步骤名称",
      "description": "步骤描述",
      "tool_name": "工具名称",
      "parameters": {{
        "参数名": "参数值"
      }},
      "priority": 优先级数字(越小越优先)
    }}
  ]
}}

注意：
- 步骤要有明确的优先级顺序
- 每个步骤要指定具体的工具和参数
- 参数要基于用户提供的环境信息设置
"""