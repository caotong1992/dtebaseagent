"""Knowledge base module for case management."""

from dte_diagnostic_agent.kb.interface import KnowledgeBaseInterface
from dte_diagnostic_agent.kb.models import Case, SearchResult
from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig, LocalKBConfig, RemoteKBConfig

__all__ = [
    "KnowledgeBaseInterface",
    "Case",
    "SearchResult",
    "KnowledgeBaseManager",
    "KnowledgeBaseConfig",
    "LocalKBConfig",
    "RemoteKBConfig",
]