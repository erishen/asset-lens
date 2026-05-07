"""
Analyze CLI commands for asset-lens.
分析命令模块 - 包含 analyze, calculate, pnl, estimate, analyze-sold
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import click
from rich import box
from rich.console import Console
from rich.table import Table


def _get_data_dir(data_mode: str | None) -> Path | None:
    """获取数据目录，处理 None 情况"""
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
        from asset_lens.core.dca_parser import dca_parser
        from asset_lens.core.irr_calculator import irr_calculator
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
        from asset_lens.data.sell_record_parser import SellRecordParser
        from asset_lens.report.analyzer import report_generator

        setup_data_mode(data_mode)

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

        data_dir = _get_data_dir(config.data_mode)
        try:
            usd_rate, hkd_rate = (
                CSVParser.get_exchange_rates(data_dir)
                if data_dir
                else (config.default_usd_rate, config.default_hkd_rate)
            )
        except Exception:
            usd_rate, hkd_rate = config.default_usd_rate, config.default_hkd_rate

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(usd_rate)),
            hkd_rate=Decimal(str(hkd_rate)),
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
            sell_records = SellRecordParser.load_sell_records()
            if sell_records:
                print(f"✅ 成功加载 {len(sell_records)} 条卖出记录")
        except Exception as e:
            print(f"⚠️  加载卖出记录失败: {e}")

        print("\n📝 正在生成分析报告...")
        report_data = report_generator.generate_analysis_report(portfolio, sell_records)

        report_data["products"] = [p.to_dict() for p in portfolio.products if p.annual_return is not None]

        if output_format in ["console", "all"]:
            report_generator.print_console_report(report_data)

        if output_format in ["csv", "all"]:
            report_generator.save_csv_report(report_data, config.output_path)

        if output_format in ["json", "all"]:
            report_generator.save_json_report(report_data, config.output_path)

        print("\n✅ 分析完成!")

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def calculate(data_mode: str | None):
        """计算所有投资产品的收益率（快捷命令）"""
        from datetime import datetime

        from asset_lens.config import config
        from asset_lens.core.dca_parser import dca_parser
        from asset_lens.core.irr_calculator import irr_calculator
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.data.models import Portfolio
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

        data_dir = _get_data_dir(config.data_mode)
        try:
            usd_rate, hkd_rate = (
                CSVParser.get_exchange_rates(data_dir)
                if data_dir
                else (config.default_usd_rate, config.default_hkd_rate)
            )
        except Exception:
            usd_rate, hkd_rate = config.default_usd_rate, config.default_hkd_rate

        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(usd_rate)),
            hkd_rate=Decimal(str(hkd_rate)),
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
                    table.add_row(
                        result.product_name,
                        result.product_type[:6],
                        (result.risk_level or "未知")[:4],
                        f"¥{result.current_value:,.0f}",
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

            console = Console()
            table = Table(title="\n已卖出产品明细")
            table.add_column("产品名称", style="cyan")
            table.add_column("风险等级", style="green")
            table.add_column("初始金额", justify="right")
            table.add_column("收益", justify="right")
            table.add_column("收益率", justify="right")

            total_initial = Decimal("0")
            total_profit = Decimal("0")

            for record in sell_records:
                initial = float(record.initial_amount or 0)
                profit = float(record.profit_amount or 0)
                return_rate = float(record.return_rate or 0)
                total_initial += Decimal(str(initial))
                total_profit += Decimal(str(profit))

                table.add_row(
                    record.name,
                    record.risk_level.value if record.risk_level else "未知",
                    f"¥{initial:,.0f}",
                    f"¥{profit:,.0f}",
                    f"{return_rate:.2f}%",
                )

            console.print(table)

            total_return_rate = (float(total_profit) / float(total_initial) * 100) if total_initial > 0 else 0
            click.echo("\n📊 汇总:")
            click.echo(f"   总投入: ¥{float(total_initial):,.0f}")
            click.echo(f"   总收益: ¥{float(total_profit):,.0f}")
            click.echo(f"   总收益率: {total_return_rate:.2f}%")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command("annual-return")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def annual_return(data_mode: str | None):
        """分析年化收益率（按投资年份分组）"""
        import csv
        from datetime import date, datetime

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config

        setup_data_mode(data_mode)

        console = Console()

        click.echo("\n📊 年化收益率分析")
        click.echo("=" * 60)

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()
            data_dir = _get_data_dir(config.data_mode)

            # 获取汇率
            usd_rate = Decimal("7.2")
            hkd_rate = Decimal("0.92")
            if data_dir:
                try:
                    rates = CSVParser.get_exchange_rates(data_dir)
                    usd_rate = Decimal(str(rates[0]))
                    hkd_rate = Decimal(str(rates[1]))
                except Exception:
                    pass

            # 1. 持有中产品收益
            from asset_lens.cli_modules.cli.report import (
                _get_cny_amount,
                _get_initial_cny_amount,
                _get_profit_cny_amount,
            )

            holding_initial = Decimal("0")
            holding_current = Decimal("0")
            holding_profit = Decimal("0")

            for p in products:
                holding_current += Decimal(str(_get_cny_amount(p)))
                holding_initial += Decimal(str(_get_initial_cny_amount(p)))
                holding_profit += Decimal(str(_get_profit_cny_amount(p)))

            # 2. 已卖出产品收益
            sold_initial = Decimal("0")
            sold_profit = Decimal("0")

            if data_dir:
                sold_file = data_dir / "卖出记录-表格 1.csv"
                if sold_file.exists():
                    with open(sold_file, encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        next(reader)
                        for row in reader:
                            if len(row) >= 21:
                                try:
                                    sold_initial += Decimal(row[19]) if row[19] else Decimal("0")
                                    sold_profit += Decimal(row[20]) if row[20] else Decimal("0")
                                except Exception:
                                    pass

            # 3. 总计
            total_initial = holding_initial + sold_initial
            total_profit = holding_profit + sold_profit

            # 4. 收集投资日期
            investments: list[dict[str, Any]] = []
            missing_date_products: list[dict[str, Any]] = []
            for p in products:
                start_date = None
                initial = Decimal("0")

                if p.transaction_records:
                    for r in p.transaction_records:
                        if isinstance(r, dict) and r.get("date"):
                            try:
                                dt = datetime.strptime(r["date"], "%Y-%m-%d")
                                if start_date is None or dt.date() < start_date:
                                    start_date = dt.date()
                            except Exception:
                                pass
                        if isinstance(r, dict) and r.get("type") == "buy":
                            initial += Decimal(str(r.get("amount", 0)))

                if start_date is None and p.start_date:
                    try:
                        start_date = datetime.strptime(str(p.start_date), "%Y-%m-%d").date()
                        initial = p.initial_amount or Decimal("0")
                    except Exception:
                        pass

                if start_date:
                    investments.append(
                        {
                            "name": p.name,
                            "start_date": start_date,
                            "initial": float(initial) if initial > 0 else float(p.initial_amount or 0),
                            "current": float(p.current_amount or 0),
                        }
                    )
                else:
                    inv_type = p.investment_type.value if p.investment_type else "其他"
                    missing_date_products.append(
                        {
                            "name": p.name,
                            "current": float(p.current_amount or 0),
                            "type": inv_type,
                        }
                    )

            # 5. 计算真实投资周期
            if investments:
                earliest = min(investments, key=lambda x: x["start_date"])
                earliest_date = earliest["start_date"]
                end_date = date(2026, 4, 25)
                days = (end_date - earliest_date).days
                years = days / 365
            else:
                earliest_date = date.today()
                days = 0
                years = 0

            # 6. 输出结果
            total_products = len(products)
            products_with_date = len(investments)
            products_without_date = total_products - products_with_date

            click.echo(f"\n📅 真实投资周期: {earliest_date} ~ 2026-04-25")
            click.echo(f"   投资天数: {days} 天 ({years:.2f} 年)")

            click.echo("\n📊 产品统计:")
            click.echo(f"   总产品数: {total_products}")
            click.echo(f"   有投资日期: {products_with_date}")
            if products_without_date > 0:
                click.echo(f"   缺失日期: {products_without_date} (活期类，未计入年化分析)")
                click.echo("\n⚠️  缺失投资日期的产品 (活期类):")
                for i, item in enumerate(missing_date_products, 1):
                    amount = item["current"]
                    inv_type = item.get("type", "其他")
                    # 美元基金需要换算
                    if inv_type == "美元基金（美元）":
                        cny_amount = amount * float(usd_rate)
                        click.echo(f"      {i}. {item['name']}: ${amount:,.0f} (≈¥{cny_amount:,.0f})")
                    elif inv_type == "股息基金（港元）":
                        cny_amount = amount * float(hkd_rate)
                        click.echo(f"      {i}. {item['name']}: HK${amount:,.0f} (≈¥{cny_amount:,.0f})")
                    elif amount > 0:
                        click.echo(f"      {i}. {item['name']}: ¥{amount:,.0f}")
                    else:
                        click.echo(f"      {i}. {item['name']}: ¥0")

            click.echo("\n💰 收益汇总:")
            click.echo(
                f"   持有中: 本金 ¥{float(holding_initial):,.0f}, 现值 ¥{float(holding_current):,.0f}, 收益 ¥{float(holding_profit):,.0f}"
            )
            click.echo(f"   已卖出: 本金 ¥{float(sold_initial):,.0f}, 收益 ¥{float(sold_profit):,.0f}")

            total_return = float(total_profit / total_initial) if total_initial > 0 else 0
            click.echo("\n📊 总计:")
            click.echo(f"   总投入本金: ¥{float(total_initial):,.0f}")
            click.echo(f"   总收益: ¥{float(total_profit):,.0f}")
            click.echo(f"   期间收益率: {total_return * 100:.2f}%")

            if years > 0:
                annualized = (1 + total_return) ** (1 / years) - 1
                click.echo(f"   简单年化收益率: {annualized * 100:.2f}%")

            # 计算 IRR（内部收益率）
            try:
                from asset_lens.core.irr_calculator import irr_calculator

                # 收集所有产品的现金流
                all_cashflows: list[dict[str, Any]] = []
                base_date = None
                total_current_value = Decimal("0")

                # 第一步：找到最早日期（从交易记录和开始日期）
                for p in products:
                    # 从交易记录找最早日期
                    if p.transaction_records and isinstance(p.transaction_records, str):
                        transactions = CSVParser._parse_transaction_records(p.transaction_records)
                        for t in transactions:
                            if t.get("date") and t.get("amount"):
                                try:
                                    date_str = t["date"].replace("/", "-")
                                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                    if base_date is None or tx_date < base_date:
                                        base_date = tx_date
                                except Exception:
                                    pass
                    # 从开始日期找最早日期（缺失交易记录的产品）
                    if p.start_date:
                        if base_date is None or p.start_date < base_date:
                            base_date = p.start_date

                if base_date:
                    tx_count = 0
                    for p in products:
                        # 有交易记录的产品
                        if p.transaction_records and isinstance(p.transaction_records, str):
                            transactions = CSVParser._parse_transaction_records(p.transaction_records)
                            if transactions:
                                for t in transactions:
                                    if t.get("date") and t.get("amount"):
                                        try:
                                            date_str = t["date"].replace("/", "-")
                                            tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                            days = (tx_date - base_date).days
                                            amount = float(t.get("amount", 0))
                                            tx_type = t.get("type", "").lower()
                                            if tx_type == "buy":
                                                all_cashflows.append({"amount": -amount, "days": days})
                                                tx_count += 1
                                            elif tx_type == "sell":
                                                all_cashflows.append({"amount": amount, "days": days})
                                                tx_count += 1
                                        except Exception:
                                            pass
                                if p.current_amount:
                                    total_current_value += p.current_amount
                            else:
                                # 缺失交易记录但有开始日期和初始金额的产品（一次性买入）
                                if p.start_date and p.initial_amount and p.initial_amount > 0 and p.current_amount:
                                    days = (p.start_date - base_date).days
                                    all_cashflows.append({"amount": -float(p.initial_amount), "days": days})
                                    tx_count += 1
                                    total_current_value += p.current_amount
                        else:
                            # 缺失交易记录但有开始日期和初始金额的产品（一次性买入）
                            if p.start_date and p.initial_amount and p.initial_amount > 0 and p.current_amount:
                                days = (p.start_date - base_date).days
                                all_cashflows.append({"amount": -float(p.initial_amount), "days": days})
                                tx_count += 1
                                total_current_value += p.current_amount

                    # 添加所有产品的当前市值作为最后的正向现金流
                    end_date = date(2026, 4, 25)
                    end_days = (end_date - base_date).days
                    all_cashflows.append({"amount": float(total_current_value), "days": end_days})

                    # 计算 IRR
                    if all_cashflows and len(all_cashflows) > 1:
                        irr = irr_calculator.calculate_irr_with_days(all_cashflows)
                        if irr is not None and -1 < irr < 10:
                            click.echo(f"   IRR 年化收益率: {irr * 100:.2f}%")
                            click.echo(
                                f"   (基于 {tx_count} 笔买入/卖出记录 + {len([p for p in products if not (p.transaction_records and isinstance(p.transaction_records, str) and CSVParser._parse_transaction_records(p.transaction_records))])} 个一次性买入产品)"
                            )
            except Exception:
                pass

            # 7. 按年份分组
            by_year: dict[int, dict[str, int | float | list]] = {}
            for inv in investments:
                year = inv["start_date"].year
                if year not in by_year:
                    by_year[year] = {"count": 0, "initial": 0.0, "current": 0.0, "investments": []}
                by_year[year]["count"] += 1  # type: ignore[operator]
                by_year[year]["initial"] += inv["initial"]  # type: ignore[operator]
                by_year[year]["current"] += inv["current"]  # type: ignore[operator]
                cast(list[dict[str, Any]], by_year[year]["investments"]).append(inv)

            click.echo("\n📈 按投资年份分析:")

            table = Table(title="", box=box.SIMPLE)
            table.add_column("年份", style="cyan", width=6)
            table.add_column("产品数", justify="right", width=6)
            table.add_column("本金", justify="right", width=12)
            table.add_column("现值", justify="right", width=12)
            table.add_column("收益", justify="right", width=10)
            table.add_column("期间收益率", justify="right", width=10)
            table.add_column("平均持有", justify="right", width=8)
            table.add_column("年化收益率", justify="right", width=10)

            for year in sorted(by_year.keys()):
                stats = by_year[year]
                current_val = stats["current"]
                initial_val = stats["initial"]
                profit = float(current_val) - float(initial_val)  # type: ignore[arg-type]
                ret = profit / float(initial_val) * 100 if float(initial_val) > 0 else 0  # type: ignore[arg-type]

                inv_list = cast(list[dict[str, Any]], stats["investments"])
                if inv_list:
                    avg_days = sum((date(2026, 4, 25) - i["start_date"]).days for i in inv_list) / len(inv_list)
                else:
                    avg_days = 0
                avg_years = avg_days / 365

                if avg_years > 0:
                    year_annualized = (1 + ret / 100) ** (1 / avg_years) - 1
                    annualized_str = f"{year_annualized * 100:.2f}%"
                else:
                    annualized_str = "-"

                table.add_row(
                    str(year),
                    str(stats["count"]),
                    f"¥{stats['initial']:,.0f}",
                    f"¥{stats['current']:,.0f}",
                    f"¥{profit:,.0f}",
                    f"{ret:.2f}%",
                    f"{avg_days:.0f}天",
                    annualized_str,
                )

            console.print(table)

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            import traceback

            traceback.print_exc()

    @cli.command("personal-irr")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--monthly-salary", type=float, default=24000, help="月工资（税后）")
    @click.option("--annual-bonus", type=float, default=24000, help="年终奖")
    def personal_irr(data_mode: str | None, monthly_salary: float, annual_bonus: float):
        """计算综合个人财务IRR（工资收入 + 消费支出 + 投资）"""
        import csv
        from datetime import date, datetime

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config

        setup_data_mode(data_mode)

        Console()

        click.echo("\n📊 综合个人财务IRR分析")
        click.echo("=" * 60)

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()
            data_dir = _get_data_dir(config.data_mode)

            Decimal("7.2")
            Decimal("0.92")
            if data_dir:
                try:
                    rates = CSVParser.get_exchange_rates(data_dir)
                    Decimal(str(rates[0]))
                    Decimal(str(rates[1]))
                except Exception:
                    pass

            all_cashflows: list[dict[str, Any]] = []
            base_date = None

            for p in products:
                if p.transaction_records and isinstance(p.transaction_records, str):
                    transactions = CSVParser._parse_transaction_records(p.transaction_records)
                    for t in transactions:
                        if t.get("date") and t.get("amount"):
                            try:
                                date_str = t["date"].replace("/", "-")
                                tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                if base_date is None or tx_date < base_date:
                                    base_date = tx_date
                            except Exception:
                                pass
                if p.start_date:
                    if base_date is None or p.start_date < base_date:
                        base_date = p.start_date

            if base_date is None:
                base_date = date(2024, 11, 1)

            click.echo(f"\n📅 分析周期: {base_date} ~ 2026-04-25")

            consumption_file = data_dir / "消费记录-表格 1.csv" if data_dir else None
            consumption_data: dict[str, float] = {}

            if consumption_file and consumption_file.exists():
                with open(consumption_file, encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if len(row) >= 7 and row[0]:
                            month_str = row[0]
                            try:
                                total = float(row[6]) if row[6] else 0
                                consumption_data[month_str] = total
                            except Exception:
                                pass
                click.echo(f"✅ 读取消费记录: {len(consumption_data)} 个月")
            else:
                click.echo("⚠️  未找到消费记录文件")

            total_salary_income = Decimal("0")
            total_consumption = Decimal("0")

            click.echo("\n💰 工资收入设置:")
            click.echo(f"   月工资（税后）: ¥{monthly_salary:,.0f}")
            click.echo(f"   年终奖: ¥{annual_bonus:,.0f}")
            click.echo(f"   年收入: ¥{monthly_salary * 12 + annual_bonus:,.0f}")

            avg_monthly_consumption = 0.0
            if consumption_data:
                avg_monthly_consumption = sum(consumption_data.values()) / len(consumption_data)
                click.echo(f"   月均消费（推算依据）: ¥{avg_monthly_consumption:,.0f}")

            salary_cashflows: list[dict[str, Any]] = []
            consumption_cashflows: list[dict[str, Any]] = []

            start_year = base_date.year
            start_month = base_date.month
            end_date = date(2026, 4, 25)

            estimated_months = 0
            actual_months = 0

            for year in range(start_year, end_date.year + 1):
                for month in range(1, 13):
                    if year == start_year and month < start_month:
                        continue
                    if year == end_date.year and month > end_date.month:
                        continue

                    salary_date = date(year, month, 15)
                    days = (salary_date - base_date).days
                    if days >= 0:
                        salary_cashflows.append(
                            {"amount": monthly_salary, "days": days, "type": "salary", "date": salary_date}
                        )
                        total_salary_income += Decimal(str(monthly_salary))

                    if month == 12 and year < 2025:
                        bonus_date = date(year, 12, 25)
                        days = (bonus_date - base_date).days
                        if days >= 0:
                            salary_cashflows.append(
                                {"amount": annual_bonus, "days": days, "type": "bonus", "date": bonus_date}
                            )
                            total_salary_income += Decimal(str(annual_bonus))

                    month_key = f"{year}.{month:02d}"
                    consumption_date = date(year, month, 25)
                    days = (consumption_date - base_date).days

                    if days >= 0:
                        if month_key in consumption_data:
                            consumption_amount = consumption_data[month_key]
                            consumption_cashflows.append(
                                {
                                    "amount": -consumption_amount,
                                    "days": days,
                                    "type": "consumption",
                                    "date": consumption_date,
                                }
                            )
                            total_consumption += Decimal(str(consumption_amount))
                            actual_months += 1
                        elif avg_monthly_consumption > 0:
                            consumption_cashflows.append(
                                {
                                    "amount": -avg_monthly_consumption,
                                    "days": days,
                                    "type": "consumption_estimated",
                                    "date": consumption_date,
                                }
                            )
                            total_consumption += Decimal(str(avg_monthly_consumption))
                            estimated_months += 1

            click.echo("\n📊 收支汇总:")
            click.echo(f"   工资收入: ¥{float(total_salary_income):,.0f}")
            click.echo("      (2025年年终奖未发放，已排除)")
            click.echo(f"   消费支出: ¥{float(total_consumption):,.0f}")
            if estimated_months > 0:
                click.echo(f"      (实际记录 {actual_months} 个月 + 推算 {estimated_months} 个月)")
            click.echo(f"   净收入: ¥{float(total_salary_income - total_consumption):,.0f}")

            from asset_lens.cli_modules.cli.report import (
                _get_cny_amount,
                _get_initial_cny_amount,
                _get_profit_cny_amount,
            )

            holding_initial = Decimal("0")
            holding_current = Decimal("0")
            holding_profit = Decimal("0")

            for p in products:
                holding_current += Decimal(str(_get_cny_amount(p)))
                holding_initial += Decimal(str(_get_initial_cny_amount(p)))
                holding_profit += Decimal(str(_get_profit_cny_amount(p)))

            sold_initial = Decimal("0")
            sold_profit = Decimal("0")

            if data_dir:
                sold_file = data_dir / "卖出记录-表格 1.csv"
                if sold_file.exists():
                    with open(sold_file, encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        next(reader)
                        for row in reader:
                            if len(row) >= 21:
                                try:
                                    sold_initial += Decimal(row[19]) if row[19] else Decimal("0")
                                    sold_profit += Decimal(row[20]) if row[20] else Decimal("0")
                                except Exception:
                                    pass

            total_investment = holding_initial + sold_initial
            total_profit = holding_profit + sold_profit
            total_current_value = holding_current

            click.echo("\n📈 投资汇总:")
            click.echo(
                f"   持有中: 本金 ¥{float(holding_initial):,.0f}, 现值 ¥{float(holding_current):,.0f}, 收益 ¥{float(holding_profit):,.0f}"
            )
            click.echo(f"   已卖出: 本金 ¥{float(sold_initial):,.0f}, 收益 ¥{float(sold_profit):,.0f}")
            click.echo(f"   总投入: ¥{float(total_investment):,.0f}")
            click.echo(f"   总收益: ¥{float(total_profit):,.0f}")

            investment_cashflows: list[dict[str, Any]] = []

            for p in products:
                if p.transaction_records and isinstance(p.transaction_records, str):
                    transactions = CSVParser._parse_transaction_records(p.transaction_records)
                    if transactions:
                        for t in transactions:
                            if t.get("date") and t.get("amount"):
                                try:
                                    date_str = t["date"].replace("/", "-")
                                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                    days = (tx_date - base_date).days
                                    amount = float(t.get("amount", 0))
                                    tx_type = t.get("type", "").lower()
                                    if tx_type == "buy":
                                        investment_cashflows.append(
                                            {
                                                "amount": -amount,
                                                "days": days,
                                                "type": "investment_buy",
                                                "product": p.name,
                                            }
                                        )
                                    elif tx_type == "sell":
                                        investment_cashflows.append(
                                            {
                                                "amount": amount,
                                                "days": days,
                                                "type": "investment_sell",
                                                "product": p.name,
                                            }
                                        )
                                except Exception:
                                    pass
                    else:
                        if p.start_date and p.initial_amount and p.initial_amount > 0 and p.current_amount:
                            days = (p.start_date - base_date).days
                            investment_cashflows.append(
                                {
                                    "amount": -float(p.initial_amount),
                                    "days": days,
                                    "type": "investment_buy",
                                    "product": p.name,
                                }
                            )
                else:
                    if p.start_date and p.initial_amount and p.initial_amount > 0 and p.current_amount:
                        days = (p.start_date - base_date).days
                        investment_cashflows.append(
                            {
                                "amount": -float(p.initial_amount),
                                "days": days,
                                "type": "investment_buy",
                                "product": p.name,
                            }
                        )

            all_cashflows = []

            for cf in salary_cashflows:
                all_cashflows.append({"amount": cf["amount"], "days": cf["days"]})

            for cf in consumption_cashflows:
                all_cashflows.append({"amount": cf["amount"], "days": cf["days"]})

            for cf in investment_cashflows:
                all_cashflows.append({"amount": cf["amount"], "days": cf["days"]})

            end_days = (end_date - base_date).days
            all_cashflows.append({"amount": float(total_current_value), "days": end_days})

            if all_cashflows and len(all_cashflows) > 1:
                from asset_lens.core.irr_calculator import irr_calculator

                irr = irr_calculator.calculate_irr_with_days(all_cashflows)
                if irr is not None and -1 < irr < 10:
                    click.echo("\n🎯 综合IRR分析结果:")
                    click.echo(f"   IRR 年化收益率: {irr * 100:.2f}%")
                    click.echo("   说明: 包含工资收入、消费支出、投资产品")

                    float(total_current_value + total_salary_income - total_consumption - total_investment)
                    click.echo("\n📊 财富净值变化:")
                    click.echo(f"   期末资产: ¥{float(total_current_value):,.0f}")
                    click.echo(f"   期间净收入: ¥{float(total_salary_income - total_consumption):,.0f}")
                else:
                    click.echo("\n📊 综合财务分析:")
                    total_net_income = float(total_salary_income - total_consumption)
                    total_wealth_change = total_net_income + float(total_profit)

                    click.echo(f"   期间净收入（工资-消费）: ¥{total_net_income:,.0f}")
                    click.echo(f"   投资收益: ¥{float(total_profit):,.0f}")
                    click.echo(f"   总财富变化: ¥{total_wealth_change:,.0f}")

                    if total_investment > 0:
                        investment_return_rate = float(total_profit / total_investment) * 100
                        click.echo(f"   投资收益率: {investment_return_rate:.2f}%")

                    savings_rate = (
                        (total_net_income / float(total_salary_income) * 100) if float(total_salary_income) > 0 else 0
                    )
                    click.echo(f"   储蓄率: {savings_rate:.1f}%")

                    click.echo("\n💡 说明: IRR计算需要更长时间跨度的数据才能得出有意义的结果")
            else:
                click.echo("\n⚠️  现金流数据不足，无法计算IRR")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            import traceback

            traceback.print_exc()
