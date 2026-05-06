# Checklist

## bin 目录验证
- [x] bin 目录已创建

## Windows 启动脚本验证
- [x] start.bat 文件已创建
- [x] 端口检查逻辑正确（使用 netstat）
- [x] 进程停止逻辑正确（使用 taskkill）
- [x] 服务启动逻辑正确（使用 python -m）
- [x] 支持自定义端口参数

## Windows 停止脚本验证
- [x] stop.bat 文件已创建
- [x] 端口检查和进程停止逻辑正确
- [x] 无进程时输出正确提示

## Linux 启动脚本验证
- [x] start.sh 文件已创建
- [x] 端口检查逻辑正确（使用 lsof）
- [x] PID 文件管理正确（写入和读取）
- [x] 服务启动逻辑正确（使用 nohup）
- [x] 日志输出配置正确
- [x] 支持自定义端口参数

## Linux 停止脚本验证
- [x] stop.sh 文件已创建
- [x] PID 文件检查逻辑正确
- [x] 端口检查逻辑正确
- [x] 进程停止逻辑正确（kill 和 kill -9）
- [x] PID 文件清理正确

## 文档更新验证
- [x] AGENTS.md 新增第9节"启动脚本"
- [x] AGENTS.md 章节编号正确调整
- [x] design.md 增加部署脚本说明