"""Query processor for preprocessing knowledge base search queries."""

import logging
from dataclasses import dataclass, field

from dte_diagnostic_agent.kb.config import QueryProcessorConfig
from dte_diagnostic_agent.kb.keyword_extractor import KeywordExtractor
from dte_diagnostic_agent.kb.translator import TranslatorService


@dataclass
class PreprocessedQuery:
    """Preprocessed query result with multilingual keywords."""
    
    original: str
    chinese_keywords: list[str] = field(default_factory=list)
    english_keywords: list[str] = field(default_factory=list)
    all_keywords: list[str] = field(default_factory=list)
    
    @property
    def keywords_by_language(self) -> dict[str, list[str]]:
        """Return keywords grouped by language."""
        return {
            "chinese": self.chinese_keywords,
            "english": self.english_keywords,
        }


class QueryProcessor:
    """Process queries for multilingual keyword extraction and translation."""
    
    TECHNICAL_TERMS = frozenset({
        "DTEBaseService", "PostgreSQL", "MySQL", "Redis", "MongoDB",
        "Kubernetes", "K8s", "Docker", "API", "REST", "gRPC",
        "HTTP", "HTTPS", "TCP", "UDP", "IP", "DNS", "SSH", "SSL", "TLS",
        "CPU", "Memory", "RAM", "GPU", "SSD", "HDD",
        "JWT", "OAuth", "OIDC", "LDAP",
        "JSON", "XML", "YAML", "SQL", "NoSQL",
        "JVM", "GC", "OOM", "SDK", "CLI", "IDE",
    })
    
    def __init__(self, translator: TranslatorService, config: QueryProcessorConfig | None):
        self.keyword_extractor = KeywordExtractor()
        self.translator = translator
        self.config = config or None
        
        self._cache: dict[str, PreprocessedQuery] = {}
        
        self.logger = logging.getLogger(__name__)
        
        if self.config:
            self.logger.info(f"QueryProcessor initialized with cache_size={self.config.cache_size}")
    
    async def process(self, query: str) -> PreprocessedQuery:
        """Process a query to extract and translate keywords.
        
        Args:
            query: Raw query string from user.
            
        Returns:
            PreprocessedQuery with original query and multilingual keywords.
        """
        if query in self._cache:
            return self._cache[query]
        
        keywords = self._extract_keywords(query)
        
        if not keywords:
            result = PreprocessedQuery(original=query)
            self._cache[query] = result
            return result
        
        chinese_keywords, english_keywords = await self._translate_keywords(keywords)
        
        all_keywords = self._merge_and_deduplicate(chinese_keywords, english_keywords)
        
        result = PreprocessedQuery(
            original=query,
            chinese_keywords=chinese_keywords,
            english_keywords=english_keywords,
            all_keywords=all_keywords,
        )
        
        self._cache[query] = result
        return result
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text using KeywordExtractor.
        
        Args:
            text: Input text to extract keywords from.
            
        Returns:
            List of extracted keywords.
        """
        return self.keyword_extractor.extract_keywords(text)
    
    async def _translate_keywords(self, keywords: list[str]) -> tuple[list[str], list[str]]:
        """Translate keywords between Chinese and English.
        
        Chinese keywords are translated to English.
        English keywords are translated to Chinese.
        Technical terms are preserved without translation.
        
        Args:
            keywords: List of keywords to translate.
            
        Returns:
            Tuple of (chinese_keywords, english_keywords).
        """
        chinese_keywords: list[str] = []
        english_keywords: list[str] = []
        
        for keyword in keywords:
            if self._is_technical_term(keyword):
                chinese_keywords.append(keyword)
                english_keywords.append(keyword)
                continue
            
            is_chinese = self._is_chinese(keyword)
            
            if is_chinese:
                chinese_keywords.append(keyword)
                if self.config and self.config.use_llm_translation:
                    translated = await self.translator.translate(
                        keyword, "中文", "英文"
                    )
                    english_keywords.append(translated)
            else:
                english_keywords.append(keyword)
                if self.config and self.config.use_llm_translation:
                    translated = await self.translator.translate(
                        keyword, "英文", "中文"
                    )
                    chinese_keywords.append(translated)
        
        return chinese_keywords, english_keywords
    
    def _merge_and_deduplicate(self, chinese: list[str], english: list[str]) -> list[str]:
        """Merge and deduplicate Chinese and English keywords.
        
        Args:
            chinese: List of Chinese keywords.
            english: List of English keywords.
            
        Returns:
            Deduplicated list of all keywords.
        """
        seen: set[str] = set()
        result: list[str] = []
        
        for keyword in chinese + english:
            lower = keyword.lower()
            if lower not in seen:
                seen.add(lower)
                result.append(keyword)
        
        return result
    
    def _is_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters.
        
        Args:
            text: Text to check.
            
        Returns:
            True if text contains at least one Chinese character.
        """
        return any('\u4e00' <= c <= '\u9fa5' for c in text)
    
    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term that should not be translated.
        
        Args:
            text: Text to check.
            
        Returns:
            True if text is a known technical term.
        """
        return text in self.TECHNICAL_TERMS or self.keyword_extractor._is_technical_term(text)