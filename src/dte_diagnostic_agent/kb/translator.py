"""Translation service for knowledge base queries."""

from langchain_openai import ChatOpenAI


class TranslatorService:
    """Translation service using LLM with caching support."""
    
    def __init__(self, llm: ChatOpenAI | None = None, cache_size: int = 100):
        self.llm = llm
        self.cache_size = cache_size
        self._cache: dict[str, str] = {}
    
    def _get_cache_key(self, source_lang: str, target_lang: str, text: str) -> str:
        return f"{source_lang}:{target_lang}:{text}"
    
    def _clear_cache_if_needed(self) -> None:
        if len(self._cache) >= self.cache_size:
            self._cache.clear()
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.llm:
            return text
        
        cache_key = self._get_cache_key(source_lang, target_lang, text)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        prompt = f"将以下{source_lang}关键词翻译为{target_lang}，只返回翻译结果\n\n{text}"
        
        response = await self.llm.ainvoke(prompt)
        result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        
        self._clear_cache_if_needed()
        self._cache[cache_key] = result
        
        return result