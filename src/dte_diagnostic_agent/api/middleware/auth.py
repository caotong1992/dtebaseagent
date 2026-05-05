"""Authentication middleware for API."""

import os
import secrets
from typing import Callable

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

security = HTTPBearer(auto_error=False)

API_KEY_HEADER = "X-API-Key"
API_KEY_ENV_VAR = "DTE_DIAG_API_KEY"

_api_keys: set[str] = set()


def init_api_keys(keys: list[str] | None = None) -> None:
    """Initialize valid API keys.
    
    Args:
        keys: List of valid API keys. If None, reads from environment.
    """
    global _api_keys
    
    if keys:
        _api_keys = set(keys)
    else:
        env_key = os.environ.get(API_KEY_ENV_VAR)
        if env_key:
            _api_keys = {env_key}
        else:
            _api_keys = set()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"dte_diag_{secrets.token_urlsafe(32)}"


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    request: Request = None,
) -> str:
    """Verify API key from request.
    
    Checks both Authorization header (Bearer token) and X-API-Key header.
    
    Args:
        credentials: Bearer token credentials
        request: FastAPI request object
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If authentication fails
    """
    api_key = None
    
    if credentials:
        api_key = credentials.credentials
    elif request:
        api_key = request.headers.get(API_KEY_HEADER)
    
    if not _api_keys:
        return "anonymous"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via Authorization header (Bearer token) or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if api_key not in _api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests.
    
    This middleware performs API key validation for protected routes.
    Health and readiness endpoints are excluded from authentication.
    """
    
    PUBLIC_PATHS = {
        "/api/v1/health",
        "/api/v1/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
    }
    
    def __init__(self, app, api_keys: list[str] | None = None):
        """Initialize the auth middleware.
        
        Args:
            app: The ASGI application
            api_keys: Optional list of valid API keys
        """
        super().__init__(app)
        init_api_keys(api_keys)
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request through the middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response from the next handler or an error response
        """
        path = request.url.path
        
        if path in self.PUBLIC_PATHS or path.startswith("/api/v1/health"):
            return await call_next(request)
        
        if not _api_keys:
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get(API_KEY_HEADER)
        
        api_key = None
        
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
        elif api_key_header:
            api_key = api_key_header
        
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "authentication_required",
                    "message": "API key required. Provide via Authorization header (Bearer token) or X-API-Key header.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if api_key not in _api_keys:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_api_key",
                    "message": "Invalid API key",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        response = await call_next(request)
        return response