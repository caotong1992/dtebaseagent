"""Keyword extractor for query preprocessing."""

import re


class KeywordExtractor:
    """Extract keywords from text for knowledge base search."""

    TECHNICAL_TERM_PATTERN = re.compile(r'[A-Z][a-zA-Z0-9]*[A-Z0-9]|[A-Z]{2,}[a-z]*')
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fa5]+')
    ENGLISH_WORD_PATTERN = re.compile(r'[a-z]+')

    def extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text.
        
        Args:
            text: Input text to extract keywords from.
            
        Returns:
            List of extracted keywords including technical terms,
            Chinese phrases, and English words.
        """
        if not text:
            return []

        technical_terms = self.TECHNICAL_TERM_PATTERN.findall(text)
        chinese_parts = self.CHINESE_PATTERN.findall(text)
        english_words = self.ENGLISH_WORD_PATTERN.findall(text.lower())

        return technical_terms + chinese_parts + english_words

    def _is_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters.
        
        Args:
            text: Text to check.
            
        Returns:
            True if text contains at least one Chinese character.
        """
        return any('\u4e00' <= c <= '\u9fa5' for c in text)

    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term.
        
        Technical terms are words with mixed case patterns like:
        - DTEBaseService (PascalCase)
        - PostgreSQL (Mixed case)
        - API (All caps)
        
        Args:
            text: Text to check.
            
        Returns:
            True if text matches technical term pattern.
        """
        return bool(self.TECHNICAL_TERM_PATTERN.match(text))