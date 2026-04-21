"""
Scheduler CLI commands for asset-lens.
调度器命令
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def scheduler():
    """定时任务调度器命令"""
    pass


@scheduler.command()
def start():
    """启动调度器"""
    from asset_lens.scheduler.task_scheduler import register_default_tasks, task_scheduler

    if task_scheduler.is_running():
        console.print("[yellow]⚠️ 调度器已在运行[/yellow]")
        return

    register_default_tasks()
    task_scheduler.start()

    console.print("[bold green]✅ 调度器已启动[/bold green]")
    console.print("[dim]调度器将在后台运行，每小时检查任务[/dim]")


@scheduler.command()
def stop():
    """停止调度器"""
    from asset_lens.scheduler.task_scheduler import task_scheduler

    if not task_scheduler.is_running():
        console.print("[yellow]⚠️ 调度器未运行[/yellow]")
        return

    task_scheduler.stop()
    console.print("[bold green]✅ 调度器已停止[/bold green]")


@scheduler.command()
def status():
    """显示调度器状态"""
    from asset_lens.scheduler.task_scheduler import task_scheduler

    is_running = task_scheduler.is_running()

    console.print(Panel.fit(
        "[bold cyan]调度器状态[/bold cyan]",
        subtitle=f"{'🟢 运行中' if is_running else '🔴 已停止'}"
    ))

    tasks = task_scheduler.get_all_tasks()

    if not tasks:
        console.print("[yellow]暂无注册任务[/yellow]")
        return

    table = Table(title="任务列表")
    table.add_column("任务名", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("调度", style="yellow")
    table.add_column("上次运行", style="dim")
    table.add_column("下次运行", style="dim")
    table.add_column("成功率", style="white")

    for task in tasks:
        enabled = "✅ 启用" if task["enabled"] else "❌ 禁用"
        schedule = f"{task['schedule_type']}: {task['schedule_value']}"

        total = task["total_runs"]
        success = task["success_count"]
        success_rate = f"{success}/{total}" if total > 0 else "-"

        table.add_row(
            task["name"],
            enabled,
            schedule,
            task["last_run"] or "-",
            task["next_run"] or "-",
            success_rate,
        )

    console.print(table)


@scheduler.command()
@click.argument("task_name")
def run(task_name):
    """手动运行任务

    示例:
        asset-lens scheduler run risk_check
        asset-lens scheduler run update_data
    """
    from asset_lens.scheduler.task_scheduler import register_default_tasks, task_scheduler

    register_default_tasks()

    console.print(f"[bold blue]▶️ 运行任务: {task_name}[/bold blue]")

    result = task_scheduler.run_task(task_name)

    if result is None:
        console.print(f"[red]❌ 任务不存在: {task_name}[/red]")
        return

    if result.status.value == "completed":
        console.print("[green]✅ 任务完成[/green]")
        console.print(f"   耗时: {result.duration:.2f}s")
        if result.result:
            console.print(f"   结果: {result.result}")
    else:
        console.print(f"[red]❌ 任务失败: {result.error}[/red]")


@scheduler.command()
@click.argument("task_name")
def enable(task_name):
    """启用任务"""
    from asset_lens.scheduler.task_scheduler import task_scheduler

    if task_scheduler.enable_task(task_name):
        console.print(f"[green]✅ 已启用任务: {task_name}[/green]")
    else:
        console.print(f"[red]❌ 任务不存在: {task_name}[/red]")


@scheduler.command()
@click.argument("task_name")
def disable(task_name):
    """禁用任务"""
    from asset_lens.scheduler.task_scheduler import task_scheduler

    if task_scheduler.disable_task(task_name):
        console.print(f"[green]✅ 已禁用任务: {task_name}[/green]")
    else:
        console.print(f"[red]❌ 任务不存在: {task_name}[/red]")


@scheduler.command()
@click.argument("task_name")
@click.option("--limit", default=10, help="显示条数")
def history(task_name, limit):
    """显示任务执行历史

    示例:
        asset-lens scheduler history risk_check
        asset-lens scheduler history update_data --limit 20
    """
    from asset_lens.scheduler.task_scheduler import task_scheduler

    records = task_scheduler.get_task_history(task_name, limit)

    if not records:
        console.print(f"[yellow]任务 {task_name} 暂无执行历史[/yellow]")
        return

    console.print(f"[bold blue]📋 任务 {task_name} 执行历史[/bold blue]")

    table = Table()
    table.add_column("开始时间", style="dim")
    table.add_column("状态", style="green")
    table.add_column("耗时", style="yellow")
    table.add_column("重试", style="white")
    table.add_column("结果/错误", style="cyan")

    for record in records:
        status = record.get("status", "")
        status_display = {
            "completed": "✅ 成功",
            "failed": "❌ 失败",
            "running": "🔄 运行中",
        }.get(status, status)

        duration = f"{record.get('duration', 0):.2f}s"
        retry = str(record.get("retry_count", 0))
        result = record.get("result") or record.get("error") or "-"
        if len(result) > 50:
            result = result[:50] + "..."

        table.add_row(
            record.get("start_time", ""),
            status_display,
            duration,
            retry,
            result,
        )

    console.print(table)


@scheduler.command()
def list_tasks():
    """列出所有可用任务"""
    from asset_lens.scheduler.task_scheduler import register_default_tasks

    register_default_tasks()

    console.print("[bold blue]📋 可用任务列表[/bold blue]")

    tasks = [
        ("update_data", "每日更新股票数据", "每天 09:30"),
        ("risk_check", "每小时风险检查", "每小时"),
        ("backup", "每日备份", "每天 23:00"),
        ("daily_report", "每日报告", "每天 15:30"),
    ]

    table = Table()
    table.add_column("任务名", style="cyan")
    table.add_column("描述", style="white")
    table.add_column("默认调度", style="yellow")

    for name, desc, schedule in tasks:
        table.add_row(name, desc, schedule)

    console.print(table)


def register_scheduler_commands(cli: click.Group) -> None:
    """注册调度器命令到 CLI 组"""
    cli.add_command(scheduler)
