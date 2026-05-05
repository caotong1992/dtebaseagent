"""CLI commands module."""

from dte_diagnostic_agent.cli.commands.diagnose import diagnose
from dte_diagnostic_agent.cli.commands.status import status
from dte_diagnostic_agent.cli.commands.history import history
from dte_diagnostic_agent.cli.commands.cancel import cancel
from dte_diagnostic_agent.cli.commands.search import search
from dte_diagnostic_agent.cli.commands.case import case
from dte_diagnostic_agent.cli.commands.cluster import cluster
from dte_diagnostic_agent.cli.commands.config_cmd import config_cmd

__all__ = [
    "diagnose",
    "status",
    "history",
    "cancel",
    "search",
    "case",
    "cluster",
    "config_cmd",
]