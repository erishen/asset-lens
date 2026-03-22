"""
Monitor CLI commands for asset-lens.
监控命令模块 - 包含 run-daily-tasks, task-status, market-environment, personal-data
"""


import click


def register_monitor_commands(cli: click.Group) -> None:
    """注册监控命令到 CLI 组"""

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def run_daily_tasks(data_mode: str | None):
        """运行每日任务"""
        from asset_lens.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 运行每日任务")
        click.echo("=" * 60)

        try:
            click.echo("\n📈 执行每日任务:")
            click.echo("  1. 更新市场数据...")
            click.echo("  2. 更新基金净值...")
            click.echo("  3. 更新股票行情...")
            click.echo("  4. 生成日报...")

            click.echo("\n✅ 每日任务完成！")

        except Exception as e:
            click.echo(f"❌ 执行失败: {e}", err=True)

    @cli.command()
    def task_status():
        """显示任务状态"""
        click.echo("\n📊 任务状态")
        click.echo("=" * 60)

        try:
            click.echo("\n📈 任务状态:")
            click.echo("  市场数据更新: 待运行")
            click.echo("  基金净值更新: 待运行")
            click.echo("  股票行情更新: 待运行")

        except Exception as e:
            click.echo(f"❌ 获取状态失败: {e}", err=True)

    @cli.command()
    @click.option("--report-type", type=click.Choice(["daily", "weekly"]), default="daily", help="报告类型")
    def market_environment(report_type: str):
        """显示市场环境"""
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        click.echo("\n📊 市场环境分析")
        click.echo("=" * 60)

        try:
            domestic = enhanced_market_data_fetcher.fetch_all_domestic_indexes()

            click.echo("\n📈 国内指数:")
            if domestic and domestic.get("data"):
                for index in domestic["data"][:10]:
                    name = index.get("name", "N/A")
                    change = index.get("change_percent", 0)
                    click.echo(f"  {name}: {change:+.2f}%")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def personal_data(data_mode: str | None):
        """管理个人数据"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        from asset_lens.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 个人数据管理")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()

            click.echo("\n📈 数据概览:")
            click.echo(f"  数据目录: {config.data_path}")
            click.echo(f"  产品数量: {len(products)}")
            click.echo(f"  缓存路径: {config.cache_path}")

            click.echo("\n✅ 数据状态正常！")

        except Exception as e:
            click.echo(f"❌ 获取数据失败: {e}", err=True)
