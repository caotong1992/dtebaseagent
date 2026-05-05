"""API Routes Module."""

from dte_diagnostic_agent.api.routes.diagnose import router as diagnose_router
from dte_diagnostic_agent.api.routes.cases import router as cases_router

__all__ = [
    "diagnose_router",
    "cases_router",
    "clusters_router",
    "health_router",
]