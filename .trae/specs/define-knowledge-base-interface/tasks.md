# Tasks

- [x] Task 1: 创建知识库接口抽象模块
  - [x] SubTask 1.1: 创建KnowledgeBaseInterface抽象类定义
  - [x] SubTask 1.2: 创建Case和SearchResult数据模型
  - [x] SubTask 1.3: 创建KnowledgeBaseManager管理器类

- [x] Task 2: 实现本地Markdown案例库适配器
  - [x] SubTask 2.1: 创建LocalMarkdownKB类实现
  - [x] SubTask 2.2: 实现Markdown文件解析逻辑（frontmatter和章节解析）
  - [x] SubTask 2.3: 实现关键词搜索逻辑
  - [x] SubTask 2.4: 实现案例保存和删除逻辑

- [x] Task 3: 实现远程知识库API适配器
  - [x] SubTask 3.1: 创建RemoteKBClient类实现
  - [x] SubTask 3.2: 实现HTTP API调用逻辑
  - [x] SubTask 3.3: 实现认证和超时配置

- [x] Task 4: 创建案例目录和示例文件
  - [x] SubTask 4.1: 创建案例目录结构（cases/database, cases/network等）
  - [x] SubTask 4.2: 创建示例案例Markdown文件（至少3个示例）

- [x] Task 5: 扩展配置文件
  - [x] SubTask 5.1: 在config.yaml.example中添加knowledge_base配置项
  - [x] SubTask 5.2: 创建KnowledgeBaseConfig配置模型

- [x] Task 6: 适配API端点
  - [x] SubTask 6.1: 修改cases路由使用KnowledgeBaseManager
  - [x] SubTask 6.2: 修改案例搜索、创建、获取端点

- [x] Task 7: 适配CLI命令
  - [x] SubTask 7.1: 修改case命令使用KnowledgeBaseManager
  - [x] SubTask 7.2: 修改search命令使用新接口

- [x] Task 8: 更新design.md文档
  - [x] SubTask 8.1: 更新案例库管理章节，描述新的知识库接口设计
  - [x] SubTask 8.2: 添加本地Markdown案例库说明
  - [x] SubTask 8.3: 添加扩展性设计说明

# Task Dependencies

- Task 2 依赖 Task 1（需要接口抽象）
- Task 3 依赖 Task 1（需要接口抽象）
- Task 5 依赖 Task 1（需要配置模型）
- Task 6 依赖 Task 1, Task 2, Task 3, Task 5（需要完整实现）
- Task 7 依赖 Task 1, Task 2, Task 3, Task 5（需要完整实现）
- Task 4 可独立执行
- Task 8 可与其他任务并行执行