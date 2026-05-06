# Tasks

- [x] Task 1: 创建关键词提取模块
  - [x] SubTask 1.1: 创建 keyword_extractor.py 文件
  - [x] SubTask 1.2: 实现 _extract_keywords 方法（提取中文词组、英文单词、专业术语）
  - [x] SubTask 1.3: 实现 _is_chinese 和 _is_technical_term 判断方法

- [x] Task 2: 创建翻译服务模块
  - [x] SubTask 2.1: 创建 translator.py 文件
  - [x] SubTask 2.2: 实现 TranslatorService 类
  - [x] SubTask 2.3: 实现 translate 方法（使用LLM翻译）
  - [x] SubTask 2.4: 实现翻译缓存逻辑

- [x] Task 3: 创建查询预处理器模块
  - [x] SubTask 3.1: 创建 query_processor.py 文件
  - [x] SubTask 3.2: 定义 PreprocessedQuery 数据类
  - [x] SubTask 3.3: 实现 QueryProcessor 类
  - [x] SubTask 3.4: 实现 process 方法（整合关键词提取和翻译）
  - [x] SubTask 3.5: 实现 _merge_and_deduplicate 方法（合并去重关键词）

- [x] Task 4: 增强知识库检索接口
  - [x] SubTask 4.1: 在 KnowledgeBaseInterface 添加 keywords 参数
  - [x] SubTask 4.2: 在 LocalMarkdownKB.search 实现多关键词匹配逻辑
  - [x] SubTask 4.3: 实现检索结果合并去重逻辑
  - [x] SubTask 4.4: 在 KnowledgeBaseManager.search 传递 keywords 参数

- [x] Task 5: 创建查询预处理配置模型
  - [x] SubTask 5.1: 在 kb/config.py 添加 QueryProcessorConfig 模型
  - [x] SubTask 5.2: 在 KnowledgeBaseConfig 添加 query_processor 配置项

- [x] Task 6: 集成到诊断流程
  - [x] SubTask 6.1: 在 DTEBaseDiagnosticAgent 初始化 QueryProcessor
  - [x] SubTask 6.2: 在 _search_similar_cases 方法调用查询预处理
  - [x] SubTask 6.3: 添加预处理日志输出

- [x] Task 7: 扩展配置文件
  - [x] SubTask 7.1: 在 config.yaml 添加 query_processor 配置块
  - [x] SubTask 7.2: 在 config.yaml.example 添加配置示例

# Task Dependencies

- Task 2 依赖 Task 0（需要 LLM 配置）
- Task 3 依赖 Task 1, Task 2（需要关键词提取和翻译服务）
- Task 4 依赖 Task 3（需要预处理后的关键词格式）
- Task 5 可独立执行
- Task 6 依赖 Task 3, Task 4, Task 5（需要完整实现）
- Task 7 可与其他任务并行执行