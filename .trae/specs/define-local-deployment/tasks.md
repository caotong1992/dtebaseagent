# Tasks

- [x] Task 1: 创建本地启动入口模块
  - [x] SubTask 1.1: 创建main.py入口模块，支持命令行参数解析
  - [x] SubTask 1.2: 实现配置文件加载逻辑
  - [x] SubTask 1.3: 实现服务启动和优雅关闭逻辑
  - [x] SubTask 1.4: 实现启动参数解析（--config, --port, --host等）

- [x] Task 2: 创建systemd服务配置
  - [x] SubTask 2.1: 创建dte-diagnostic-agent.service文件
  - [x] SubTask 2.2: 创建install.sh安装脚本
  - [x] SubTask 2.3: 创建uninstall.sh卸载脚本

- [x] Task 3: 创建配置文件模板
  - [x] SubTask 3.1: 创建config.yaml.example示例配置
  - [x] SubTask 3.2: 创建完整配置文件文档说明

- [x] Task 4: 移除容器化部署配置
  - [x] SubTask 4.1: 删除deployment/k8s目录下的所有Kubernetes配置
  - [x] SubTask 4.2: 删除deployment/docker目录下的Dockerfile和docker-compose.yaml

- [x] Task 5: 移除监控相关代码
  - [x] SubTask 5.1: 删除AgentMetrics监控指标类
  - [x] SubTask 5.2: 删除告警规则配置文件

- [x] Task 6: 更新design.md文档
  - [x] SubTask 6.1: 更新第10节部署架构，改为本地单机部署方案
  - [x] SubTask 6.2: 移除第11节监控与告警章节
  - [x] SubTask 6.3: 添加本地部署配置说明

- [x] Task 7: 创建部署文档
  - [x] SubTask 7.1: 创建docs/deployment.md本地部署指南

# Task Dependencies

- Task 2 依赖 Task 3（需要配置文件模板才能完成安装脚本）
- Task 4 可与其他任务并行执行
- Task 5 可与其他任务并行执行
- Task 6 可与其他任务并行执行
- Task 7 依赖 Task 1, Task 2, Task 3（需要完整的部署方案才能编写文档）