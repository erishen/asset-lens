"""
Stock Pool CLI commands for asset-lens.
股票池命令模块 - 包含 stock-pool, track-stocks, investment-status, investment-report
"""

from typing import Optional

import click


def register_stock_pool_commands(cli: click.Group) -> None:
    """注册股票池命令到 CLI 组"""
    
    @cli.command("stock-pool")
    @click.option("--action", type=click.Choice(["list", "add", "remove", "update"]), default="list", help="操作类型")
    @click.option("--code", type=str, help="股票代码")
    @click.option("--name", type=str, help="股票名称")
    def stock_pool(action: str, code: Optional[str], name: Optional[str]):
        """管理股票池"""
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 股票池管理")
        click.echo("=" * 60)

        try:
            pool = StockPool()
            
            if action == "list":
                positions = pool.list_positions()
                click.echo(f"\n股票池 ({len(positions)} 只股票):")
                for pos in positions:
                    click.echo(f"  {pos.code} - {pos.name}")

            elif action == "add":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.add_position(code=code, name=name or "")
                click.echo(f"✅ 已添加股票: {code}")

            elif action == "remove":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.remove_position(code)
                click.echo(f"✅ 已移除股票: {code}")

            elif action == "update":
                pool.update_prices()
                click.echo("✅ 股票池数据已更新")

        except Exception as e:
            click.echo(f"❌ 操作失败: {e}", err=True)

    @cli.command()
    @click.option("--action", type=click.Choice(["list", "add", "remove"]), default="list", help="操作类型")
    @click.option("--code", type=str, help="股票代码")
    def track_stocks(action: str, code: Optional[str]):
        """跟踪股票"""
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 股票跟踪")
        click.echo("=" * 60)

        try:
            pool = StockPool("tracked")
            
            if action == "list":
                positions = pool.list_positions()
                click.echo(f"\n跟踪股票 ({len(positions)} 只):")
                for pos in positions:
                    click.echo(f"  {pos.code} - {pos.name}")

            elif action == "add":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.add_position(code=code, name="")
                click.echo(f"✅ 已开始跟踪: {code}")

            elif action == "remove":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.remove_position(code)
                click.echo(f"✅ 已停止跟踪: {code}")

        except Exception as e:
            click.echo(f"❌ 操作失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def investment_status(data_mode: Optional[str]):
        """显示投资状态"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 投资状态")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            total_value = sum(p.current_amount or 0 for p in products)
            click.echo(f"\n总资产: ¥{total_value:,.2f}")
            click.echo(f"产品数: {len(products)}")

        except Exception as e:
            click.echo(f"❌ 加载失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def investment_report(data_mode: Optional[str]):
        """生成投资报告"""
        from asset_lens.config import config
        from asset_lens.report.investment_report import investment_report_generator

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 生成投资报告")
        click.echo("=" * 60)

        try:
            report_path = investment_report_generator.generate_pool_report()
            click.echo(f"\n✅ 报告已生成: {report_path}")

        except Exception as e:
            click.echo(f"❌ 生成失败: {e}", err=True)
