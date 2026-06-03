"""
Annual return analyze CLI command.
年化收益率分析命令
"""

import logging
from decimal import Decimal
from typing import Any

import click
from rich import box
from rich.console import Console
from rich.table import Table

from asset_lens.cli_modules.cli.analyze_core import _get_data_dir, _YearStats

logger = logging.getLogger(__name__)


def register_annual_return_command(cli: click.Group) -> None:
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

            # 从数据目录名称中提取日期
            end_date = date.today()
            if data_dir:
                dir_name = data_dir.name
                if dir_name.startswith("money_csv_"):
                    try:
                        date_str = dir_name.replace("money_csv_", "")
                        end_date = datetime.strptime(date_str, "%Y%m%d").date()
                    except ValueError:
                        pass

            # 获取汇率
            usd_rate = Decimal("7.2")
            hkd_rate = Decimal("0.92")
            if data_dir:
                try:
                    rates = CSVParser.get_exchange_rates(data_dir)
                    usd_rate = Decimal(str(rates[0]))
                    hkd_rate = Decimal(str(rates[1]))
                except (ValueError, TypeError):
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
                                except (ValueError, TypeError):
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
                            except ValueError:
                                pass
                        if isinstance(r, dict) and r.get("type") == "buy":
                            initial += Decimal(str(r.get("amount", 0)))

                if start_date is None and p.start_date:
                    try:
                        start_date = datetime.strptime(str(p.start_date), "%Y-%m-%d").date()
                        initial = p.initial_amount or Decimal("0")
                    except ValueError:
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

            click.echo(f"\n📅 真实投资周期: {earliest_date} ~ {end_date}")
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
                                except ValueError:
                                    pass
                    # 从开始日期找最早日期（缺失交易记录的产品）
                    if p.start_date and (base_date is None or p.start_date < base_date):
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
                                        except (ValueError, TypeError):
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
            except Exception as e:
                logger.debug(f"忽略异常: {e}")

            # 7. 按年份分组
            by_year: dict[int, _YearStats] = {}
            for inv in investments:
                year = inv["start_date"].year
                if year not in by_year:
                    by_year[year] = {"count": 0, "initial": 0.0, "current": 0.0, "investments": []}
                by_year[year]["count"] += 1
                by_year[year]["initial"] += inv["initial"]
                by_year[year]["current"] += inv["current"]
                by_year[year]["investments"].append(inv)

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
                profit = float(current_val) - float(initial_val)
                ret = profit / float(initial_val) * 100 if float(initial_val) > 0 else 0

                inv_list = stats["investments"]
                avg_days = sum((end_date - i["start_date"]).days for i in inv_list) / len(inv_list) if inv_list else 0
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
