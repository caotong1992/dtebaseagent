# Tasks

- [x] Task 1: 修改 start.bat 添加重启参数
  - [x] SubTask 1.1: 添加参数解析逻辑（解析 --restart 和 -r）
  - [x] SubTask 1.2: 添加 FORCE_RESTART 变量判断
  - [x] SubTask 1.3: 修改进程检查逻辑（强制重启时跳过同进程检测）
  - [x] SubTask 1.4: 测试正常启动和强制重启两种场景

- [x] Task 2: 修改 start.sh 添加重启参数
  - [x] SubTask 2.1: 添加参数解析逻辑（解析 --restart 和 -r）
  - [x] SubTask 2.2: 添加 FORCE_RESTART 变量判断
  - [x] SubTask 2.3: 修改进程检查逻辑

# Task Dependencies

- Task 1 和 Task 2 可并行执行