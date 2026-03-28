"""
Analyze CLI commands for asset-lens.
分析命令模块 - 包含 analyze, calculate, pnl, estimate, analyze-sold
"""

from decimal import Decimal
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box


def _get_data_dir(data_mode: str) -> Path | None:
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
    def analyze(data_mode: str | None, output_format: str, data_path: str | None):
        """分析投资组合并生成报告"""
        from asset_lens.cli.helpers import (
            load_products,
            setup_data_mode,
        )
        from asset_lens.config import config
        from asset_lens.report.analyzer import ReportGenerator

        setup_data_mode(data_mode)

        click.echo("\n📊 投资组合分析")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            from asset_lens.data.models import Portfolio
            portfolio = Portfolio(products=products)

            report_gen = ReportGenerator()
            report = report_gen.generate_analysis_report(portfolio)

            click.echo("\n📈 投资组合概览:")
            summary = report.get("portfolio_summary", {})
            total_value = summary.get("total_value", "0")
            total_profit = summary.get("total_profit", "0")
            total_return_rate = summary.get("total_return_rate", "0%")
            click.echo(f"  总资产: ¥{float(total_value):,.2f}")
            click.echo(f"  总收益: ¥{float(total_profit):,.2f}")
            click.echo(f"  总收益率: {total_return_rate}")

            if output_format in ["console", "all"]:
                console = Console()
                table = Table(title="\n产品明细", show_lines=False, expand=False, box=box.SIMPLE)
                table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", width=25)
                table.add_column("类型", style="green", no_wrap=True, width=10)
                table.add_column("金额", justify="right", style="yellow", width=12)
                table.add_column("收益率", justify="right", width=10)

                for product in sorted(products, key=lambda p: float(p.return_rate or 0), reverse=True)[:20]:
                    table.add_row(
                        product.name[:25],
                        product.investment_type.value if product.investment_type else "未知",
                        f"¥{float(product.current_amount or 0):,.0f}",
                        f"{float(product.return_rate or 0):.2f}%",
                    )

                console.print(table)

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def calculate(data_mode: str | None):
        """计算投资组合的收益"""
        from asset_lens.cli_modules.cli.helpers import (
            load_products,
            setup_data_mode,
        )

        setup_data_mode(data_mode)

        click.echo("\n📊 计算投资组合收益")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            total_amount = sum(float(p.current_amount or 0) for p in products)
            total_initial = sum(float(p.initial_amount or 0) for p in products)
            total_profit = total_amount - total_initial
            total_return = (total_profit / total_initial * 100) if total_initial > 0 else 0

            click.echo(f"\n💰 总资产: ¥{total_amount:,.2f}")
            click.echo(f"💵 总投入: ¥{total_initial:,.2f}")
            click.echo(f"📈 总收益: ¥{total_profit:,.2f}")
            click.echo(f"📊 收益率: {total_return:.2f}%")

            console = Console()
            table = Table(title="\n收益率排名 (前10)", show_lines=False, expand=False, box=box.SIMPLE)
            table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", width=25)
            table.add_column("类型", style="green", no_wrap=True, width=10)
            table.add_column("金额", justify="right", style="yellow", width=12)
            table.add_column("收益", justify="right", width=10)
            table.add_column("收益率", justify="right", width=10)

            sorted_products = sorted(products, key=lambda p: float(p.return_rate or 0), reverse=True)[:10]
            for product in sorted_products:
                profit = float(product.current_amount or 0) - float(product.initial_amount or 0)
                table.add_row(
                    product.name[:25],
                    product.investment_type.value if product.investment_type else "未知",
                    f"¥{float(product.current_amount or 0):,.0f}",
                    f"¥{profit:,.0f}",
                    f"{float(product.return_rate or 0):.2f}%",
                )

            console.print(table)

            click.echo("\n✅ 计算完成！")

        except Exception as e:
            click.echo(f"❌ 计算失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--weekly", is_flag=True, help="周盈亏模式")
    def pnl(data_mode: str | None, weekly: bool):
        """估算今日/本周盈亏"""
        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.core.realtime_pnl import RealtimePnlEstimator

        setup_data_mode(data_mode)

        period_text = "本周" if weekly else "今日"
        click.echo(f"\n📊 {period_text}盈亏估算")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            estimator = RealtimePnlEstimator()
            result = estimator.estimate_portfolio_pnl(products, is_weekly=weekly)

            total_pnl = result.get("total", 0)
            total_amount = result.get("total_amount", 0)
            return_rate = result.get("total_return_rate", 0)

            click.echo(f"\n💰 总资产: ¥{total_amount:,.2f}")
            click.echo(f"📈 {period_text}盈亏: ¥{total_pnl:,.2f}")
            click.echo(f"📊 收益率: {return_rate:.2f}%")

            console = Console()
            table = Table(title=f"\n{period_text}盈亏明细", show_lines=False, expand=False, box=box.SIMPLE)
            table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", width=25)
            table.add_column("类型", style="green", no_wrap=True, width=10)
            table.add_column("金额", justify="right", style="yellow", width=12)
            table.add_column("盈亏", justify="right", width=10)
            table.add_column("收益率", justify="right", width=8)

            for detail in result.get("details", [])[:20]:
                table.add_row(
                    detail.get("name", "")[:25],
                    detail.get("type", ""),
                    f"¥{detail.get('amount', 0):,.0f}",
                    f"¥{detail.get('pnl', 0):,.0f}",
                    f"{detail.get('return_rate', 0):.2f}%",
                )

            console.print(table)

            click.echo("\n✅ 估算完成！")

        except Exception as e:
            click.echo(f"❌ 估算失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--weekly", is_flag=True, help="周预估模式")
    def estimate(data_mode: str | None, weekly: bool):
        """全产品收益估算（基于预期年化收益率）"""
        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.core.daily_estimate import estimate_all_products
        from asset_lens.core.realtime_pnl import RealtimePnlEstimator

        setup_data_mode(data_mode)

        period_text = "周" if weekly else "日"
        click.echo(f"\n📊 全产品{period_text}收益估算")
        click.echo("=" * 60)

        try:
            products = load_products()
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

                for result in up_results[:30]:
                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        f"¥{result.current_value:,.0f}",
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_return_rate:.2f}%",
                    )

                console.print(table)

            if down_results:
                click.echo(f"\n🔴 下跌产品 ({len(down_results)} 个):")
                table = Table(show_header=True, header_style="bold red", expand=True)
                table.add_column("产品名称", style="cyan", no_wrap=True, min_width=20)
                table.add_column("类型", min_width=6)
                table.add_column("风险", min_width=4)
                table.add_column("市值", justify="right", min_width=10)
                table.add_column("预估收益", justify="right", min_width=8)
                table.add_column("收益率", justify="right", min_width=7)

                for result in down_results[:30]:
                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        f"¥{result.current_value:,.0f}",
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_return_rate:.2f}%",
                    )

                console.print(table)

            total_estimated = sum(r.estimated_daily_return for r in results)
            click.echo(f"\n💰 预估总收益: ¥{total_estimated:,.0f}")

            click.echo("\n✅ 估算完成！")

        except Exception as e:
            click.echo(f"❌ 估算失败: {e}", err=True)

    @cli.command("analyze-sold")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def analyze_sold(data_mode: str | None):
        """分析已卖出产品"""
        from asset_lens.cli.helpers import load_products, setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 已卖出产品分析")
        click.echo("=" * 60)

        try:
            products = load_products()
            sold_products = [p for p in products if p.status and p.status.value == "sold"]

            if not sold_products:
                click.echo("没有已卖出的产品")
                return

            click.echo(f"✅ 找到 {len(sold_products)} 个已卖出产品")

            console = Console()
            table = Table(title="\n已卖出产品明细")
            table.add_column("产品名称", style="cyan")
            table.add_column("类型", style="green")
            table.add_column("卖出金额", justify="right")
            table.add_column("收益", justify="right")
            table.add_column("收益率", justify="right")

            for p in sold_products:
                profit = float(p.current_amount or 0) - float(p.initial_amount or 0)
                return_rate = (profit / float(p.initial_amount or 1) * 100) if p.initial_amount else 0
                table.add_row(
                    p.name,
                    p.investment_type.value if p.investment_type else "未知",
                    f"¥{float(p.current_amount or 0):,.0f}",
                    f"¥{profit:,.0f}",
                    f"{return_rate:.2f}%",
                )

            console.print(table)

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
