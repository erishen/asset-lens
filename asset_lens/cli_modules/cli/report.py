"""
报告生成 CLI 命令
"""

import logging

import click

from asset_lens.utils.currency_converter import (
    format_amount,
    get_cny_amount,
    get_global_rates,
    get_initial_cny_amount,
    get_profit_cny_amount,
)

logger = logging.getLogger(__name__)


def _get_cny_amount(product) -> float:
    return get_cny_amount(product)


def _get_initial_cny_amount(product) -> float:
    return get_initial_cny_amount(product)


def _get_profit_cny_amount(product) -> float:
    return get_profit_cny_amount(product)


def _format_amount(product) -> str:
    return format_amount(product)


def _get_global_rates() -> tuple[float, float]:
    return get_global_rates()


from asset_lens.cli_modules.cli.report_monthly import register_monthly_command
from asset_lens.cli_modules.cli.report_weekly import register_weekly_command


def register_report_commands(cli: click.Group) -> None:
    """注册报告命令到 CLI 组"""

    register_weekly_command(cli)
    register_monthly_command(cli)

    @cli.command("daily-report")
    def daily_report():
        """生成日度报告（快速摘要）"""
        from datetime import datetime

        from rich.console import Console
        from rich.panel import Panel

        from asset_lens.cli_modules.cli.helpers import load_products

        console = Console()
        console.print("\n📝 日度报告")
        console.print("=" * 60)

        try:
            console.print(f"\n📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            console.print("\n💰 投资组合概览:")
            try:
                products = load_products()

                if products:
                    total_amount = sum(_get_cny_amount(p) for p in products)
                    total_profit = sum(_get_profit_cny_amount(p) for p in products)
                    profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0

                    summary = f"""
总资产: ¥{total_amount:,.2f}
总收益: ¥{total_profit:,.2f}
收益率: {profit_rate:+.2f}%
产品数: {len(products)}
"""
                    console.print(Panel(summary, title="投资组合", border_style="blue"))
                else:
                    console.print("[yellow]⚠️ 无投资组合数据[/yellow]")
            except (FileNotFoundError, ValueError, OSError) as e:
                logger.debug(f"忽略异常: {e}")
                console.print("[yellow]⚠️ 无法加载投资组合[/yellow]")

            console.print("\n✅ 日度报告生成完成！")

        except Exception as e:
            console.print(f"[red]❌ 报告生成失败: {e}[/red]")
