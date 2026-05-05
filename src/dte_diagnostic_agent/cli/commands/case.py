"""Case command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def case_show(ctx: CLIContext, case_id: str) -> None:
    """Show case details."""
    ctx.log_verbose(f"查看案例详情: {case_id}")

    try:
        result = ctx.client.get_case(case_id)
        headers = ["case_id", "title", "problem", "solution"]
        ctx.formatter.print(result, headers=headers)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def case_save(ctx: CLIContext, session_id: str, title: str, tags: str | None) -> None:
    """Save case from diagnostic result."""
    ctx.log_verbose(f"保存案例: session={session_id}, title={title}")

    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    try:
        result = ctx.client.create_case(session_id=session_id, title=title, tags=tag_list)
        ctx.formatter.print_success(f"案例已保存: {result.get('case_id')}")
        ctx.formatter.print(result)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def case_list(ctx: CLIContext, limit: int) -> None:
    """List all cases."""
    ctx.log_verbose(f"列出案例: limit={limit}")

    try:
        result = ctx.client.list_cases(limit=limit)
        items = result.get("items", [])
        total = result.get("total", 0)

        ctx.log_info(f"共 {total} 条案例")

        headers = ["case_id", "title", "problem", "created_at"]
        ctx.formatter.print(items, headers=headers)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()