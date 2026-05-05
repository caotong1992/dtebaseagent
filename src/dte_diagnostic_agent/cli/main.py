"""CLI entry point for dte-diag diagnostic tool."""

import sys
from pathlib import Path
from typing import Any

import click

from dte_diagnostic_agent import __version__
from dte_diagnostic_agent.cli.config import ConfigManager, Config
from dte_diagnostic_agent.cli.output import OutputFormatter, OutputFormat
from dte_diagnostic_agent.cli.client import APIClient


class CLIContext:
    """CLI context holding global options and state."""

    config_manager: ConfigManager
    config: Config
    formatter: OutputFormatter
    client: APIClient
    verbose: bool
    quiet: bool
    no_color: bool

    def __init__(
        self,
        config_path: Path | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
        output_format: str = "table",
        verbose: bool = False,
        quiet: bool = False,
        no_color: bool = False,
    ):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()

        if api_url:
            self.config.api.url = api_url
        if api_key:
            self.config.api.key = api_key

        output_enum = OutputFormat(output_format.lower())
        self.formatter = OutputFormatter(format=output_enum, no_color=no_color)

        self.client = APIClient(
            base_url=self.config.api.url,
            api_key=self.config.api.key,
            timeout=self.config.api.timeout,
        )

        self.verbose = verbose
        self.quiet = quiet
        self.no_color = no_color

    def log_verbose(self, message: str) -> None:
        if self.verbose and not self.quiet:
            click.echo(f"[DEBUG] {message}")

    def log_info(self, message: str) -> None:
        if not self.quiet:
            click.echo(message)

    def log_error(self, message: str) -> None:
        click.echo(f"错误: {message}", err=True)


pass_ctx = click.make_pass_decorator(CLIContext, ensure=True)


@click.group(
    name="dte-diag",
    help="DTEBaseService 问题诊断工具",
    invoke_without_command=True,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False, path_type=Path),
    default=None,
    help="配置文件路径，默认 ~/.dte-diag/config.yaml",
)
@click.option(
    "--api-url",
    "-u",
    type=str,
    default=None,
    help="API服务地址，默认 http://localhost:8080",
)
@click.option(
    "--api-key",
    "-k",
    type=str,
    default=None,
    help="API认证密钥",
    envvar="DTE_DIAG_API_KEY",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml", "text", "markdown"], case_sensitive=False),
    default="table",
    help="输出格式: table/json/yaml/text/markdown",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="详细输出模式",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="静默模式，仅输出结果",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="禁用彩色输出",
)
@click.version_option(version=__version__, prog_name="dte-diag")
@click.pass_context
def main(
    ctx: click.Context,
    config: Path | None,
    api_url: str | None,
    api_key: str | None,
    output: str,
    verbose: bool,
    quiet: bool,
    no_color: bool,
) -> None:
    """DTEBaseService 问题诊断 CLI 工具."""
    ctx.obj = CLIContext(
        config_path=config,
        api_url=api_url,
        api_key=api_key,
        output_format=output,
        verbose=verbose,
        quiet=quiet,
        no_color=no_color,
    )

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command(name="diagnose", help="执行诊断")
@click.option("--description", "-d", required=True, help="问题描述")
@click.option("--cluster", "-C", required=True, help="集群名称")
@click.option("--node", "-n", default=None, help="目标节点IP")
@click.option("--node-user", default=None, help="节点登录用户")
@click.option("--node-port", default=22, type=int, help="SSH端口")
@click.option("--auth-type", type=click.Choice(["password", "key"]), default=None, help="认证类型")
@click.option("--password", default=None, help="登录密码")
@click.option("--ssh-key", default=None, type=click.Path(exists=False), help="SSH密钥路径")
@click.option("--service", "-s", default="DTEBaseService", help="服务名称")
@click.option("--namespace", "-N", default=None, help="K8s命名空间")
@click.option("--time-start", default=None, help="问题开始时间，ISO8601格式")
@click.option("--time-end", default=None, help="问题结束时间，ISO8601格式")
@click.option("--last", default=None, help="最近时间段，如: 1h, 30m, 2d")
@click.option("--priority", type=click.Choice(["critical", "high", "medium", "low"]), default="medium", help="优先级")
@click.option("--timeout", default=300, type=int, help="超时时间(秒)")
@click.option("--dry-run", is_flag=True, default=False, help="仅生成诊断计划不执行")
@click.option("--wait", "-w", is_flag=True, default=False, help="等待诊断完成并显示结果")
@click.option("--follow", "-f", is_flag=True, default=False, help="实时显示诊断进度")
@click.option("--interactive", "-i", is_flag=True, default=False, help="交互式输入模式")
@pass_ctx
def diagnose_cmd(
    ctx: CLIContext,
    description: str,
    cluster: str,
    node: str | None,
    node_user: str | None,
    node_port: int,
    auth_type: str | None,
    password: str | None,
    ssh_key: Path | None,
    service: str,
    namespace: str | None,
    time_start: str | None,
    time_end: str | None,
    last: str | None,
    priority: str,
    timeout: int,
    dry_run: bool,
    wait: bool,
    follow: bool,
    interactive: bool,
) -> None:
    """执行诊断."""
    ctx.log_verbose(f"提交诊断请求: 集群={cluster}, 描述={description}")

    from dte_diagnostic_agent.cli.commands.diagnose import diagnose
    diagnose(
        ctx=ctx,
        description=description,
        cluster=cluster,
        node=node,
        node_user=node_user,
        node_port=node_port,
        auth_type=auth_type,
        password=password,
        ssh_key=ssh_key,
        service=service,
        namespace=namespace,
        time_start=time_start,
        time_end=time_end,
        last=last,
        priority=priority,
        timeout=timeout,
        dry_run=dry_run,
        wait=wait,
        follow=follow,
        interactive=interactive,
    )


@main.command(name="status", help="查询诊断状态")
@click.argument("session_id", required=True)
@click.option("--format", "-F", type=click.Choice(["json", "markdown", "text"]), default=None, help="输出格式")
@click.option("--include-evidence", is_flag=True, default=False, help="包含收集的证据详情")
@click.option("--watch", is_flag=True, default=False, help="持续监控直到完成")
@pass_ctx
def status_cmd(
    ctx: CLIContext,
    session_id: str,
    format: str | None,
    include_evidence: bool,
    watch: bool,
) -> None:
    """查询诊断状态."""
    from dte_diagnostic_agent.cli.commands.status import status
    status(ctx=ctx, session_id=session_id, format=format, include_evidence=include_evidence, watch=watch)


@main.command(name="history", help="查看历史记录")
@click.option("--limit", "-l", default=20, type=int, help="返回数量")
@click.option("--status", "-s", type=click.Choice(["all", "pending", "running", "completed", "failed"]), default="all", help="状态筛选")
@click.option("--cluster", "-C", default=None, help="集群筛选")
@click.option("--date", default=None, help="日期筛选")
@click.option("--after", default=None, help="此日期之后的记录")
@click.option("--before", default=None, help="此日期之前的记录")
@pass_ctx
def history_cmd(
    ctx: CLIContext,
    limit: int,
    status: str,
    cluster: str | None,
    date: str | None,
    after: str | None,
    before: str | None,
) -> None:
    """查看历史记录."""
    from dte_diagnostic_agent.cli.commands.history import history
    history(ctx=ctx, limit=limit, status=status, cluster=cluster, date=date, after=after, before=before)


@main.command(name="cancel", help="取消诊断")
@click.argument("session_id", required=True)
@pass_ctx
def cancel_cmd(ctx: CLIContext, session_id: str) -> None:
    """取消诊断."""
    from dte_diagnostic_agent.cli.commands.cancel import cancel
    cancel(ctx=ctx, session_id=session_id)


@main.command(name="search", help="搜索案例库")
@click.option("--query", "-q", required=True, help="搜索关键词")
@click.option("--symptoms", "-s", default=None, help="症状筛选，逗号分隔")
@click.option("--category", "-c", default=None, help="问题类别筛选")
@click.option("--limit", "-l", default=10, type=int, help="返回数量")
@pass_ctx
def search_cmd(
    ctx: CLIContext,
    query: str,
    symptoms: str | None,
    category: str | None,
    limit: int,
) -> None:
    """搜索案例库."""
    from dte_diagnostic_agent.cli.commands.search import search
    search(ctx=ctx, query=query, symptoms=symptoms, category=category, limit=limit)


@main.group(name="case", help="案例管理")
def case_group() -> None:
    """案例管理命令组."""
    pass


@case_group.command(name="show", help="查看案例详情")
@click.argument("case_id", required=True)
@pass_ctx
def case_show_cmd(ctx: CLIContext, case_id: str) -> None:
    """查看案例详情."""
    from dte_diagnostic_agent.cli.commands.case import case_show
    case_show(ctx=ctx, case_id=case_id)


@case_group.command(name="save", help="从诊断结果保存案例")
@click.argument("session_id", required=True)
@click.option("--title", "-t", required=True, help="案例标题")
@click.option("--tags", default=None, help="标签，逗号分隔")
@pass_ctx
def case_save_cmd(ctx: CLIContext, session_id: str, title: str, tags: str | None) -> None:
    """从诊断结果保存案例."""
    from dte_diagnostic_agent.cli.commands.case import case_save
    case_save(ctx=ctx, session_id=session_id, title=title, tags=tags)


@case_group.command(name="list", help="列出所有案例")
@click.option("--limit", "-l", default=20, type=int, help="返回数量")
@pass_ctx
def case_list_cmd(ctx: CLIContext, limit: int) -> None:
    """列出所有案例."""
    from dte_diagnostic_agent.cli.commands.case import case_list
    case_list(ctx=ctx, limit=limit)


@main.group(name="cluster", help="集群管理")
def cluster_group() -> None:
    """集群管理命令组."""
    pass


@cluster_group.command(name="list", help="列出可用集群")
@pass_ctx
def cluster_list_cmd(ctx: CLIContext) -> None:
    """列出可用集群."""
    from dte_diagnostic_agent.cli.commands.cluster import cluster_list
    cluster_list(ctx=ctx)


@cluster_group.command(name="status", help="查看集群状态")
@click.argument("cluster_name", required=True)
@pass_ctx
def cluster_status_cmd(ctx: CLIContext, cluster_name: str) -> None:
    """查看集群状态."""
    from dte_diagnostic_agent.cli.commands.cluster import cluster_status
    cluster_status(ctx=ctx, cluster_name=cluster_name)


@cluster_group.command(name="test", help="测试集群连接")
@click.argument("cluster_name", required=True)
@click.option("--node", "-n", default=None, help="测试指定节点")
@pass_ctx
def cluster_test_cmd(ctx: CLIContext, cluster_name: str, node: str | None) -> None:
    """测试集群连接."""
    from dte_diagnostic_agent.cli.commands.cluster import cluster_test
    cluster_test(ctx=ctx, cluster_name=cluster_name, node=node)


@main.group(name="config", help="配置管理")
def config_group() -> None:
    """配置管理命令组."""
    pass


@config_group.command(name="show", help="查看当前配置")
@pass_ctx
def config_show_cmd(ctx: CLIContext) -> None:
    """查看当前配置."""
    from dte_diagnostic_agent.cli.commands.config_cmd import config_show
    config_show(ctx=ctx)


@config_group.command(name="set", help="设置配置项")
@click.argument("key", required=True)
@click.argument("value", required=True)
@pass_ctx
def config_set_cmd(ctx: CLIContext, key: str, value: str) -> None:
    """设置配置项."""
    from dte_diagnostic_agent.cli.commands.config_cmd import config_set
    config_set(ctx=ctx, key=key, value=value)


@config_group.command(name="init", help="初始化配置文件")
@click.option("--api-url", "-u", default=None, help="API服务地址")
@click.option("--api-key", "-k", default=None, help="API认证密钥")
@pass_ctx
def config_init_cmd(ctx: CLIContext, api_url: str | None, api_key: str | None) -> None:
    """初始化配置文件."""
    from dte_diagnostic_agent.cli.commands.config_cmd import config_init
    config_init(ctx=ctx, api_url=api_url, api_key=api_key)


main.add_command(case_group)
main.add_command(cluster_group)
main.add_command(config_group)


def cli_main() -> None:
    """CLI entry point."""
    try:
        main()
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()