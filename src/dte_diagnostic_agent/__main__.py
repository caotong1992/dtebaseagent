"""Local deployment entry point for DTE Diagnostic Agent.

This module provides the entry point for running the diagnostic agent as a local service.
Supports command-line arguments for configuration and implements graceful shutdown.
"""

import argparse
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

import yaml

from pydantic import BaseModel, Field

from dte_diagnostic_agent import __version__
from dte_diagnostic_agent.api.main import create_app


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DEFAULT_WORKERS = 1
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CONFIG_PATH = Path.home() / ".dte-diag" / "config.yaml"
SYSTEM_CONFIG_PATH = Path("/etc/dte-diagnostic-agent/config.yaml")
SHUTDOWN_TIMEOUT = 30


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    workers: int = DEFAULT_WORKERS


class LLMConfig(BaseModel):
    """LLM configuration."""

    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_iterations: int = 15


class StorageConfig(BaseModel):
    """Storage configuration."""

    session_dir: str = "/var/lib/dte-diagnostic-agent/sessions"
    case_dir: str = "/var/lib/dte-diagnostic-agent/cases"
    log_dir: str = "/var/log/dte-diagnostic-agent"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = DEFAULT_LOG_LEVEL
    file: str | None = None
    max_size: str = "10MB"
    backup_count: int = 5


class AuthConfig(BaseModel):
    """Authentication configuration."""

    api_keys: list[str] = Field(default_factory=list)
    env_key: str = "DTE_DIAG_API_KEY"


class ClusterConfig(BaseModel):
    """Cluster connection configuration."""

    kubeconfig: str | None = None
    ssh_key: str | None = None


class AppConfig(BaseModel):
    """Application configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    clusters: dict[str, ClusterConfig] = Field(default_factory=dict)
    knowledge_base: dict[str, Any] = Field(default_factory=dict)


class GracefulShutdownManager:
    """Manages graceful shutdown of the service."""

    def __init__(self, timeout: int = SHUTDOWN_TIMEOUT):
        self.timeout = timeout
        self._shutdown_requested = False
        self._app_state: dict[str, Any] = {}

    def request_shutdown(self) -> None:
        """Request a graceful shutdown."""
        self._shutdown_requested = True

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested

    def save_state(self, key: str, value: Any) -> None:
        """Save application state for cleanup."""
        self._app_state[key] = value

    def get_state(self, key: str) -> Any | None:
        """Get saved application state."""
        return self._app_state.get(key)

    async def wait_for_completion(self) -> None:
        """Wait for existing requests to complete."""
        import asyncio

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < self.timeout:
            if self._can_safely_exit():
                return
            await asyncio.sleep(0.1)

    def _can_safely_exit(self) -> bool:
        """Check if it's safe to exit."""
        return True


shutdown_manager = GracefulShutdownManager()


def find_config_file(config_path: Path | None = None) -> Path | None:
    """Find configuration file with priority order.

    Priority:
    1. Command-line specified path
    2. /etc/dte-diagnostic-agent/config.yaml
    3. ~/.dte-diag/config.yaml

    Args:
        config_path: Optional command-line specified config path

    Returns:
        Path to the config file, or None if not found
    """
    if config_path:
        if config_path.exists():
            return config_path
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if SYSTEM_CONFIG_PATH.exists():
        return SYSTEM_CONFIG_PATH

    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH

    return None


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from file.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file is specified but not found
        yaml.YAMLError: If config file is invalid YAML
    """
    found_path = find_config_file(config_path)

    if found_path:
        with open(found_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = AppConfig(**data)
    else:
        config = AppConfig()

    return config


def setup_logging(log_level: str, log_file: str | None = None) -> None:
    """Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=handlers,
    )


def merge_cli_args_with_config(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    """Merge CLI arguments with configuration.

    CLI arguments take precedence over config file values.

    Args:
        config: Configuration loaded from file
        args: Parsed command-line arguments

    Returns:
        Merged configuration
    """
    if args.host is not None:
        config.server.host = args.host
    if args.port is not None:
        config.server.port = args.port
    if args.workers is not None:
        config.server.workers = args.workers
    if args.api_key is not None:
        config.auth.api_keys = [args.api_key]
    if args.log_level is not None:
        config.logging.level = args.log_level
    if args.log_file is not None:
        config.logging.file = args.log_file

    return config


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="dte_diagnostic_agent",
        description="DTEBaseService Diagnostic Agent - Local deployment mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m dte_diagnostic_agent                    # Start with default config
  python -m dte_diagnostic_agent --port 9000       # Start on port 9000
  python -m dte_diagnostic_agent --config ./config.yaml  # Use specific config
  python -m dte_diagnostic_agent --dry-run         # Validate config only
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help=f"Configuration file path (default: {DEFAULT_CONFIG_PATH})",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=None,
        help=f"Service listening port (default: {DEFAULT_PORT})",
    )

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"Service listening address (default: {DEFAULT_HOST})",
    )

    parser.add_argument(
        "--api-key",
        "-k",
        type=str,
        default=None,
        help="API authentication key (overrides config file)",
    )

    parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help=f"Logging level (default: {DEFAULT_LOG_LEVEL})",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log file path",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help=f"Number of worker processes (default: {DEFAULT_WORKERS})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without starting the service",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args()


def validate_config(config: AppConfig) -> list[str]:
    """Validate configuration.

    Args:
        config: Configuration to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if config.server.port < 1 or config.server.port > 65535:
        errors.append(f"Invalid port number: {config.server.port}")

    if config.server.workers < 1:
        errors.append(f"Invalid workers count: {config.server.workers}")

    if config.logging.level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        errors.append(f"Invalid log level: {config.logging.level}")

    if config.llm.api_key is None and not config.auth.api_keys:
        env_key = os.environ.get(config.auth.env_key)
        if not env_key:
            pass

    return errors


def create_signal_handlers(logger: logging.Logger) -> None:
    """Create signal handlers for graceful shutdown.

    Args:
        logger: Logger instance
    """

    def handle_shutdown(signum: int, frame: Any) -> None:
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        shutdown_manager.request_shutdown()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)


async def run_server(config: AppConfig, logger: logging.Logger) -> None:
    """Run the server with the given configuration.

    Args:
        config: Application configuration
        logger: Logger instance
    """
    import uvicorn
    from uvicorn import Config, Server

    api_keys = config.auth.api_keys or None
    session_dir = config.storage.session_dir
    
    app = create_app(
        api_keys=api_keys,
        session_dir=session_dir,
        config=config,
        logger=logger
    )

    server_config = Config(
        app=app,
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers,
        log_level=config.logging.level.lower(),
    )

    server = Server(server_config)

    create_signal_handlers(logger)

    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def main() -> int:
    """Main entry point for local deployment.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file: {e}", file=sys.stderr)
        return 1

    config = merge_cli_args_with_config(config, args)

    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"Configuration error: {error}", file=sys.stderr)
        return 1

    setup_logging(config.logging.level, config.logging.file)
    logger = logging.getLogger(__name__)

    logger.info(f"DTE Diagnostic Agent v{__version__}")
    logger.info(f"Configuration loaded from: {args.config or 'defaults'}")

    if args.dry_run:
        logger.info("Dry-run mode: Configuration validated successfully")
        print("Configuration validated successfully")
        return 0

    create_signal_handlers(logger)

    logger.info(f"Starting server on {config.server.host}:{config.server.port}")
    logger.info(f"Workers: {config.server.workers}")
    logger.info(f"Log level: {config.logging.level}")

    import asyncio

    try:
        asyncio.run(run_server(config, logger))
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())