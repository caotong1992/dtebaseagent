"""Diagnose command implementation."""

import time
from datetime import datetime, timedelta
from pathlib import Path

import click

from dte_diagnostic_agent.cli.main import CLIContext, pass_ctx
from dte_diagnostic_agent.cli.client import DiagnoseRequest


def parse_duration(duration_str: str) -> tuple[datetime, datetime]:
    """Parse duration string like '1h', '30m', '2d'."""
    end = datetime.now()
    unit = duration_str[-1].lower()
    value = int(duration_str[:-1])
    match unit:
        case "h":
            start = end - timedelta(hours=value)
        case "m":
            start = end - timedelta(minutes=value)
        case "d":
            start = end - timedelta(days=value)
        case _:
            raise ValueError(f"无法解析时间格式: {duration_str}")
    return start, end


def diagnose(
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
    """Execute diagnostic."""
    if interactive:
        description = click.prompt("问题描述", type=str, default=description)
        cluster = click.prompt("集群名称", type=str, default=cluster or ctx.config.defaults.cluster or "")
        node = click.prompt("目标节点IP", type=str, default=node or "")
        service = click.prompt("服务名称", type=str, default=service)

    time_range = None
    if last:
        start, end = parse_duration(last)
        time_range = {"start": start.isoformat(), "end": end.isoformat()}
    elif time_start or time_end:
        time_range = {
            "start": time_start or (datetime.now() - timedelta(hours=1)).isoformat(),
            "end": time_end or datetime.now().isoformat(),
        }

    node_info = None
    if node:
        node_info = {
            "host": node,
            "port": node_port,
            "username": node_user,
            "auth_type": auth_type or "password",
        }
        if password:
            node_info["password"] = password
        if ssh_key:
            node_info["ssh_key_path"] = str(ssh_key)

    options = {"timeout": timeout, "dry_run": dry_run, "verbose": ctx.verbose}

    request = DiagnoseRequest(
        description=description,
        cluster_name=cluster,
        time_range=time_range,
        node_info=node_info,
        service_name=service,
        namespace=namespace,
        priority=priority,
        options=options,
    )

    ctx.log_verbose(f"发送诊断请求: {request.model_dump()}")

    try:
        response = ctx.client.submit_diagnose(request)
        ctx.log_info(f"诊断任务已创建: {response.session_id}")
        ctx.log_info(f"状态: {response.status}")
        ctx.log_info(f"预计耗时: {response.estimated_duration or '未知'}秒")

        if wait or follow:
            _wait_for_completion(ctx, response.session_id, follow, timeout)

    except Exception as e:
        ctx.log_error(str(e))
        raise click.Abort()


def _wait_for_completion(ctx: CLIContext, session_id: str, follow: bool, timeout: int) -> None:
    """Wait for diagnostic completion."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = ctx.client.get_diagnose_result(session_id)

        if follow:
            _display_progress(ctx, result)

        if result.status in ["completed", "failed"]:
            ctx.formatter.print(result.model_dump())
            if result.status == "completed":
                ctx.formatter.print_success("诊断完成")
            else:
                ctx.formatter.print_error("诊断失败")
            return

        time.sleep(5)

    ctx.formatter.print_warning(f"等待超时 ({timeout}秒)，诊断仍在进行中")
    ctx.log_info(f"使用 'dte-diag status {session_id}' 查看进度")


def _display_progress(ctx: CLIContext, result) -> None:
    """Display diagnostic progress."""
    if result.progress:
        current = result.progress.get("current_step", "未知")
        percentage = result.progress.get("percentage", 0)
        completed = result.progress.get("completed_steps", [])
        ctx.log_info(f"进度: {percentage}% - 当前步骤: {current}")
        if ctx.verbose and completed:
            ctx.log_verbose(f"已完成步骤: {completed}")