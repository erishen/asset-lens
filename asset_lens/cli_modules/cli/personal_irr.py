import logging
from decimal import Decimal
from typing import Any

import click

from asset_lens.cli_modules.cli.analyze_core import _get_data_dir

logger = logging.getLogger(__name__)


def register_personal_irr_command(cli: click.Group) -> None:
    @cli.command("personal-irr")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--monthly-salary", type=float, default=None, help="月工资（税后），默认从配置文件读取")
    @click.option("--annual-bonus", type=float, default=None, help="年终奖，默认从配置文件或bonus_records.json读取")
    def personal_irr(data_mode: str | None, monthly_salary: float | None, annual_bonus: float | None):
        import csv
        import json
        from datetime import date, datetime
        from pathlib import Path

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config, settings

        setup_data_mode(data_mode)

        if monthly_salary is None:
            monthly_salary = settings.monthly_salary

        bonus_records = {}
        bonus_file = Path(__file__).parent.parent.parent.parent / "data" / "bonus_records.json"
        if bonus_file.exists():
            try:
                with open(bonus_file, encoding="utf-8") as f:
                    bonus_data = json.load(f)
                    for record in bonus_data.get("records", []):
                        bonus_records[record["year"]] = {
                            "date": datetime.strptime(record["issue_date"], "%Y-%m-%d").date(),
                            "amount": record["after_tax"],
                            "note": record.get("note", ""),
                        }
            except (json.JSONDecodeError, OSError, ValueError, KeyError) as e:
                click.echo(f"⚠️  读取年终奖记录失败: {e}")

        if annual_bonus is None:
            annual_bonus = settings.annual_bonus

        click.echo("\n📊 综合个人财务IRR分析")
        click.echo("=" * 60)

        click.echo("\n⚠️  假设条件:")
        click.echo(f"   1. 月工资（税后）: ¥{monthly_salary:,.0f}")
        if bonus_records:
            click.echo(f"   2. 年终奖: 从 bonus_records.json 读取（共 {len(bonus_records)} 年记录）")
        else:
            click.echo(f"   2. 年终奖: ¥{annual_bonus:,.0f}（固定金额）")
        click.echo("   3. 工资发放日: 每月15日")
        click.echo("   4. 年终奖发放日: 每年12月25日（或从JSON文件读取实际日期）")
        click.echo("   5. 消费支出: 每月25日")
        click.echo("\n💡 提示:")
        click.echo("   - 可在 .env 文件中配置 MONTHLY_SALARY 和 ANNUAL_BONUS")
        click.echo("   - 可在 data/bonus_records.json 中记录每年的年终奖详情")
        click.echo("   - 也可通过 --monthly-salary 和 --annual-bonus 参数临时调整")

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()
            data_dir = _get_data_dir(config.data_mode)

            end_date = date.today()
            if data_dir:
                dir_name = data_dir.name
                if dir_name.startswith("money_csv_"):
                    try:
                        date_str = dir_name.replace("money_csv_", "")
                        end_date = datetime.strptime(date_str, "%Y%m%d").date()
                    except ValueError as e:
                        logger.debug("日期解析失败: %s", e)

            if data_dir:
                try:
                    CSVParser.get_exchange_rates(data_dir)
                    # rates[0]=USD, rates[1]=HKD 汇率已读取
                except (ValueError, TypeError) as e:
                    logger.debug("汇率参数解析失败: %s", e)

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
                            except ValueError as e:
                                logger.debug("交易日期解析失败: %s", e)
                if p.start_date and (base_date is None or p.start_date < base_date):
                    base_date = p.start_date

            if base_date is None:
                base_date = date(2024, 11, 1)

            click.echo(f"\n📅 分析周期: {base_date} ~ {end_date}")

            products_with_transactions = sum(1 for p in products if p.transaction_records)
            products_with_start_date = sum(1 for p in products if p.start_date)
            click.echo("\n📊 数据完整性:")
            click.echo(f"   总产品数: {len(products)}")
            click.echo(f"   有交易记录: {products_with_transactions}")
            click.echo(f"   有开始日期: {products_with_start_date}")

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
                            except (ValueError, TypeError) as e:
                                logger.debug("消费数据解析失败: %s", e)
                click.echo(f"   消费记录: {len(consumption_data)} 个月")
            else:
                click.echo("   消费记录: ⚠️  未找到")

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
            else:
                click.echo("   ⚠️  消费数据缺失，将无法准确计算储蓄率")

            salary_cashflows: list[dict[str, Any]] = []
            consumption_cashflows: list[dict[str, Any]] = []

            start_year = base_date.year
            start_month = base_date.month

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

                    if month == 12:
                        if year in bonus_records:
                            bonus_date = bonus_records[year]["date"]
                            bonus_amount = bonus_records[year]["amount"]
                            days = (bonus_date - base_date).days
                            if days >= 0 and bonus_date <= end_date:
                                salary_cashflows.append(
                                    {
                                        "amount": bonus_amount,
                                        "days": days,
                                        "type": "bonus",
                                        "date": bonus_date,
                                        "note": bonus_records[year].get("note", ""),
                                    }
                                )
                                total_salary_income += Decimal(str(bonus_amount))
                        else:
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
            click.echo(f"   消费支出: ¥{float(total_consumption):,.0f}")
            if estimated_months > 0:
                click.echo(f"      (实际记录 {actual_months} 个月 + 推算 {estimated_months} 个月)")
                click.echo("      ⚠️  推算部分可能不准确，建议补充消费记录数据")
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
                                except (ValueError, TypeError) as e:
                                    logger.debug("卖出记录解析失败: %s", e)

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
                                except (ValueError, TypeError, KeyError) as e:
                                    logger.debug(f"忽略异常: {e}")
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
                    click.echo("\n⚠️  注意事项:")
                    click.echo("   1. IRR计算基于假设条件，实际结果可能有所不同")
                    click.echo("   2. 建议定期更新数据以提高准确性")
                    click.echo("   3. 消费数据不完整时，IRR结果可能偏高")

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

        except FileNotFoundError as e:
            click.echo(f"❌ 文件未找到: {e}", err=True)
        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            import traceback

            traceback.print_exc()
