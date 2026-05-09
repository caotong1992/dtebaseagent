"""Intent understanding prompt template."""

INTENT_PROMPT = """你是一个专业的运维诊断助手，负责分析用户描述的问题并提取关键信息。

用户输入：
{user_input}

请分析以上输入，提取以下信息并以JSON格式返回：

1. problem_description: 问题现象的详细描述
2. time_range: 问题发生的时间范围
   - start: 开始时间 (格式: YYYY-MM-DD HH:MM:SS)
   - end: 结束时间 (格式: YYYY-MM-DD HH:MM:SS)
3. environment: 环境信息
   - cluster_name: 集群名称
   - node_info: 节点登录信息
     - host: 节点IP或域名
     - port: SSH端口
     - username: 登录用户名
     - auth_type: 认证类型 (password/ssh_key)
   - service_name: 服务名称
   - namespace: K8s命名空间
4. symptoms: 问题症状列表 (关键词列表)
5. priority: 优先级 (critical/high/medium/low)
6. category: 问题类别，从以下选项中选择：
   - service_unavailable: 服务不可用
   - performance_degradation: 性能下降
   - data_inconsistency: 数据不一致
   - network_issue: 网络问题
   - resource_exhaustion: 资源耗尽
   - configuration_error: 配置错误
   - collection_task_failed:  采集任务失败
   - unknown: 未知类型

注意：
- 如果用户未提供某些信息，请根据上下文合理推断
- 时间信息要转换为标准格式
- symptoms要提取关键症状关键词

请直接返回JSON对象，不要包含其他解释文字。
"""