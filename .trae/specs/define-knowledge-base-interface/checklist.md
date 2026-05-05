# Checklist

## 知识库接口抽象验证
- [x] KnowledgeBaseInterface抽象类定义正确，包含search/get/save/list_all/delete方法
- [x] Case数据模型包含所有必要字段（case_id, title, category, severity, symptoms等）
- [x] SearchResult数据模型包含case、similarity、match_reason字段
- [x] KnowledgeBaseManager根据配置正确选择后端实现

## 本地Markdown适配器验证
- [x] LocalMarkdownKB正确解析Markdown文件frontmatter元数据
- [x] 正确解析中文章节标题（问题现象、症状列表、解决方案等）
- [x] 关键词搜索逻辑正确匹配标题、问题描述、症状、标签
- [x] 案例保存生成正确的Markdown文件格式
- [x] 案例删除正确移除文件和索引

## 远程知识库适配器验证
- [x] RemoteKBClient正确构造HTTP请求
- [x] API Key认证正确设置到Authorization header
- [x] 超时配置正确生效
- [x] 返回数据正确解析为Case模型

## 案例目录验证
- [x] 案例目录结构正确（database/network子目录）
- [x] 示例Markdown文件格式符合规范
- [x] 文件命名遵循CASE-{id}-{title-slug}.md格式

## 配置验证
- [x] config.yaml.example包含knowledge_base配置块
- [x] 支持mode、local、remote配置项
- [x] 配置加载失败时服务报错提示（validate_config方法）

## 文档验证
- [x] design.md案例库管理章节已更新（6.5节）
- [x] 添加本地Markdown案例库说明
- [x] 添加扩展性设计说明（未来支持的知识库类型）