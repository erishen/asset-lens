"""
Analyze CLI commands for asset-lens.
分析命令模块 - 包含 analyze, calculate, pnl, estimate, analyze-sold, analyze-by-time, ai-analyze, portfolio-metrics, compare
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import click


def _get_data_dir(data_mode: str) -> Optional[Path]:
    """获取数据目录，处理 None 情况"""
    from asset_lens.config import config
    
    if data_mode == "real":
        return config.get_latest_data_dir()
    else:
        return config.project_root / "data" / "sample_data"


def register_analyze_commands(cli: click.Group) -> None:
    """注册分析命令到 CLI 组"""
    
    @cli.command()
    @click.option(
        "--data-mode",
        type=click.Choice(["sample", "real"]),
        help="数据模式 (sample=示例数据, real=真实数据)",
    )
    @click.option(
        "--output-format",
        type=click.Choice(["console", "csv", "json", "all"]),
        default="console",
        help="输出格式",
    )
    @click.option("--data-path", type=click.Path(exists=True), help="自定义数据路径")
    def analyze(data_mode: Optional[str], output_format: str, data_path: Optional[str]):
        """分析投资组合并生成报告"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
        from asset_lens.core.dca_parser import dca_parser
        from asset_lens.core.irr_calculator import irr_calculator
        from asset_lens.report.analyzer import report_generator
        
        if data_mode:
            config.data_mode = data_mode
            print(f"使用数据模式: {data_mode}")

        print("\n📊 正在加载数据...")
        try:
            if data_path:
                products = CSVParser.load_data(Path(data_path))
            else:
                products = CSVParser.load_data()
            print(f"✅ 成功加载 {len(products)} 个投资产品")
        except Exception as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort()

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        print("\n🔢 正在计算收益率...")
        reference_date = datetime.now()

        for product in portfolio.products:
            if product.transaction_records:
                transactions = dca_parser.parse_transaction_record(
                    product.transaction_records,
                    reference_date=reference_date,
                )
                product.transactions = transactions

                if transactions and product.current_amount:
                    irr = irr_calculator.calculate_annualized_irr(
                        transactions=transactions,
                        current_value=product.current_amount,
                        reference_date=reference_date,
                    )
                    product.annualized_return_irr = irr
            else:
                if product.initial_amount and product.current_amount and product.investment_days:
                    simple_return = irr_calculator.calculate_simple_annual_return(
                        initial_amount=product.initial_amount,
                        current_amount=product.current_amount,
                        days=product.investment_days,
                    )
                    product.annualized_return_irr = simple_return

        print("✅ 收益率计算完成")

        sell_records = []
        try:
            from asset_lens.data.sell_record_parser import SellRecordParser
            sell_records = SellRecordParser.load_sell_records()
            if sell_records:
                print(f"✅ 成功加载 {len(sell_records)} 条卖出记录")
        except Exception as e:
            print(f"⚠️  加载卖出记录失败: {e}")

        print("\n📝 正在生成分析报告...")
        report_data = report_generator.generate_analysis_report(portfolio, sell_records)

        report_data["products"] = [
            p.to_dict() for p in portfolio.products if p.annual_return is not None
        ]

        if output_format in ["console", "all"]:
            report_generator.print_console_report(report_data)

        if output_format in ["csv", "all"]:
            report_generator.save_csv_report(report_data, config.output_path)

        if output_format in ["json", "all"]:
            report_generator.save_json_report(report_data, config.output_path)

        print("\n✅ 分析完成!")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def calculate(data_mode: Optional[str]):
        """计算所有投资产品的收益率（快捷命令）"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
        from asset_lens.core.dca_parser import dca_parser
        from asset_lens.core.irr_calculator import irr_calculator
        from asset_lens.report.calculate_report import calculate_report_generator

        if data_mode:
            config.data_mode = data_mode
            print(f"使用数据模式: {data_mode}")

        print("\n📊 正在加载数据...")
        try:
            products = CSVParser.load_data()
            print(f"✅ 成功加载 {len(products)} 个投资产品")
        except Exception as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort()

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        print("\n🔢 正在计算收益率...")
        reference_date = datetime.now()

        for product in portfolio.products:
            if product.transaction_records:
                transactions = dca_parser.parse_transaction_record(
                    product.transaction_records,
                    reference_date=reference_date,
                )
                product.transactions = transactions

                if transactions and product.current_amount:
                    irr = irr_calculator.calculate_annualized_irr(
                        transactions=transactions,
                        current_value=product.current_amount,
                        reference_date=reference_date,
                    )
                    product.annualized_return_irr = irr
            else:
                if product.initial_amount and product.current_amount and product.investment_days:
                    simple_return = irr_calculator.calculate_simple_annual_return(
                        initial_amount=product.initial_amount,
                        current_amount=product.current_amount,
                        days=product.investment_days,
                    )
                    product.annualized_return_irr = simple_return

        print("✅ 收益率计算完成")

        print("\n📝 正在生成计算报告...")
        report = calculate_report_generator.generate_calculate_report(portfolio)
        calculate_report_generator.print_calculate_report(report)

        print("\n✅ 计算完成!")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--weekly", is_flag=True, help="周预估模式")
    def pnl(data_mode: Optional[str], weekly: bool):
        """估算实时盈亏（基于市场指数）"""
        from rich.console import Console
        from rich.table import Table
        from rich import box
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.realtime_pnl import RealtimePnlEstimator

        if data_mode:
            config.data_mode = data_mode

        click.echo(f"\n{'📊 周盈亏估算' if weekly else '📊 日盈亏估算'}")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            estimator = RealtimePnlEstimator()
            result = estimator.estimate_portfolio_pnl(products, is_weekly=weekly)

            if "error" in result:
                click.echo(f"❌ {result['error']}", err=True)
                click.echo("💡 提示: 请先更新市场指数数据缓存")
                return

            console = Console()

            click.echo(f"\n💰 总盈亏: ¥{result['total']:,.2f}")
            click.echo(f"📈 估算产品收益率: {result['total_return_rate']:.2f}%")
            click.echo(f"💵 估算产品金额: ¥{result['total_amount']:,.2f}")

            click.echo(f"\n📊 市场指数涨跌幅:")
            for index_key, move in result["moves"].items():
                click.echo(f"  {index_key}: {move:+.2f}%")

            if result["details"]:
                table = Table(title="\n产品盈亏明细", show_lines=False, expand=True, box=box.MINIMAL)
                table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", min_width=18)
                table.add_column("类型", style="green", no_wrap=True, overflow="ellipsis", min_width=8)
                table.add_column("金额", justify="right", style="yellow", min_width=8)
                table.add_column("盈亏", justify="right", min_width=8)
                table.add_column("收益率", justify="right", min_width=6)
                table.add_column("指数", style="blue", no_wrap=True, min_width=5)

                for detail in result["details"][:20]:
                    table.add_row(
                        detail["name"],
                        detail["type"],
                        f"¥{detail['amount']:,.0f}",
                        f"¥{detail['pnl']:,.0f}",
                        f"{detail['return_rate']:.2f}%",
                        detail["index_key"],
                    )

                console.print(table)

            click.echo(f"\n✅ 估算完成！")

        except Exception as e:
            click.echo(f"❌ 估算失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--weekly", is_flag=True, help="周预估模式")
    def estimate(data_mode: Optional[str], weekly: bool):
        """全产品收益估算（基于预期年化收益率）"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.daily_estimate import estimate_all_products
        from asset_lens.core.realtime_pnl import RealtimePnlEstimator

        if data_mode:
            config.data_mode = data_mode

        period_text = "周" if weekly else "日"
        click.echo(f"\n📊 全产品{period_text}收益估算")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            estimator = RealtimePnlEstimator()
            market_change = Decimal("0")

            try:
                moves = estimator.read_index_moves_from_cache(is_weekly=weekly)
                if moves:
                    total_change = Decimal("0")
                    count = 0
                    for key, value in moves.items():
                        total_change += Decimal(str(value))
                        count += 1
                    if count > 0:
                        market_change = total_change / count / Decimal("100")
            except Exception:
                pass

            results = estimate_all_products(products, market_change, is_weekly=weekly)

            if not results:
                click.echo("❌ 没有可估算的产品", err=True)
                return

            up_results = [r for r in results if r.estimated_daily_return >= 0]
            down_results = [r for r in results if r.estimated_daily_return < 0]

            up_results.sort(key=lambda x: x.estimated_daily_return, reverse=True)
            down_results.sort(key=lambda x: x.estimated_daily_return)

            console = Console()

            if up_results:
                click.echo(f"\n🟢 上涨产品 ({len(up_results)} 个):")
                table = Table(show_header=True, header_style="bold blue", expand=True)
                table.add_column("产品名称", style="cyan", no_wrap=True, min_width=20)
                table.add_column("类型", min_width=6)
                table.add_column("风险", min_width=4)
                table.add_column("市值", justify="right", min_width=10)
                table.add_column("预估收益", justify="right", min_width=8)
                table.add_column("收益率", justify="right", min_width=7)
                table.add_column("年化", justify="right", min_width=5)

                for result in up_results[:30]:
                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        f"¥{result.current_value:,.0f}",
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_daily_return_rate * 100:.2f}%",
                        f"{result.expected_annual_return * 100:.1f}%",
                    )

                console.print(table)

            if down_results:
                click.echo(f"\n🔴 下跌产品 ({len(down_results)} 个):")
                table = Table(show_header=True, header_style="bold blue", expand=True)
                table.add_column("产品名称", style="cyan", no_wrap=True, min_width=20)
                table.add_column("类型", min_width=6)
                table.add_column("风险", min_width=4)
                table.add_column("市值", justify="right", min_width=10)
                table.add_column("预估收益", justify="right", min_width=8)
                table.add_column("收益率", justify="right", min_width=7)
                table.add_column("年化", justify="right", min_width=5)

                for result in down_results[:30]:
                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        f"¥{result.current_value:,.0f}",
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_daily_return_rate * 100:.2f}%",
                        f"{result.expected_annual_return * 100:.1f}%",
                    )

                console.print(table)

            total_return = sum(r.estimated_daily_return for r in results)
            total_value = sum(r.current_value for r in results)
            avg_return_rate = total_return / total_value * 100 if total_value > 0 else 0

            click.echo(f"\n📊 汇总:")
            click.echo(f"  总预估收益: ¥{total_return:,.2f}")
            click.echo(f"  总市值: ¥{total_value:,.2f}")
            click.echo(f"  平均收益率: {avg_return_rate:.4f}%")
            click.echo(f"\n✅ 估算完成！")

        except Exception as e:
            click.echo(f"❌ 估算失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def analyze_sold(data_mode: Optional[str]):
        """分析已卖出投资"""
        from rich.console import Console
        from asset_lens.config import config
        from asset_lens.data.sell_record_parser import SellRecordParser
        from asset_lens.core.sold_investment import SoldInvestmentAnalyzer

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 已卖出投资分析")
        click.echo("=" * 60)

        try:
            data_dir = _get_data_dir(config.data_mode)
            if not data_dir:
                click.echo("❌ 数据目录不存在", err=True)
                return

            csv_file = data_dir / "卖出记录-表格 1.csv"

            if not csv_file.exists():
                click.echo(f"❌ 卖出记录文件不存在: {csv_file}", err=True)
                return

            sell_records = SellRecordParser.parse_csv_file(csv_file)
            click.echo(f"✅ 成功加载 {len(sell_records)} 条卖出记录")

            analyzer = SoldInvestmentAnalyzer()
            result = analyzer.analyze_sold_investments(sell_records)

            stats = result["stats"]
            click.echo(f"\n📈 总体统计:")
            click.echo(f"  总记录数: {stats.total_records}")
            click.echo(f"  总初始投资: ¥{stats.total_initial:,.2f}")
            click.echo(f"  总收益: ¥{stats.total_profit:,.2f}")
            click.echo(f"  总收益率: {stats.total_return_rate:.2f}%")
            click.echo(f"  正收益数量: {stats.positive_count}")
            click.echo(f"  负收益数量: {stats.negative_count}")
            click.echo(f"  平均持有天数: {stats.avg_holding_days:.1f}天")
            click.echo(f"  平均收益率: {stats.avg_return_rate:.2f}%")

            if result["details"]:
                console = Console(force_terminal=True)
                console.print("\n[bold cyan]📋 已卖出投资明细（前20条）：[/bold cyan]")
                console.print("[dim]─" * 50 + "[/dim]")
                for detail in result["details"][:20]:
                    profit_color = "green" if detail.profit_amount >= 0 else "red"
                    profit_sign = "+" if detail.profit_amount >= 0 else ""
                    console.print(f"[bold white]• {detail.name}[/bold white]")
                    console.print(
                        f"  [dim]日期:[/dim] [yellow]{detail.sell_date.strftime('%Y-%m-%d')}[/yellow] | [dim]收益:[/dim] [{profit_color}]¥{detail.profit_amount:,.0f} ({profit_sign}{detail.return_rate:.1f}%)[/{profit_color}] | [dim]年化:[/dim] [blue]{detail.annualized_return:.1f}%[/blue]"
                    )
                if len(result["details"]) > 20:
                    console.print(f"\n[dim]... 还有 {len(result['details']) - 20} 条记录未显示[/dim]")

            click.echo(f"\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def analyze_by_time(data_mode: Optional[str]):
        """按投资时间分组分析"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.time_group import TimeGroupAnalyzer

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 按投资时间分组分析")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            analyzer = TimeGroupAnalyzer()
            result = analyzer.analyze_by_holding_period(products)

            click.echo(f"\n📈 总体统计:")
            click.echo(f"  总产品数: {result['total_products']}")
            click.echo(f"  总金额: ¥{result['total_amount']:,.2f}")
            click.echo(f"  总初始投资: ¥{result['total_initial']:,.2f}")
            click.echo(f"  总收益: ¥{result['total_profit']:,.2f}")
            click.echo(f"  总收益率: {result['total_return_rate']:.2f}%")

            if result["groups"]:
                console = Console()
                table = Table(title="\n投资时间分组统计")
                table.add_column("分组", style="cyan", no_wrap=True)
                table.add_column("描述", style="green", no_wrap=True)
                table.add_column("产品数", justify="right")
                table.add_column("总金额", justify="right", style="yellow")
                table.add_column("总收益", justify="right")
                table.add_column("平均收益率", justify="right")
                table.add_column("平均持有天数", justify="right")

                for group in result["groups"]:
                    table.add_row(
                        group.group_name,
                        group.group_description,
                        str(group.products_count),
                        f"¥{group.total_amount:,.0f}",
                        f"¥{group.total_profit:,.2f}",
                        f"{group.avg_return_rate:.2f}%",
                        f"{group.avg_holding_days:.1f}天",
                    )

                console.print(table)

            click.echo(f"\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
