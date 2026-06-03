"""
Core analyze CLI commands.
核心分析命令 - analyze, calculate, pnl, estimate, analyze-sold
"""

import logging
from decimal import Decimal
from pathlib import Path
from typing import Any, TypedDict

import click
from rich import box
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


class _YearStats(TypedDict):
    count: int
    initial: float
    current: float
    investments: list[dict[str, Any]]


def _get_data_dir(data_mode: str | None) -> Path | None:
    from pathlib import Path

    from asset_lens.config import config

    if data_mode == "real" or (data_mode is None and config.data_mode == "real"):
        if config.real_data_path:
            return Path(config.real_data_path)
        return config.get_latest_data_dir()
    elif data_mode == "sample" or data_mode is None:
        return config.project_root / "data" / "sample_data"
    else:
        if config.real_data_path:
            return Path(config.real_data_path)
        return config.get_latest_data_dir()


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
        from datetime import datetime

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
        from asset_lens.data.sell_record_parser import SellRecordParser
        from asset_lens.report.analyzer import report_generator

        setup_data_mode(data_mode)

        logger.info("正在加载数据...")
        try:
            products = CSVParser.load_data(Path(data_path)) if data_path else CSVParser.load_data()
            logger.info(f"成功加载 {len(products)} 个投资产品")
        except (OSError, ValueError, KeyError, TypeError) as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort() from None

        data_dir = _get_data_dir(config.data_mode)
        try:
            usd_rate, hkd_rate = (
                CSVParser.get_exchange_rates(data_dir)
                if data_dir
                else (config.default_usd_rate, config.default_hkd_rate)
            )
        except (ValueError, KeyError, TypeError):
            usd_rate, hkd_rate = config.default_usd_rate, config.default_hkd_rate

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(usd_rate)),
            hkd_rate=Decimal(str(hkd_rate)),
        )

        logger.info("正在计算收益率...")
        reference_date = datetime.now()

        from asset_lens.data.parsers.investment_calculator import InvestmentCalculator

        for product in portfolio.products:
            InvestmentCalculator.calculate_product_returns(product, reference_date)

        logger.info("收益率计算完成")

        sell_records = []
        try:
            sell_records = SellRecordParser.load_sell_records()
            if sell_records:
                logger.info(f"成功加载 {len(sell_records)} 条卖出记录")
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"加载卖出记录失败: {e}")

        logger.info("正在生成分析报告...")
        report_data = report_generator.generate_analysis_report(portfolio, sell_records)

        report_data["products"] = [p.to_dict() for p in portfolio.products if p.annual_return is not None]

        if output_format in ["console", "all"]:
            report_generator.print_console_report(report_data)

        if output_format in ["csv", "all"]:
            report_generator.save_csv_report(report_data, config.output_path)

        if output_format in ["json", "all"]:
            report_generator.save_json_report(report_data, config.output_path)

        logger.info("分析完成!")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def calculate(data_mode: str | None):
        """计算所有投资产品的收益率（快捷命令）"""
        from datetime import datetime

        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
        from asset_lens.report.calculate_report import calculate_report_generator

        if data_mode:
            config.data_mode = data_mode
            logger.info(f"使用数据模式: {data_mode}")

        logger.info("正在加载数据...")
        try:
            products = CSVParser.load_data()
            logger.info(f"成功加载 {len(products)} 个投资产品")
        except (OSError, ValueError, KeyError, TypeError) as e:
            click.echo(f"❌ 加载数据失败: {e}", err=True)
            raise click.Abort() from None

        data_dir = _get_data_dir(config.data_mode)
        try:
            usd_rate, hkd_rate = (
                CSVParser.get_exchange_rates(data_dir)
                if data_dir
                else (config.default_usd_rate, config.default_hkd_rate)
            )
        except (ValueError, KeyError, TypeError):
            usd_rate, hkd_rate = config.default_usd_rate, config.default_hkd_rate

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(usd_rate)),
            hkd_rate=Decimal(str(hkd_rate)),
        )

        logger.info("正在计算收益率...")
        reference_date = datetime.now()

        from asset_lens.data.parsers.investment_calculator import InvestmentCalculator

        for product in portfolio.products:
            InvestmentCalculator.calculate_product_returns(product, reference_date)
        logger.info("收益率计算完成")
        logger.info("正在生成计算报告...")
        report = calculate_report_generator.generate_calculate_report(portfolio)
        calculate_report_generator.print_calculate_report(report)
        click.echo("\n✅ 计算完成!")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--weekly", is_flag=True, help="周盈亏模式")
    def pnl(data_mode: str | None, weekly: bool):
        """估算今日/本周盈亏"""
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode
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
            total_amount_all = result.get("total_amount_all", total_amount)
            return_rate = result.get("total_return_rate", 0)

            click.echo(f"\n💰 总资产: ¥{total_amount_all:,.2f}")
            click.echo(f"💰 权益资产: ¥{total_amount:,.2f}")
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
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode
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
                    for value in moves.values():
                        total_change += Decimal(str(value))
                        count += 1
                    if count > 0:
                        market_change = total_change / count / Decimal("100")
            except (ValueError, TypeError) as e:
                logger.debug("分析参数解析失败: %s", e)

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
                    from asset_lens.utils.cli_utils import format_amount_with_currency

                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        format_amount_with_currency(float(result.current_value), result.investment_type),
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_daily_return_rate:.2f}%",
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
                    from asset_lens.utils.cli_utils import format_amount_with_currency

                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        format_amount_with_currency(float(result.current_value), result.investment_type),
                        f"¥{result.estimated_daily_return:,.0f}",
                        f"{result.estimated_daily_return_rate:.2f}%",
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

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.data.sell_record_parser import SellRecordParser

        setup_data_mode(data_mode)

        click.echo("\n📊 已卖出产品分析")
        click.echo("=" * 60)

        try:
            sell_records = SellRecordParser.load_sell_records()

            if not sell_records:
                click.echo("没有已卖出的产品")
                return

            click.echo(f"✅ 找到 {len(sell_records)} 个已卖出产品")

            # 数据验证
            missing_data_count = 0
            for record in sell_records:
                if not record.initial_amount or record.initial_amount <= 0:
                    missing_data_count += 1
                    click.echo(f"⚠️  {record.name}: 缺少初始金额数据")

            if missing_data_count > 0:
                click.echo(f"\n⚠️  警告: {missing_data_count} 个产品数据不完整")

            console = Console()
            table = Table(title="\n已卖出产品明细")
            table.add_column("产品名称", style="cyan", width=25)
            table.add_column("风险等级", style="green", width=8)
            table.add_column("初始金额", justify="right", width=12)
            table.add_column("收益", justify="right", width=10)
            table.add_column("收益率", justify="right", width=10)
            table.add_column("持有天数", justify="right", width=8)
            table.add_column("年化收益率", justify="right", width=10)

            total_initial = Decimal("0")
            total_profit = Decimal("0")
            records_with_days: list[dict[str, Any]] = []

            for record in sell_records:
                initial = float(record.initial_amount or 0)
                profit = float(record.profit_amount or 0)
                return_rate = float(record.return_rate or 0)

                # 计算持有天数
                days = record.investment_days or 0
                if days == 0 and record.start_date and record.sell_date:
                    days = (record.sell_date - record.start_date).days

                # 计算年化收益率（如果没有）
                annual_return = float(record.annual_return or 0)
                if annual_return == 0 and days > 0 and return_rate != 0:
                    years = days / 365
                    if years > 0:
                        annual_return = ((1 + return_rate / 100) ** (1 / years) - 1) * 100

                total_initial += Decimal(str(initial))
                total_profit += Decimal(str(profit))

                if days > 0:
                    records_with_days.append(
                        {
                            "name": record.name,
                            "days": days,
                            "return_rate": return_rate,
                            "annual_return": annual_return,
                            "initial": initial,
                        }
                    )

                table.add_row(
                    record.name[:25],
                    record.risk_level.value if record.risk_level else "未知",
                    f"¥{initial:,.0f}",
                    f"¥{profit:,.0f}",
                    f"{return_rate:.2f}%",
                    str(days) if days > 0 else "-",
                    f"{annual_return:.2f}%" if annual_return != 0 else "-",
                )

            console.print(table)

            # 汇总统计
            total_return_rate = (float(total_profit) / float(total_initial) * 100) if total_initial > 0 else 0
            click.echo("\n📊 汇总:")
            click.echo(f"   总投入: ¥{float(total_initial):,.0f}")
            click.echo(f"   总收益: ¥{float(total_profit):,.0f}")
            click.echo(f"   总收益率: {total_return_rate:.2f}%")

            # 持有期分析
            if records_with_days:
                click.echo("\n📅 持有期分析:")
                avg_days = sum(r["days"] for r in records_with_days) / len(records_with_days)
                click.echo(f"   平均持有天数: {avg_days:.0f} 天")

                # 按持有期分组
                short_term = [r for r in records_with_days if r["days"] < 90]
                mid_term = [r for r in records_with_days if 90 <= r["days"] < 365]
                long_term = [r for r in records_with_days if r["days"] >= 365]

                if short_term:
                    avg_return = sum(r["return_rate"] for r in short_term) / len(short_term)
                    click.echo(f"   短期投资(<90天): {len(short_term)} 个, 平均收益率 {avg_return:.2f}%")
                if mid_term:
                    avg_return = sum(r["return_rate"] for r in mid_term) / len(mid_term)
                    click.echo(f"   中期投资(90-365天): {len(mid_term)} 个, 平均收益率 {avg_return:.2f}%")
                if long_term:
                    avg_return = sum(r["return_rate"] for r in long_term) / len(long_term)
                    click.echo(f"   长期投资(>365天): {len(long_term)} 个, 平均收益率 {avg_return:.2f}%")

            click.echo("\n✅ 分析完成！")

        except FileNotFoundError as e:
            click.echo(f"❌ 文件未找到: {e}", err=True)
        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            import traceback

            traceback.print_exc()
