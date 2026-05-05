"""Config command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def config_show(ctx: CLIContext) -> None:
    """Show current configuration."""
    ctx.log_verbose("显示配置")

    config = ctx.config_manager.load()
    ctx.log_info(f"配置文件路径: {ctx.config_manager.config_path}")
    ctx.formatter.print(config.model_dump())


def config_set(ctx: CLIContext, key: str, value: str) -> None:
    """Set configuration value."""
    ctx.log_verbose(f"设置配置: {key}={value}")

    try:
        ctx.config_manager.set(key, value)
        ctx.formatter.print_success(f"配置已更新: {key}={value}")
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def config_init(ctx: CLIContext, api_url: str | None, api_key: str | None) -> None:
    """Initialize configuration file."""
    ctx.log_verbose("初始化配置")

    ctx.config_manager.init_config(api_url=api_url, api_key=api_key)
    ctx.formatter.print_success(f"配置文件已创建: {ctx.config_manager.config_path}")

    if api_url:
        ctx.log_info(f"API地址: {api_url}")
    if api_key:
        ctx.log_info("API密钥已设置")