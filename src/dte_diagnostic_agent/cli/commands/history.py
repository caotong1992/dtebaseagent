"""History command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def history(
    ctx: CLIContext,
    limit: int,
    status: str,
    cluster: str | None,
    date: str | None,
    after: str | None,
    before: str | None,
) -> None:
    """View diagnostic history."""
    ctx.log_verbose(f"查询历史记录: limit={limit}, status={status}")

    try:
        result = ctx.client.list_diagnoses(
            limit=limit,
            status=status if status != "all" else None,
            cluster=cluster,
            start_date=after or date,
            end_date=before,
        )

        items = result.get("items", [])
        total = result.get("total", 0)

        ctx.log_info(f"共 {total} 条记录")

        headers = ["session_id", "status", "cluster_name", "description", "created_at", "completed_at"]
        ctx.formatter.print(items, headers=headers)

    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()