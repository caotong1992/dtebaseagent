# Checklist

## 本地启动入口验证
- [x] main.py入口模块正确解析命令行参数
- [x] --config参数支持自定义配置文件路径
- [x] --port参数支持自定义服务端口
- [x] --host参数支持自定义监听地址
- [x] --api-key参数支持覆盖配置文件中的密钥
- [x] 服务启动时正确加载配置文件
- [x] 服务收到SIGTERM信号时优雅关闭

## systemd服务配置验证
- [x] dte-diagnostic-agent.service文件配置正确
- [x] install.sh安装脚本能正确创建目录和安装服务
- [x] uninstall.sh卸载脚本能正确清理服务和文件

## 配置文件验证
- [x] config.yaml.example包含所有必要配置项
- [x] 配置文件支持server、llm、storage、logging、auth、clusters配置块
- [x] 配置文件加载失败时服务报错退出

## 移除容器化部署验证
- [x] deployment/k8s目录已删除
- [x] deployment/docker目录已删除或无容器化配置

## 移除监控能力验证
- [x] AgentMetrics监控指标类已删除
- [x] 告警规则配置文件已删除

## 文档验证
- [x] design.md部署章节已更新为本地单机部署方案
- [x] design.md监控章节已移除
- [x] docs/deployment.md本地部署指南已创建