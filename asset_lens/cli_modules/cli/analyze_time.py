import logging
from decimal import Decimal
from typing import Any

import click
from rich.console import Console

from asset_lens.cli_modules.cli.analyze_core import _get_data_dir

logger = logging.getLogger(__name__)


def register_analyze_time_commands(cli: click.Group) -> None:
    @cli.command("analyze-by-time")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def analyze_by_time(data_mode: str | None):
        from datetime import date, datetime

        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.config import config

        setup_data_mode(data_mode)

        console = Console()

        click.echo("\n📊 按投资时间分组分析")
        click.echo("=" * 60)

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()

            Decimal("7.2")
            Decimal("0.92")
            data_dir = _get_data_dir(config.data_mode)
            if data_dir:
                try:
                    rates = CSVParser.get_exchange_rates(data_dir)
                    Decimal(str(rates[0]))
                    Decimal(str(rates[1]))
                except (ValueError, TypeError) as e:
                    logger.debug("汇率参数解析失败: %s", e)

            short_term: list[dict[str, Any]] = []
            medium_term: list[dict[str, Any]] = []
            long_term: list[dict[str, Any]] = []
            very_long_term: list[dict[str, Any]] = []

            end_date = date.today()
            if data_dir:
                dir_name = data_dir.name
                if dir_name.startswith("money_csv_"):
                    try:
                        date_str = dir_name.replace("money_csv_", "")
                        end_date = datetime.strptime(date_str, "%Y%m%d").date()
                    except ValueError as e:
                        logger.debug("日期解析失败: %s", e)

            for p in products:
                if not p.start_date or not p.current_amount:
                    continue

                days = (end_date - p.start_date).days

                if days < 0:
                    continue

                years = days / 365

                from asset_lens.cli_modules.cli.report import _get_cny_amount

                amount = float(_get_cny_amount(p))
                initial = float(p.initial_amount or 0)
                profit = float(p.profit_amount or 0) if p.profit_amount else amount - initial

                product_info = {
                    "name": p.name,
                    "type": p.investment_type.value if p.investment_type else "其他",
                    "days": days,
                    "years": years,
                    "initial": initial,
                    "current": amount,
                    "profit": profit,
                    "return_rate": float(p.return_rate) if p.return_rate else 0,
                    "annual_return": float(p.annual_return) if p.annual_return else 0,
                }

                if days < 90:
                    short_term.append(product_info)
                elif days < 365:
                    medium_term.append(product_info)
                elif days < 1095:
                    long_term.append(product_info)
                else:
                    very_long_term.append(product_info)

            def print_group(name: str, products_list: list[dict], color: str):
                if not products_list:
                    return

                click.echo(f"\n{color} {name}:")
                click.echo("-" * 60)

                total_initial = sum(p["initial"] for p in products_list)
                total_current = sum(p["current"] for p in products_list)
                total_profit = sum(p["profit"] for p in products_list)
                avg_return = total_profit / total_initial * 100 if total_initial > 0 else 0

                weighted_annual = 0
                total_weight = 0
                for p in products_list:
                    if p["annual_return"] > 0:
                        weighted_annual += p["annual_return"] * p["initial"]
                        total_weight += p["initial"]

                avg_annual = weighted_annual / total_weight if total_weight > 0 else 0

                click.echo(f"   产品数: {len(products_list)}")
                click.echo(f"   总本金: ¥{total_initial:,.0f}")
                click.echo(f"   总现值: ¥{total_current:,.0f}")
                click.echo(f"   总收益: ¥{total_profit:,.0f}")
                click.echo(f"   平均收益率: {avg_return:.2f}%")
                if avg_annual > 0:
                    click.echo(f"   加权年化收益率: {avg_annual:.2f}%")

                from rich.table import Table

                table = Table(title="\n   前5个产品", show_header=True, header_style="bold cyan")
                table.add_column("排名", style="cyan", width=6)
                table.add_column("产品名称", style="white", width=35)
                table.add_column("现值(¥)", justify="right", style="green", width=12)
                table.add_column("天数", justify="right", style="yellow", width=8)
                table.add_column("实际收益率", justify="right", style="magenta", width=12)
                table.add_column("年化收益率", justify="right", width=12)

                for i, p in enumerate(sorted(products_list, key=lambda x: x["annual_return"], reverse=True)[:5], 1):
                    annual_return_str = f"{p['annual_return']:.2f}%" if p["annual_return"] > 0 else "-"
                    annual_return_style = "green" if p["annual_return"] > 0 else "red"
                    table.add_row(
                        str(i),
                        p["name"],
                        f"{p['current']:,.0f}",
                        str(p["days"]),
                        f"{p['return_rate']:.2f}%",
                        f"[{annual_return_style}]{annual_return_str}[/{annual_return_style}]",
                    )

                console.print(table)

            print_group("短期投资（< 90天）", short_term, "🟢")
            print_group("中期投资（90-365天）", medium_term, "🟡")
            print_group("长期投资（1-3年）", long_term, "🟠")
            print_group("超长期投资（> 3年）", very_long_term, "🔴")

            total_products = len(short_term) + len(medium_term) + len(long_term) + len(very_long_term)
            total_initial = (
                sum(p["initial"] for p in short_term)
                + sum(p["initial"] for p in medium_term)
                + sum(p["initial"] for p in long_term)
                + sum(p["initial"] for p in very_long_term)
            )
            total_current = (
                sum(p["current"] for p in short_term)
                + sum(p["current"] for p in medium_term)
                + sum(p["current"] for p in long_term)
                + sum(p["current"] for p in very_long_term)
            )
            total_profit = (
                sum(p["profit"] for p in short_term)
                + sum(p["profit"] for p in medium_term)
                + sum(p["profit"] for p in long_term)
                + sum(p["profit"] for p in very_long_term)
            )

            click.echo("\n📊 汇总:")
            click.echo(f"   总产品数: {total_products}")
            click.echo(f"   总本金: ¥{total_initial:,.0f}")
            click.echo(f"   总现值: ¥{total_current:,.0f}")
            click.echo(f"   总收益: ¥{total_profit:,.0f}")
            if total_initial > 0:
                click.echo(f"   总收益率: {total_profit / total_initial * 100:.2f}%")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            import traceback

            traceback.print_exc()

    from .personal_irr import register_personal_irr_command

    register_personal_irr_command(cli)
