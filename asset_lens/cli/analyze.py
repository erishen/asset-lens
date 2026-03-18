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
            click.echo(f"使用数据模式: {data_mode}")

        click.echo("\n📊 正在加载数据...")
        try:
            if data_path:
                products = CSVParser.load_data(Path(data_path))
            else:
                products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")
        except Exception as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort()

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        click.echo("\n🔢 正在计算收益率...")
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

        click.echo("✅ 收益率计算完成")

        sell_records = []
        try:
            from asset_lens.data.sell_record_parser import SellRecordParser
            sell_records = SellRecordParser.load_sell_records()
            if sell_records:
                click.echo(f"✅ 成功加载 {len(sell_records)} 条卖出记录")
        except Exception as e:
            click.echo(f"⚠️  加载卖出记录失败: {e}")

        click.echo("\n📝 正在生成分析报告...")
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

        click.echo("\n✅ 分析完成!")

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
            click.echo(f"使用数据模式: {data_mode}")

        click.echo("\n📊 正在加载数据...")
        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")
        except Exception as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort()

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        click.echo("\n🔢 正在计算收益率...")
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

        click.echo("✅ 收益率计算完成")

        click.echo("\n📝 正在生成计算报告...")
        report = calculate_report_generator.generate_calculate_report(portfolio)
        calculate_report_generator.print_calculate_report(report)

        click.echo("\n✅ 计算完成!")

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
            index_cn_names = {
                "SHComp": "上证指数",
                "HS300": "沪深300",
                "CSI500": "中证500",
                "GEM": "创业板指",
                "STAR50": "科创50",
                "SP500": "标普500",
                "HangSeng": "恒生指数",
                "Nasdaq": "纳斯达克",
                "Nikkei": "日经225",
                "Gold": "黄金",
                "Defense": "军工指数",
                "FTSE": "富时100",
                "DAX": "德国DAX",
                "CAC": "法国CAC",
            }
            for index_key, move in result["moves"].items():
                cn_name = index_cn_names.get(index_key, index_key)
                click.echo(f"  {cn_name}: {move:+.2f}%")

            if result["details"]:
                table = Table(title="\n产品盈亏明细", show_lines=False, expand=False, box=box.SIMPLE)
                table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", width=25)
                table.add_column("类型", style="green", no_wrap=True, width=10)
                table.add_column("金额", justify="right", style="yellow", width=12)
                table.add_column("盈亏", justify="right", width=10)
                table.add_column("收益率", justify="right", width=8)
                table.add_column("指数", style="blue", no_wrap=True, width=8)

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

    @cli.command("predict-etf")
    @click.option("--code", type=str, help="ETF 代码")
    @click.option("--days", type=int, default=5, help="预测天数")
    def predict_etf(code: Optional[str], days: int):
        """预测 ETF 走势"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.data.stock_activity_analyzer import StockActivityAnalyzer

        click.echo("\n📊 ETF 走势预测")
        click.echo("=" * 60)

        try:
            analyzer = StockActivityAnalyzer()
            
            if code:
                result = analyzer.predict_etf(code, days)
                click.echo(f"\n📈 {code} 预测结果:")
                click.echo(f"  当前价格: ¥{result.current_price:.2f}")  # pylint: disable=no-member
                click.echo(f"  预测价格: ¥{result.predicted_price:.2f}")  # pylint: disable=no-member
                click.echo(f"  预测涨跌: {result.predicted_change:.2f}%")
                click.echo(f"  置信度: {result.confidence:.1f}%")
                click.echo(f"  趋势: {result.trend}")
                
                if result.related_stocks:
                    console = Console()
                    table = Table(title="相关股票")
                    table.add_column("代码", style="cyan")
                    table.add_column("名称", style="green")
                    table.add_column("涨跌幅", justify="right")
                    table.add_column("市值", justify="right")
                    
                    for stock in result.related_stocks[:10]:  # pylint: disable=unsubscriptable-object
                        table.add_row(
                            stock.get("code", ""),
                            stock.get("name", ""),
                            f"{stock.get('change_percent', 0):.2f}%",
                            f"¥{stock.get('market_cap', 1):,.1f}",
                        )
                    console.print(table)
            else:
                click.echo("请使用 --code 参数指定 ETF 代码")
                click.echo("示例: asset-lens predict-etf --code 510050 --days 5")

            click.echo(f"\n✅ 预测完成！")

        except Exception as e:
            click.echo(f"❌ 预测失败: {e}", err=True)

    @cli.command("weekly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/weekly_report.md", help="输出文件")
    def weekly(data_mode: Optional[str], output: str):
        """生成周度投资报告"""
        from pathlib import Path
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 生成周度投资报告")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            
            report_lines = [
                "# 周度投资报告",
                "",
                f"**报告日期**: {datetime.now().strftime('%Y-%m-%d')}",
                "",
                "## 投资组合概览",
                "",
                f"- 总产品数: {len(products)}",
                f"- 总金额: ¥{sum(float(p.current_amount or 0) for p in products):,.2f}",
                f"- 总收益: ¥{sum(float(p.current_amount or 0) - float(p.initial_amount or 0) for p in products):,.2f}",
                "",
                "## 本周重点关注",
                "",
                "### 涨幅前5",
                "",
            ]
            
            sorted_products = sorted(
                products, 
                key=lambda p: float(p.return_rate or 0), 
                reverse=True
            )[:5]
            
            for p in sorted_products:
                report_lines.append(f"- {p.name}: {float(p.return_rate or 0):.2f}%")
            
            report_lines.extend([
                "",
                "### 跌幅前5",
                "",
            ])
            
            sorted_products = sorted(
                products, 
                key=lambda p: float(p.return_rate or 0)
            )[:5]
            
            for p in sorted_products:
                report_lines.append(f"- {p.name}: {float(p.return_rate or 0):.2f}%")
            
            report_lines.extend([
                "",
                "## 下周计划",
                "",
                "- 继续关注市场动态",
                "- 定期调整投资组合",
                "",
                "---",
                f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ])
            
            report_content = "\n".join(report_lines)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding="utf-8")
            
            click.echo(f"\n✅ 周报已生成: {output_path}")

        except Exception as e:
            click.echo(f"❌ 生成周报失败: {e}", err=True)

    @cli.command("sentiment")
    def sentiment():
        """分析市场风向"""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from asset_lens.core.market_sentiment import MarketSentimentAnalyzer

        click.echo("\n📊 市场风向分析")
        click.echo("=" * 60)

        try:
            analyzer = MarketSentimentAnalyzer()
            result = analyzer.analyze()

            console = Console()
            
            trend_color = {
                "bullish": "green",
                "bearish": "red",
                "neutral": "yellow"
            }.get(result.trend, "white")
            
            console.print(Panel(
                f"[bold]综合评分[/bold]: {result.overall_score:.1f}/100\n"
                f"[bold]市场趋势[/bold]: [{trend_color}]{result.trend}[/{trend_color}]\n"
                f"[bold]风险等级[/bold]: {result.risk_level}\n"
                f"[bold]分析时间[/bold]: {result.analysis_time}",
                title="市场风向",
                border_style="blue"
            ))

            if result.indicators:
                table = Table(title="情绪指标")
                table.add_column("指标名称", style="cyan")
                table.add_column("数值", justify="right")
                table.add_column("状态", style="green")
                table.add_column("说明", style="yellow")

                for indicator in result.indicators:
                    level_color = {
                        "bullish": "green",
                        "bearish": "red",
                        "neutral": "yellow"
                    }.get(indicator.level, "white")
                    
                    table.add_row(
                        indicator.name,
                        f"{indicator.value:.1f}",
                        f"[{level_color}]{indicator.level}[/{level_color}]",
                        indicator.description
                    )

                console.print(table)

            if result.suggestions:
                click.echo("\n💡 投资建议:")
                for i, suggestion in enumerate(result.suggestions, 1):
                    click.echo(f"  {i}. {suggestion}")

            click.echo(f"\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command("portfolio-metrics")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def portfolio_metrics(data_mode: Optional[str]):
        """计算投资组合专业指标（夏普比率、最大回撤等）"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.portfolio_analytics import PortfolioAnalytics

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 投资组合专业指标分析")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            analytics = PortfolioAnalytics()
            metrics = analytics.calculate_metrics(products)

            console = Console()
            table = Table(title="投资组合指标", show_lines=False)
            table.add_column("指标名称", style="cyan")
            table.add_column("数值", justify="right", style="green")
            table.add_column("说明", style="yellow")

            table.add_row("总资产", f"¥{metrics.total_amount:,.2f}", "投资组合总市值")  # pylint: disable=no-member
            table.add_row("总收益", f"¥{metrics.total_return:,.2f}", "总盈亏金额")
            table.add_row("总收益率", f"{metrics.total_return_rate:.2f}%", "总收益率")  # pylint: disable=no-member
            table.add_row("年化收益率", f"{metrics.annualized_return:.2f}%", "年化收益率")
            table.add_row("夏普比率", f"{metrics.sharpe_ratio:.2f}", "风险调整后收益")
            table.add_row("最大回撤", f"{metrics.max_drawdown:.2f}%", "最大亏损幅度")
            table.add_row("波动率", f"{metrics.volatility:.2f}%", "收益波动程度")
            table.add_row("胜率", f"{metrics.win_rate:.1f}%", "盈利产品占比")

            console.print(table)

            click.echo(f"\n✅ 指标计算完成！")

        except Exception as e:
            click.echo(f"❌ 指标计算失败: {e}", err=True)

    @cli.command("generate-charts")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/charts", help="输出目录")
    def generate_charts(data_mode: Optional[str], output: str):
        """生成投资分析图表（资产配置、风险分布等）"""
        from pathlib import Path
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.report.charts import ChartGenerator

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 生成投资分析图表")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_dir = Path(output)
            chart_gen = ChartGenerator(output_dir)

            portfolio_data = {
                "products": [
                    {
                        "name": p.name,
                        "type": p.investment_type.value if p.investment_type else "未知",
                        "amount": float(p.current_amount or 0),
                        "return_rate": float(p.return_rate or 0),
                    }
                    for p in products
                ]
            }

            charts = chart_gen.generate_all_charts(portfolio_data)

            click.echo(f"\n✅ 已生成 {len(charts)} 个图表:")
            for name, path in charts.items():
                click.echo(f"  📈 {name}: {path}")

            click.echo(f"\n✅ 图表生成完成！")

        except Exception as e:
            click.echo(f"❌ 图表生成失败: {e}", err=True)

    @cli.command("generate-report")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/report.pdf", help="输出文件")
    @click.option("--include-ai", is_flag=True, help="包含 AI 分析")
    def generate_report(data_mode: Optional[str], output: str, include_ai: bool):
        """生成投资分析报告（PDF）"""
        from pathlib import Path
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.report.pdf_report import PDFReportGenerator

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 生成投资分析报告（PDF）")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_gen = PDFReportGenerator(output_path.parent)
            report_path = report_gen.generate(products, output_path.name, include_ai=include_ai)  # pylint: disable=no-member

            click.echo(f"\n✅ 报告已生成: {report_path}")

        except Exception as e:
            click.echo(f"❌ 报告生成失败: {e}", err=True)

    @cli.command("generate-html-report")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/report.html", help="输出文件")
    @click.option("--include-ai", is_flag=True, help="包含 AI 分析")
    def generate_html_report(data_mode: Optional[str], output: str, include_ai: bool):
        """生成投资分析报告（HTML）"""
        from pathlib import Path
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.report.html_report import HTMLReportGenerator

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 生成投资分析报告（HTML）")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_gen = HTMLReportGenerator(output_path.parent)
            report_path = report_gen.generate(products, output_path.name, include_ai=include_ai)  # pylint: disable=no-member

            click.echo(f"\n✅ 报告已生成: {report_path}")

        except Exception as e:
            click.echo(f"❌ 报告生成失败: {e}", err=True)

    @cli.command("ai-analyze")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def ai_analyze(data_mode: Optional[str]):
        """使用 AI 分析投资组合"""
        from rich.console import Console
        from rich.panel import Panel
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.ai_analyzer import AIAnalyzer

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n🤖 AI 投资组合分析")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            analyzer = AIAnalyzer()
            click.echo(f"📊 使用模型: {analyzer.model}")

            portfolio_data = {
                "products": [
                    {
                        "name": p.name,
                        "type": p.investment_type.value if p.investment_type else "未知",
                        "amount": float(p.current_amount or 0),
                        "return_rate": float(p.return_rate or 0),
                        "annual_return": float(p.annual_return or 0),
                    }
                    for p in products
                ],
                "total_amount": sum(float(p.current_amount or 0) for p in products),
                "total_return": sum(
                    float(p.current_amount or 0) - float(p.initial_amount or 0)
                    for p in products
                ),
            }

            click.echo("🔄 正在分析...")
            result = analyzer.analyze_portfolio(portfolio_data)

            console = Console()
            console.print(
                Panel(
                    f"[bold green]投资组合摘要[/bold green]\n\n{result.summary}",
                    title="AI 分析结果",
                    border_style="blue",
                )
            )

            console.print(
                Panel(
                    f"[bold yellow]风险评估[/bold yellow]\n\n{result.risk_assessment}",
                    title="风险分析",
                    border_style="yellow",
                )
            )

            if result.suggestions:
                click.echo("\n💡 投资建议:")
                for i, suggestion in enumerate(result.suggestions, 1):
                    click.echo(f"  {i}. {suggestion}")

            if result.warnings:
                click.echo("\n⚠️ 警告:")
                for warning in result.warnings:
                    click.echo(f"  • {warning}")

            click.echo(f"\n📊 综合评分: {result.score}/100")

            click.echo(f"\n✅ AI 分析完成！")

        except Exception as e:
            click.echo(f"❌ AI 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--before", type=str, help="对比之前的数据目录")
    @click.option("--after", type=str, help="对比之后的数据目录")
    def compare(before: Optional[str], after: Optional[str]):
        """对比不同时期的投资收益变化"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.core.comparison import ComparisonAnalyzer

        click.echo("\n📊 投资组合对比分析")
        click.echo("=" * 60)

        try:
            if before:
                before_dir = Path(before)
            else:
                before_dir = config.get_latest_data_dir()
                if not before_dir:
                    click.echo("❌ 未找到数据目录", err=True)
                    return

            if after:
                after_dir = Path(after)
            else:
                data_dirs = sorted(config.data_path.glob("*_*"))
                if len(data_dirs) < 2:
                    click.echo("❌ 需要至少两个数据目录进行对比", err=True)
                    return
                after_dir = data_dirs[-1]
                before_dir = data_dirs[-2]

            click.echo(f"📁 对比目录: {before_dir.name} vs {after_dir.name}")

            products_before = CSVParser.load_data_from_dir(before_dir)
            products_after = CSVParser.load_data_from_dir(after_dir)

            click.echo(f"✅ 加载 {len(products_before)} 个产品（之前）")
            click.echo(f"✅ 加载 {len(products_after)} 个产品（之后）")

            analyzer = ComparisonAnalyzer()
            result = analyzer.generate_comparison_report(
                products_before, products_after, f"{before_dir.name} vs {after_dir.name}"
            )

            trend = result["comparison"]["trend"]
            click.echo(f"\n💰 总体变化:")
            click.echo(f"  之前总金额: ¥{trend.total_amount_before:,.2f}")
            click.echo(f"  之后总金额: ¥{trend.total_amount_after:,.2f}")
            click.echo(f"  总变化: ¥{trend.total_change:,.2f}")
            click.echo(f"  总收益率: {trend.total_return_rate:.2f}%")

            console = Console()
            table = Table(title="产品对比明细", show_lines=False)
            table.add_column("产品名称", style="cyan")
            table.add_column("类型", style="green")
            table.add_column("之前金额", justify="right")
            table.add_column("之后金额", justify="right")
            table.add_column("变化", justify="right")
            table.add_column("收益率", justify="right")

            for detail in result["comparison"]["details"][:20]:
                table.add_row(
                    detail.name,
                    detail.type,
                    f"¥{detail.amount_before:,.2f}",
                    f"¥{detail.amount_after:,.2f}",
                    f"¥{detail.amount_change:,.2f}",
                    f"{detail.return_rate:.2f}%",
                )

            console.print(table)

            click.echo(f"\n✅ 对比分析完成！")

        except Exception as e:
            click.echo(f"❌ 对比分析失败: {e}", err=True)

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
