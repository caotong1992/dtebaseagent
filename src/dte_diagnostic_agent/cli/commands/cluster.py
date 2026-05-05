"""Cluster command implementation."""

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx


def cluster_list(ctx: CLIContext) -> None:
    """List available clusters."""
    ctx.log_verbose("列出集群")

    try:
        result = ctx.client.get_clusters()
        clusters = result.get("clusters", [])

        ctx.log_info(f"共 {len(clusters)} 个集群")

        headers = ["name", "type", "status", "services"]
        ctx.formatter.print(clusters, headers=headers)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def cluster_status(ctx: CLIContext, cluster_name: str) -> None:
    """Show cluster status."""
    ctx.log_verbose(f"查看集群状态: {cluster_name}")

    try:
        result = ctx.client.get_cluster_status(cluster_name)
        ctx.formatter.print(result)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def cluster_test(ctx: CLIContext, cluster_name: str, node: str | None) -> None:
    """Test cluster connection."""
    ctx.log_verbose(f"测试集群连接: {cluster_name}, node={node}")

    try:
        result = ctx.client.test_cluster_connection(cluster_name, node=node)
        status = result.get("status", "unknown")

        if status == "success":
            ctx.formatter.print_success(f"集群 {cluster_name} 连接成功")
        else:
            ctx.formatter.print_error(f"集群 {cluster_name} 连接失败: {result.get('message', '')}")

        ctx.formatter.print(result)
    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()