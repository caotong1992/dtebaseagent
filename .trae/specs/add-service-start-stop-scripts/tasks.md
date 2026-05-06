# Tasks

- [x] Task 1: 创建 bin 目录
  - [x] SubTask 1.1: 创建 d:\code\dtebaseagent\bin 目录

- [x] Task 2: 创建 Windows 启动脚本
  - [x] SubTask 2.1: 创建 start.bat 文件
  - [x] SubTask 2.2: 实现端口检查逻辑（netstat）
  - [x] SubTask 2.3: 实现进程停止逻辑（taskkill）
  - [x] SubTask 2.4: 实现服务启动逻辑

- [x] Task 3: 创建 Windows 停止脚本
  - [x] SubTask 3.1: 创建 stop.bat 文件
  - [x] SubTask 3.2: 实现端口检查和进程停止逻辑

- [x] Task 4: 创建 Linux 启动脚本
  - [x] SubTask 4.1: 创建 start.sh 文件
  - [x] SubTask 4.2: 实现端口检查逻辑（lsof）
  - [x] SubTask 4.3: 实现 PID 文件管理
  - [x] SubTask 4.4: 实现服务启动逻辑（nohup）
  - [x] SubTask 4.5: 设置脚本可执行权限说明

- [x] Task 5: 创建 Linux 停止脚本
  - [x] SubTask 5.1: 创建 stop.sh 文件
  - [x] SubTask 5.2: 实现 PID 文件和端口双重检查
  - [x] SubTask 5.3: 实现进程停止逻辑

- [x] Task 6: 更新 AGENTS.md 文档
  - [x] SubTask 6.1: 在 AGENTS.md 新增第9节"启动脚本 (bin/)"
  - [x] SubTask 6.2: 调整后续章节编号

- [x] Task 7: 更新 design.md 文档
  - [x] SubTask 7.1: 在 design.md 增加部署脚本使用说明

# Task Dependencies

- Task 1 需首先执行（创建目录）
- Task 2, 3, 4, 5 可并行执行（创建脚本）
- Task 6, 7 依赖 Task 2-5 完成（文档更新）