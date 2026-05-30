"""Diagnostic tools module."""

from dte_diagnostic_agent.tools.ssh import SSHConnectTool
from dte_diagnostic_agent.tools.log import LogAnalysisTool
from dte_diagnostic_agent.tools.database import DatabaseQueryTool
from dte_diagnostic_agent.tools.resource import ResourceMonitorTool
from dte_diagnostic_agent.tools.k8s import K8sOperationTool
from dte_diagnostic_agent.tools.config import ConfigCheckTool
from dte_diagnostic_agent.tools.network import NetworkDiagTool
from dte_diagnostic_agent.tools.case import create_case_search_tool, MockCaseSearchTool
from dte_diagnostic_agent.tools.registry import (
    ToolMetadata,
    ParameterInfo,
    extract_parameters_from_tool,
    format_tool_metadata,
    generate_tool_docs_string
)

__all__ = [
    "SSHConnectTool",
    "LogAnalysisTool",
    "DatabaseQueryTool",
    "ResourceMonitorTool",
    "K8sOperationTool",
    "ConfigCheckTool",
    "NetworkDiagTool",
    "MockCaseSearchTool",
    "create_case_search_tool",
    "ToolMetadata",
    "ParameterInfo",
    "extract_parameters_from_tool",
    "format_tool_metadata",
    "generate_tool_docs_string",
]

STATIC_TOOLS = {
    "ssh_connect": SSHConnectTool,
    "log_analysis": LogAnalysisTool,
    "resource_monitor": ResourceMonitorTool,
    "database_query": DatabaseQueryTool,
    "network_diag": NetworkDiagTool,
    "k8s_operation": K8sOperationTool,
    "config_check": ConfigCheckTool,
}