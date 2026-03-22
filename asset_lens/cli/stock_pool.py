"""
Stock Pool CLI commands for asset-lens.
股票池命令模块 - 包含 stock-pool, track-stocks, investment-status, investment-report
"""


import click


def register_stock_pool_commands(cli: click.Group) -> None:
    """注册股票池命令到 CLI 组"""

    @cli.command("stock-pool")
    @click.option("--action", type=click.Choice(["list", "add", "remove", "update", "clear"]), default="list", help="操作类型")
    @click.option("--code", type=str, help="股票代码")
    @click.option("--name", type=str, help="股票名称")
    @click.option("--force", is_flag=True, help="强制清空，无需确认")
    def stock_pool(action: str, code: str | None, name: str | None, force: bool):
        """管理股票池"""
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 股票池管理")
        click.echo("=" * 60)

        try:
            pool = StockPool()

            if action == "list":
                from rich.console import Console
                from rich.table import Table

                console = Console()
                stocks = pool.list_stocks()
                holding = [s for s in stocks if s.get('status') == 'holding']
                watching = [s for s in stocks if s.get('status') == 'watching']
                sold = [s for s in stocks if s.get('status') == 'sold']

                console.print(f"\n[bold cyan]📊 股票池总览[/bold cyan] ([cyan]{len(stocks)}[/cyan] 只股票)\n")

                if holding:
                    table = Table(title=f"📊 持仓股票 ({len(holding)} 只)", show_lines=False)
                    table.add_column("代码", style="cyan", width=10)
                    table.add_column("名称", style="white", width=12)
                    table.add_column("买入价", justify="right", style="yellow")
                    table.add_column("股数", justify="right", style="white")
                    table.add_column("金额", justify="right", style="green")
                    table.add_column("买入日期", style="dim")

                    total_amount = 0
                    for stock in holding:
                        code = stock.get('code', '')
                        name = stock.get('name', '')
                        buy_price = stock.get('buy_price', 0)
                        buy_date = stock.get('buy_date', '')
                        shares = stock.get('shares', 0)
                        amount = buy_price * shares
                        total_amount += amount

                        table.add_row(
                            code,
                            name,
                            f"¥{buy_price:.2f}",
                            str(shares),
                            f"¥{amount:,.2f}",
                            buy_date
                        )

                    console.print(table)
                    console.print(f"[bold green]持仓总金额: ¥{total_amount:,.2f}[/bold green]\n")

                if watching:
                    table = Table(title=f"👀 观察股票 ({len(watching)} 只)", show_lines=False)
                    table.add_column("代码", style="cyan", width=10)
                    table.add_column("名称", style="white", width=12)
                    table.add_column("入选次数", justify="center", style="yellow")
                    table.add_column("入选日期", style="dim")

                    for stock in watching[:15]:
                        code = stock.get('code', '')
                        name = stock.get('name', '')
                        count = stock.get('selected_count', 1)
                        first_date = stock.get('first_selected_date', '')

                        table.add_row(code, name, str(count), first_date)

                    if len(watching) > 15:
                        table.add_row("...", f"还有 {len(watching) - 15} 只", "", "")

                    console.print(table)

                if sold:
                    table = Table(title=f"💰 已卖出股票 ({len(sold)} 只)", show_lines=False)
                    table.add_column("代码", style="cyan", width=10)
                    table.add_column("名称", style="white", width=12)
                    table.add_column("收益率", justify="right")
                    table.add_column("卖出日期", style="dim")

                    total_profit = 0
                    for stock in sold[:10]:
                        code = stock.get('code', '')
                        name = stock.get('name', '')
                        buy_price = stock.get('buy_price', 0)
                        sell_price = stock.get('sell_price', 0)
                        profit_rate = ((sell_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                        sell_date = stock.get('sell_date', '')

                        profit_str = f"{profit_rate:+.2f}%"
                        if profit_rate > 0:
                            profit_str = f"[green]{profit_rate:+.2f}%[/green]"
                        elif profit_rate < 0:
                            profit_str = f"[red]{profit_rate:+.2f}%[/red]"

                        table.add_row(code, name, profit_str, sell_date)

                    if len(sold) > 10:
                        table.add_row("...", f"还有 {len(sold) - 10} 只", "", "")

                    console.print(table)

            elif action == "add":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.buy_stock(code=code, price=0.0)
                click.echo(f"✅ 已添加股票: {code}")

            elif action == "remove":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.remove_stock(code)
                click.echo(f"✅ 已移除股票: {code}")

            elif action == "update":
                pool.update_prices({})
                click.echo("✅ 股票池数据已更新")

            elif action == "clear":
                stocks = pool.list_stocks()
                if not stocks:
                    click.echo("⚠️ 股票池已为空")
                    return

                holding = [s for s in stocks if s.get('status') == 'holding']
                watching = [s for s in stocks if s.get('status') == 'watching']

                click.echo("\n当前股票池状态:")
                click.echo(f"  持仓股票: {len(holding)} 只")
                click.echo(f"  观察股票: {len(watching)} 只")
                click.echo(f"  总计: {len(stocks)} 只")

                if not force:
                    try:
                        confirm = click.confirm("\n⚠️ 确定要清空股票池吗？", default=False)
                        if not confirm:
                            click.echo("❌ 已取消操作")
                            return
                    except Exception:
                        click.echo("❌ 无法获取确认，请使用 --force 参数强制清空")
                        return

                count = pool.clear_pool()
                click.echo(f"✅ 已清空股票池 ({count} 只股票)")

        except Exception as e:
            import traceback
            click.echo(f"❌ 操作失败: {e}", err=True)
            click.echo(traceback.format_exc(), err=True)

    @cli.command()
    @click.option("--action", type=click.Choice(["list", "add", "remove"]), default="list", help="操作类型")
    @click.option("--code", type=str, help="股票代码")
    def track_stocks(action: str, code: str | None):
        """跟踪股票"""
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 股票跟踪")
        click.echo("=" * 60)

        try:
            pool = StockPool("tracked")

            if action == "list":
                stocks = pool.list_stocks()
                click.echo(f"\n跟踪股票 ({len(stocks)} 只):")
                for stock in stocks:
                    click.echo(f"  {stock.get('code')} - {stock.get('name')}")

            elif action == "add":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.buy_stock(code=code, price=0.0)
                click.echo(f"✅ 已开始跟踪: {code}")

            elif action == "remove":
                if not code:
                    click.echo("❌ 请提供股票代码", err=True)
                    return
                pool.remove_stock(code)
                click.echo(f"✅ 已停止跟踪: {code}")

        except Exception as e:
            click.echo(f"❌ 操作失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def investment_status(data_mode: str | None):
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
    def investment_report(data_mode: str | None):
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
