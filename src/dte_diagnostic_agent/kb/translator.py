"""Translation service for knowledge base queries."""

import logging
import time

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class TranslatorService:
    """Translation service using LLM with caching support."""
    
    def __init__(self, llm: ChatOpenAI | None = None, cache_size: int = 100):
        self.llm = llm
        self.cache_size = cache_size
        self._cache: dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_key(self, source_lang: str, target_lang: str, text: str) -> str:
        return f"{source_lang}:{target_lang}:{text}"
    
    def _clear_cache_if_needed(self, session_id: str = "") -> None:
        if len(self._cache) >= self.cache_size:
            self.logger.info(f"[{session_id}] [Translator] 缓存已满({self.cache_size}), 清空缓存")
            self._cache.clear()
    
    def _extract_token_info(self, response) -> str:
        """Extract token usage information from LLM response."""
        try:
            metadata = getattr(response, 'response_metadata', {}) or {}
            token_usage = metadata.get('token_usage', {})
            
            if token_usage:
                prompt_tokens = token_usage.get('prompt_tokens', 0)
                completion_tokens = token_usage.get('completion_tokens', 0)
                total_tokens = token_usage.get('total_tokens', 0)
                return f"prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
            
            usage = metadata.get('usage', {})
            if usage:
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                return f"prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
            
            return "N/A"
        except Exception:
            return "N/A"
    
    async def translate(self, text: str, source_lang: str, target_lang: str, session_id: str = "") -> str:
        if not self.llm:
            self.logger.info(f"[{session_id}] [Translator] LLM未配置, 返回原文: {text[:30]}")
            return text
        
        cache_key = self._get_cache_key(source_lang, target_lang, text)
        
        if cache_key in self._cache:
            self.logger.info(f"[{session_id}] [Translator] 缓存命中: {text[:30]} ({source_lang}->{target_lang})")
            return self._cache[cache_key]
        
        prompt = f"将以下{source_lang}关键词翻译为{target_lang}，只返回翻译结果\n\n{text}"
        
        text_preview = text[:50] + "..." if len(text) > 50 else text
        self.logger.info(f"[{session_id}] [Translator] LLM调用开始, 翻译: {text_preview} ({source_lang}->{target_lang})")
        self.logger.info(f"[{session_id}] [Translator] LLM调用输入(prompt): {prompt}")
        
        start_time = time.perf_counter()
        response = await self.llm.ainvoke(prompt)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        token_info = self._extract_token_info(response)
        result_preview = result[:50] + "..." if len(result) > 50 else result
        self.logger.info(f"[{session_id}] [Translator] LLM调用完成, 耗时: {elapsed_ms:.2f}ms, tokens: {token_info}")
        self.logger.info(f"[{session_id}] [Translator] LLM响应(翻译结果): {result_preview}")
        
        self._clear_cache_if_needed(session_id)
        self._cache[cache_key] = result
        
        return result