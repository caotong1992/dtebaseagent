"""Status command implementation."""

import time

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx
from dte_diagnostic_agent.cli.output import OutputFormat


def status(
    ctx: CLIContext,
    session_id: str,
    format: str | None,
    include_evidence: bool,
    watch: bool,
) -> None:
    """Query diagnostic status."""
    if format:
        output_format = OutputFormat(format.lower())
        ctx.formatter = ctx.formatter.__class__(format=output_format, no_color=ctx.no_color)

    ctx.log_verbose(f"查询诊断状态: {session_id}")

    try:
        if watch:
            _watch_status(ctx, session_id, include_evidence)
        else:
            result = ctx.client.get_diagnose_result(session_id, include_evidence=include_evidence)
            headers = ["session_id", "status", "summary", "problem_category", "severity"]
            ctx.formatter.print(result.model_dump(), headers=headers)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def _watch_status(ctx: CLIContext, session_id: str, include_evidence: bool) -> None:
    """Watch diagnostic status until completion."""
    while True:
        result = ctx.client.get_diagnose_result(session_id, include_evidence=include_evidence)

        ctx.log_info(f"状态: {result.status}")
        if result.progress:
            current = result.progress.get("current_step", "未知")
            percentage = result.progress.get("percentage", 0)
            ctx.log_info(f"进度: {percentage}% - {current}")

        if result.status in ["completed", "failed"]:
            ctx.formatter.print(result.model_dump())
            if result.status == "completed":
                ctx.formatter.print_success("诊断完成")
            else:
                ctx.formatter.print_error("诊断失败")
            break

        time.sleep(3)