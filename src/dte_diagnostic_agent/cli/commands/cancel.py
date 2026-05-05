"""Cancel command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def cancel(ctx: CLIContext, session_id: str) -> None:
    """Cancel diagnostic."""
    ctx.log_verbose(f"取消诊断: {session_id}")

    try:
        result = ctx.client.cancel_diagnose(session_id)
        ctx.formatter.print_success(f"诊断已取消: {session_id}")
        ctx.formatter.print(result)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()