"""Search command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def search(
    ctx: CLIContext,
    query: str,
    symptoms: str | None,
    category: str | None,
    limit: int,
) -> None:
    """Search case library."""
    ctx.log_verbose(f"搜索案例: query={query}, symptoms={symptoms}, category={category}")

    try:
        result = ctx.client.search_cases(
            query=query,
            symptoms=symptoms,
            category=category,
            limit=limit,
        )

        ctx.log_info(f"找到 {result.total} 条匹配案例")

        headers = ["case_id", "title", "problem", "similarity", "created_at"]
        ctx.formatter.print(result.items, headers=headers)

    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()