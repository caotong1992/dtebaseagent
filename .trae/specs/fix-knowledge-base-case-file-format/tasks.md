# Tasks

- [x] Task 1: 修复 CASE-020 案例文件格式
  - [x] Task 1.1: 将 frontmatter 分隔符从 `***` 改为 `---`
  - [x] Task 1.2: 移除 YAML 键中的转义字符（`case\_id` → `case_id` 等）
  - [x] Task 1.3: 移除 YAML 列表项中的转义字符（如有）

- [x] Task 2: 验证修复结果
  - [x] Task 2.1: 重启服务或调用 reload API 重新加载知识库
  - [x] Task 2.2: 使用 "采集任务失败" 作为查询词测试检索功能
  - [x] Task 2.3: 确认 CASE-020 被正确检索返回

- [x] Task 3: (可选) 增强解析器容错能力 - 已跳过（当前问题已通过修复案例文件格式解决）
  - [ ] Task 3.1: 修改 `_parse_frontmatter` 支持 `***` 分隔符 (未执行)
  - [ ] Task 3.2: 添加格式错误警告日志 (未执行)

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 是可选增强，不依赖其他任务