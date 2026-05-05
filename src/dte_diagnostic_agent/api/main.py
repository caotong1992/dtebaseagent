"""FastAPI application entry point for DTE Diagnostic Agent."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dte_diagnostic_agent.api.routes import (
    diagnose_router,
    cases_router,
)
from dte_diagnostic_agent.api.middleware.auth import AuthMiddleware
from dte_diagnostic_agent.api.routes.diagnose import (
    set_session_store,
    set_llm_config,
    set_kb_config,
    LLMConfig,
)
from dte_diagnostic_agent.storage.session_store import SessionStore
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig, LocalKBConfig, RemoteKBConfig

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

_APP_TITLE = "DTE Diagnostic Agent API"
_APP_DESCRIPTION = """
DTEBaseService Problem Diagnosis AI Agent API

This API provides intelligent diagnostic capabilities for DTEBaseService 
infrastructure issues. It supports:

- **Diagnostic Sessions**: Submit, track, and cancel diagnostic requests
- **Case Management**: Search and manage historical diagnostic cases
- **Cluster Management**: Monitor and manage cluster status
- **Health Checks**: Service health and readiness endpoints

## Authentication

Most endpoints require API key authentication. Provide your API key via:
- `Authorization: Bearer <api_key>` header
- `X-API-Key: <api_key>` header

Health endpoints are public and do not require authentication.
"""
_APP_VERSION = "0.1.0"

_session_store: SessionStore | None = None
_app_config: "AppConfig | None" = None  # type: ignore
_logger: logging.Logger | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    logger = _logger or logging.getLogger(__name__)
    config = _app_config
    
    logger.info(f"Starting {_APP_TITLE} v{_APP_VERSION}")
    
    if config:
        logger.info(f"Server listening on {config.server.host}:{config.server.port}")
        logger.info(f"API keys configured: {'Yes' if config.auth.api_keys else 'No'}")
        logger.info(f"Session storage directory: {config.storage.session_dir}")
        logger.info(f"LLM base_url: {config.llm.base_url}")
        logger.info(f"LLM model_name: {config.llm.model_name}")
        logger.info(f"LLM temperature: {config.llm.temperature}")
        if config.knowledge_base:
            logger.info(f"Knowledge base mode: {config.knowledge_base.get('mode', 'local')}")
    
    yield
    
    logger.info(f"Shutting down {_APP_TITLE}")


def create_app(
    api_keys: list[str] | None = None,
    session_dir: str = "./data/sessions",
    config: "AppConfig | None" = None,
    logger: logging.Logger | None = None
) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Args:
        api_keys: Optional list of valid API keys for authentication.
        session_dir: Directory path for storing diagnostic session CSV files.
        config: Optional application configuration containing LLM and KB settings.
        logger: Optional logger instance for lifespan events.
        
    Returns:
        Configured FastAPI application instance.
    """
    global _session_store, _app_config, _logger
    
    _session_store = SessionStore(session_dir)
    set_session_store(_session_store)
    
    if config:
        _app_config = config
    
    if logger:
        _logger = logger
    
    if config:
        llm_config = LLMConfig(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            model_name=config.llm.model_name,
            temperature=config.llm.temperature
        )
        set_llm_config(llm_config)
        
        if hasattr(config, 'knowledge_base') and config.knowledge_base:
            kb_config = KnowledgeBaseConfig(
                mode=config.knowledge_base.get("mode", "local"),
                local=LocalKBConfig(
                    case_dir=config.knowledge_base.get("local", {}).get("case_dir", "./cases")
                )
            )
            if config.knowledge_base.get("mode") == "remote" and config.knowledge_base.get("remote"):
                remote_cfg = config.knowledge_base["remote"]
                kb_config.remote = RemoteKBConfig(
                    api_url=remote_cfg.get("api_url", ""),
                    api_key=remote_cfg.get("api_key"),
                    timeout=remote_cfg.get("timeout", 30)
                )
            set_kb_config(kb_config)
    
    app = FastAPI(
        title=_APP_TITLE,
        description=_APP_DESCRIPTION,
        version=_APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(AuthMiddleware, api_keys=api_keys)
    
    app.include_router(diagnose_router, prefix=API_PREFIX)
    app.include_router(cases_router, prefix=API_PREFIX)
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint returning API information."""
        return {
            "name": _APP_TITLE,
            "version": _APP_VERSION,
            "docs": "/docs",
            "api_prefix": API_PREFIX,
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "dte_diagnostic_agent.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )