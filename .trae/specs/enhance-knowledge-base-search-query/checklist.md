# Checklist

## 关键词提取验证
- [x] keyword_extractor.py 正确提取中文词组
- [x] 正确提取英文单词
- [x] 正确识别并保留专业术语（如 DTEBaseService, PostgreSQL）
- [x] _is_chinese 判断方法正确识别中文字符
- [x] _is_technical_term 判断方法正确识别专业术语

## 翻译服务验证
- [x] TranslatorService 类正确初始化
- [x] translate 方法正确调用 LLM 进行翻译
- [x] 中文关键词正确翻译为英文
- [x] 英文关键词正确翻译为中文
- [x] 翻译缓存正确工作（相同输入返回缓存结果）
- [x] 缓存大小限制生效

## 查询预处理器验证
- [x] PreprocessedQuery 数据类包含所有必要字段
- [x] QueryProcessor.process 方法返回正确的预处理结果
- [x] chinese_keywords 和 english_keywords 正确生成
- [x] all_keywords 正确合并去重
- [x] 专业术语在双语列表中保留原值

## 知识库检索增强验证
- [x] KnowledgeBaseInterface.search 支持 keywords 参数
- [x] LocalMarkdownKB.search 多关键词匹配正确计分
- [x] 多个关键词匹配同一案例时分数累加
- [x] 检索结果正确去重（同一案例只返回一次）
- [x] KnowledgeBaseManager.search 正确传递 keywords 参数

## 配置验证
- [x] QueryProcessorConfig 模型包含 enabled, use_llm_translation, cache_size 字段
- [x] KnowledgeBaseConfig 包含 query_processor 配置项
- [x] config.yaml 包含 query_processor 配置块
- [x] enabled: false 时跳过预处理直接检索

## 诊断流程集成验证
- [x] DTEBaseDiagnosticAgent 正确初始化 QueryProcessor
- [x] _search_similar_cases 正确调用查询预处理
- [x] 预处理关键词正确传递给知识库检索
- [x] 日志输出预处理后的关键词列表