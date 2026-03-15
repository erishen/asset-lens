"""
Monitor CLI commands for asset-lens.
监控命令模块 - 包含 run-daily-tasks, task-status, market-environment, personal-data
"""

from typing import Optional

import click


def register_monitor_commands(cli: click.Group) -> None:
    """注册监控命令到 CLI 组"""
    
    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def run_daily_tasks(data_mode: Optional[str]):
        """运行每日任务"""
        from asset_lens.config import config
        from asset_lens.monitoring.daily_tasks import daily_task_runner

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 运行每日任务")
        click.echo("=" * 60)

        try:
            result = daily_task_runner.run_all()

            click.echo(f"\n📈 任务执行结果:")
            for task, status in result.items():
                status_icon = "✅" if status == "success" else "❌"
                click.echo(f"  {status_icon} {task}: {status}")

            click.echo(f"\n✅ 每日任务完成！")

        except Exception as e:
            click.echo(f"❌ 执行失败: {e}", err=True)

    @cli.command()
    def task_status():
        """显示任务状态"""
        from asset_lens.monitoring.task_status import task_status_checker

        click.echo("\n📊 任务状态")
        click.echo("=" * 60)

        try:
            status = task_status_checker.get_status()

            click.echo(f"\n📈 任务状态:")
            for task, info in status.items():
                click.echo(f"  {task}:")
                click.echo(f"    最后运行: {info.get('last_run', 'N/A')}")
                click.echo(f"    状态: {info.get('status', 'N/A')}")

        except Exception as e:
            click.echo(f"❌ 获取状态失败: {e}", err=True)

    @cli.command()
    @click.option("--report-type", type=click.Choice(["daily", "weekly"]), default="daily", help="报告类型")
    def market_environment(report_type: str):
        """显示市场环境"""
        from asset_lens.monitoring.market_environment import market_environment_analyzer

        click.echo("\n📊 市场环境分析")
        click.echo("=" * 60)

        try:
            result = market_environment_analyzer.analyze(report_type=report_type)

            click.echo(f"\n📈 市场环境:")
            click.echo(f"  整体评分: {result.get('score', 0):.2f}")
            click.echo(f"  市场情绪: {result.get('sentiment', 'N/A')}")

            if result.get("indexes"):
                click.echo(f"\n📊 指数表现:")
                for index, data in result["indexes"].items():
                    click.echo(f"  {index}: {data.get('change', 0):+.2f}%")

            click.echo(f"\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def personal_data(data_mode: Optional[str]):
        """管理个人数据"""
        from asset_lens.config import config
        from asset_lens.monitoring.personal_data import personal_data_manager

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 个人数据管理")
        click.echo("=" * 60)

        try:
            summary = personal_data_manager.get_summary()

            click.echo(f"\n📈 数据概览:")
            click.echo(f"  数据目录: {summary.get('data_dir', 'N/A')}")
            click.echo(f"  产品数量: {summary.get('products_count', 0)}")
            click.echo(f"  最后更新: {summary.get('last_update', 'N/A')}")

            click.echo(f"\n✅ 数据状态正常！")

        except Exception as e:
            click.echo(f"❌ 获取数据失败: {e}", err=True)
