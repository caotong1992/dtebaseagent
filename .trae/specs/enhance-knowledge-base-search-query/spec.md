# 知识库查询增强 Spec

## Why
当前知识库检索仅使用原始查询字符串进行简单的关键词匹配，对于中英文混合查询、长句描述、专业术语等场景检索效果不佳。需要将用户输入问题拆分为关键词，并翻译为中英文双语进行检索，提高知识库检索的准确性和可靠性。

## What Changes
- 创建查询预处理模块，实现关键词提取和分词功能
- 创建翻译服务模块，支持中英文双向翻译
- 增强知识库检索逻辑，使用多语言关键词组合检索
- 新增查询预处理配置项

## Impact
- Affected specs: define-knowledge-base-interface
- Affected code: kb/manager.py, kb/local_kb.py, agent/core.py

## ADDED Requirements

### Requirement: 查询预处理
系统 SHALL 在知识库检索前对用户输入进行预处理，提取关键词并翻译为中英文双语。

#### Scenario: 关键词提取
- **WHEN** 用户输入问题描述"用户登录失败，多次尝试后无法访问系统"
- **THEN** 系统提取关键词：["用户", "登录", "失败", "尝试", "访问", "系统"]

#### Scenario: 中文查询翻译为英文
- **WHEN** 提取中文关键词后
- **THEN** 系统翻译为英文关键词：["user", "login", "fail", "attempt", "access", "system"]

#### Scenario: 英文查询翻译为中文
- **WHEN** 用户输入英文问题描述"user login failed after multiple attempts"
- **THEN** 系统提取并翻译为中文关键词：["用户", "登录", "失败"]

#### Scenario: 专业术语保留
- **WHEN** 查询包含专业术语（如 DTEBaseService, PostgreSQL, Kubernetes）
- **THEN** 保留原术语不做翻译，直接作为检索关键词

### Requirement: 多语言组合检索
系统 SHALL 使用中英文关键词组合进行知识库检索，提高检索覆盖率。

#### Scenario: 双语关键词检索
- **WHEN** 预处理生成中文和英文关键词列表
- **THEN** 系统同时使用两组关键词检索案例库

#### Scenario: 检索结果合并
- **WHEN** 中文关键词和英文关键词分别检索
- **THEN** 合并检索结果，按匹配分数排序，去重后返回

#### Scenario: 匹配分数计算
- **WHEN** 计算案例匹配分数
- **THEN** 中文关键词匹配和英文关键词匹配分别计分，累加后为总分

### Requirement: 翻译服务配置
系统 SHALL 支持配置翻译服务，使用已配置的LLM服务进行翻译。

#### Scenario: 使用LLM翻译
- **WHEN** 配置翻译服务为LLM模式
- **THEN** 使用已配置的ChatOpenAI进行关键词翻译

#### Scenario: 翻译缓存
- **WHEN** 同一关键词多次翻译
- **THEN** 使用缓存避免重复调用LLM

### Requirement: 查询预处理配置
系统 SHALL 在配置文件中支持查询预处理相关配置。

#### Scenario: 启用查询预处理
- **WHEN** 配置启用查询预处理（enabled: true）
- **THEN** 知识库检索前自动执行预处理

#### Scenario: 禁用查询预处理
- **WHEN** 配置禁用查询预处理（enabled: false）
- **THEN** 使用原始查询字符串直接检索

## MODIFIED Requirements

### Requirement: 知识库检索接口（原 KnowledgeBaseInterface）
知识库检索接口需支持预处理后的关键词列表查询。

原实现：
```python
async def search(query: str, symptoms: list[str] | None = None, ...) -> list[SearchResult]:
    # 直接使用 query 字符串匹配
    query_lower = query.lower()
    if query_lower in case.title.lower():
        score += 10
```

修改后实现：
```python
async def search(
    query: str,
    keywords: list[str] | None = None,  # 新增：预处理后的关键词列表
    symptoms: list[str] | None = None,
    ...
) -> list[SearchResult]:
    # 支持关键词列表匹配
    for keyword in (keywords or [query]):
        if keyword.lower() in case.title.lower():
            score += 10
```

### Requirement: 诊断流程知识库调用（原 _search_similar_cases）
诊断流程中的知识库调用需集成查询预处理。

原实现：
```python
async def _search_similar_cases(self, context, session_id):
    results = await self.kb_manager.search(
        query=context.problem_description,
        symptoms=context.symptoms,
        top_k=5
    )
```

修改后实现：
```python
async def _search_similar_cases(self, context, session_id):
    # 查询预处理
    preprocessed = await self.query_processor.process(context.problem_description)
    
    results = await self.kb_manager.search(
        query=context.problem_description,
        keywords=preprocessed.all_keywords,  # 中英文关键词列表
        symptoms=context.symptoms,
        top_k=5
    )
```

---

## 详细设计

### 1. 查询预处理模块结构

```
src/dte_diagnostic_agent/kb/
├── query_processor.py       # 查询预处理器
├── translator.py            # 翻译服务
├── keyword_extractor.py     # 关键词提取器
```

### 2. 查询预处理器设计

```python
from dataclasses import dataclass
from dte_diagnostic_agent.kb.translator import TranslatorService

@dataclass
class PreprocessedQuery:
    """预处理后的查询结果"""
    original: str                    # 原始查询
    chinese_keywords: list[str]      # 中文关键词
    english_keywords: list[str]      # 英文关键词
    all_keywords: list[str]          # 合去重后的所有关键词
    
    @property
    def keywords_by_language(self) -> dict[str, list[str]]:
        return {
            "chinese": self.chinese_keywords,
            "english": self.english_keywords
        }

class QueryProcessor:
    """查询预处理器"""
    
    def __init__(self, translator: TranslatorService, config: QueryProcessorConfig):
        self.translator = translator
        self.config = config
        self._cache: dict[str, PreprocessedQuery] = {}
    
    async def process(self, query: str) -> PreprocessedQuery:
        """处理查询，返回预处理结果"""
        if query in self._cache:
            return self._cache[query]
        
        # 1. 提取关键词
        keywords = self._extract_keywords(query)
        
        # 2. 检测语言并翻译
        chinese_kw, english_kw = await self._translate_keywords(keywords)
        
        # 3. 构建结果
        result = PreprocessedQuery(
            original=query,
            chinese_keywords=chinese_kw,
            english_keywords=english_kw,
            all_keywords=self._merge_and_deduplicate(chinese_kw, english_kw)
        )
        
        self._cache[query] = result
        return result
    
    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        import re
        
        # 保留专业术语（大小写混合、包含数字的词）
        technical_terms = re.findall(r'[A-Z][a-zA-Z0-9]*[A-Z0-9]|[A-Z]{2,}[a-z]*', text)
        
        # 中文分词（简单实现：按标点和空格分割）
        chinese_parts = re.findall(r'[\u4e00-\u9fa5]+', text)
        
        # 英文单词
        english_words = re.findall(r'[a-z]+', text.lower())
        
        return technical_terms + chinese_parts + english_words
    
    async def _translate_keywords(self, keywords: list[str]) -> tuple[list[str], list[str]]:
        """翻译关键词为中英文"""
        chinese_kw = []
        english_kw = []
        
        for kw in keywords:
            if self._is_chinese(kw):
                chinese_kw.append(kw)
                translated = await self.translator.translate(kw, "zh", "en")
                english_kw.append(translated)
            elif self._is_technical_term(kw):
                # 专业术语不翻译
                chinese_kw.append(kw)
                english_kw.append(kw)
            else:
                english_kw.append(kw)
                translated = await self.translator.translate(kw, "en", "zh")
                chinese_kw.append(translated)
        
        return chinese_kw, english_kw
    
    def _is_chinese(self, text: str) -> bool:
        return any(c >= '\u4e00' and c <= '\u9fa5' for c in text)
    
    def _is_technical_term(self, text: str) -> bool:
        import re
        return bool(re.match(r'[A-Z][a-zA-Z0-9]*[A-Z0-9]|[A-Z]{2,}', text))
    
    def _merge_and_deduplicate(self, chinese: list[str], english: list[str]) -> list[str]:
        """合并去重"""
        all_kw = chinese + english
        seen = set()
        result = []
        for kw in all_kw:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                result.append(kw)
        return result
```

### 3. 翻译服务设计

```python
from langchain_openai import ChatOpenAI

class TranslatorService:
    """翻译服务"""
    
    def __init__(self, llm: ChatOpenAI | None = None, cache_size: int = 100):
        self.llm = llm
        self._cache: dict[str, str] = {}
        self.cache_size = cache_size
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """翻译文本"""
        cache_key = f"{source_lang}:{target_lang}:{text}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not self.llm:
            return text
        
        prompt = f"将以下{source_lang}关键词翻译为{target_lang}，只返回翻译结果，不要解释：\n{text}"
        
        response = await self.llm.ainvoke(prompt)
        translated = response.content.strip()
        
        # 缓存管理
        if len(self._cache) >= self.cache_size:
            self._cache.clear()
        self._cache[cache_key] = translated
        
        return translated
```

### 4. 知识库检索增强

```python
async def search(
    self,
    query: str,
    keywords: list[str] | None = None,
    symptoms: list[str] | None = None,
    category: str | None = None,
    top_k: int = 10
) -> list[SearchResult]:
    """关键词搜索案例 - 支持多语言关键词"""
    results = []
    
    # 使用预处理关键词或原始查询
    search_terms = keywords if keywords else [query]
    
    for case in self.index.values():
        if category and case.category != category:
            continue
        
        score = 0
        match_reasons = []
        
        # 多关键词匹配
        for term in search_terms:
            term_lower = term.lower()
            
            if term_lower in case.title.lower():
                score += 10
                match_reasons.append(f"标题匹配: {term}")
            
            if term_lower in case.problem.lower():
                score += 5
                match_reasons.append(f"问题描述匹配: {term}")
            
            for tag in case.tags:
                if term_lower in tag.lower():
                    score += 2
                    match_reasons.append(f"标签匹配: {tag}")
        
        # 症状匹配
        for symptom in (symptoms or []):
            if symptom.lower() in [s.lower() for s in case.symptoms]:
                score += 3
                match_reasons.append(f"症状匹配: {symptom}")
        
        if score > 0:
            results.append(SearchResult(
                case=case,
                similarity=min(score / 20, 1.0),
                match_reason="; ".join(match_reasons)
            ))
    
    # 去重（同一案例可能被多个关键词匹配）
    unique_results = {}
    for r in results:
        if r.case.case_id in unique_results:
            # 合并分数
            existing = unique_results[r.case.case_id]
            existing.similarity = min(existing.similarity + r.similarity, 1.0)
            existing.match_reason = f"{existing.match_reason}; {r.match_reason}"
        else:
            unique_results[r.case.case_id] = r
    
    results = list(unique_results.values())
    results.sort(key=lambda r: r.similarity, reverse=True)
    return results[:top_k]
```

### 5. 配置扩展

```yaml
knowledge_base:
  mode: local
  
  # 查询预处理配置
  query_processor:
    enabled: true              # 启用查询预处理
    use_llm_translation: true # 使用LLM翻译
    cache_size: 100           # 翻译缓存大小
  
  local:
    case_dir: ./cases
```

### 6. 集成点修改

**Agent core.py 集成：**
```python
from dte_diagnostic_agent.kb.query_processor import QueryProcessor

class DTEBaseDiagnosticAgent:
    def __init__(self, ..., kb_manager, query_processor_config=None):
        self.kb_manager = kb_manager
        if query_processor_config and query_processor_config.enabled:
            self.query_processor = QueryProcessor(
                translator=TranslatorService(llm=self.llm),
                config=query_processor_config
            )
        else:
            self.query_processor = None
    
    async def _search_similar_cases(self, context, session_id):
        if not self.kb_manager:
            return []
        
        query = context.problem_description
        
        # 查询预处理
        if self.query_processor:
            preprocessed = await self.query_processor.process(query)
            keywords = preprocessed.all_keywords
            self.logger.info(f"[{session_id}] 查询预处理完成, 关键词: {keywords}")
        else:
            keywords = None
        
        results = await self.kb_manager.search(
            query=query,
            keywords=keywords,
            symptoms=context.symptoms,
            top_k=5
        )
        
        return [r.case for r in results]
```