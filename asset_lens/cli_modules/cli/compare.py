"""
对比分析 CLI 命令
"""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table


def register_compare_commands(cli: click.Group) -> None:
    """注册对比命令到 CLI 组"""

    @cli.command("compare")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--before", type=str, help="对比前日期 (YYYY-MM-DD)")
    @click.option("--after", type=str, help="对比后日期 (YYYY-MM-DD)")
    @click.option("--days", type=int, default=7, help="对比天数（默认7天）")
    def compare(data_mode: str | None, before: str | None, after: str | None, days: int):
        """投资组合对比分析"""
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode
        from asset_lens.core.comparison import ComparisonAnalyzer
        from asset_lens.data.csv_parser import CSVParser

        setup_data_mode(data_mode)

        click.echo("\n📊 投资组合对比分析")
        click.echo("=" * 60)

        try:
            data_dir = Path("data")
            real_dir = data_dir / "real"

            data_dirs = []
            if real_dir.exists():
                data_dirs = sorted([d for d in real_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

            if len(data_dirs) >= 2:
                before_dir = (
                    data_dirs[-2] if not before else next((d for d in data_dirs if before in d.name), data_dirs[-2])
                )
                after_dir = (
                    data_dirs[-1] if not after else next((d for d in data_dirs if after in d.name), data_dirs[-1])
                )

                click.echo(f"📁 对比目录: {before_dir.name} vs {after_dir.name}")

                products_before = CSVParser.load_data_from_dir(before_dir)
                products_after = CSVParser.load_data_from_dir(after_dir)
            else:
                click.echo("📁 对比当前数据与初始投资")

                products_after = load_products()
                if not products_after:
                    click.echo("❌ 无法加载当前投资产品数据", err=True)
                    return

                products_before = _get_initial_products(products_after)
                if not products_before:
                    click.echo("❌ 无法获取初始投资数据", err=True)
                    return

            click.echo(f"✅ 加载 {len(products_before)} 个产品（之前）")
            click.echo(f"✅ 加载 {len(products_after)} 个产品（之后）")

            analyzer = ComparisonAnalyzer()
            result = analyzer.generate_comparison_report(products_before, products_after, f"近{days}天对比")

            trend = result["comparison"]["trend"]
            click.echo("\n💰 总体变化:")
            click.echo(f"  之前总金额: ¥{trend.total_amount_before:,.2f}")
            click.echo(f"  之后总金额: ¥{trend.total_amount_after:,.2f}")
            click.echo(f"  总变化: ¥{trend.total_change:,.2f}")
            click.echo(f"  总收益率: {trend.total_return_rate:.2f}%")

            click.echo("\n📊 按资产类型分类统计:")
            click.echo("-" * 60)

            type_groups = {
                "权益": ["基金", "定投基金", "ETF", "美股（美元）", "个人养老金", "券商理财"],
                "理财": ["理财"],
                "债券": ["债券"],
                "货币": ["货币", "现金", "现金（港元）"],
                "高端理财": ["高端理财"],
                "美元基金": ["美元基金（美元）"],
                "特别国债": ["特别国债"],
                "黄金": ["黄金"],
                "公募固收": ["公募固收"],
            }

            type_stats: dict[str, dict[str, Decimal | int]] = {}
            for group_name in type_groups:
                type_stats[group_name] = {"before": Decimal("0"), "after": Decimal("0"), "count": 0}

            for detail in result["comparison"]["details"]:
                for group_name, types in type_groups.items():
                    if detail.type in types:
                        type_stats[group_name]["before"] += detail.amount_before
                        type_stats[group_name]["after"] += detail.amount_after
                        type_stats[group_name]["count"] += 1
                        break

            type_table = Table(title="资产类型变化", show_lines=False)
            type_table.add_column("资产类型", style="cyan")
            type_table.add_column("之前金额", justify="right")
            type_table.add_column("之后金额", justify="right")
            type_table.add_column("变化", justify="right")
            type_table.add_column("变化率", justify="right")

            sorted_stats = sorted(
                type_stats.items(),
                key=lambda x: abs(Decimal(str(x[1]["after"])) - Decimal(str(x[1]["before"]))),
                reverse=True,
            )

            console = Console()

            for group_name, stats in sorted_stats:
                before_val = Decimal(str(stats["before"]))
                after_val = Decimal(str(stats["after"]))
                if before_val > 0 or after_val > 0:
                    change = after_val - before_val
                    change_rate = (change / before_val * 100) if before_val > 0 else Decimal("0")
                    change_str = f"¥{change:,.0f}"
                    if change < 0:
                        change_str = f"[red]¥{change:,.0f}[/red]"
                    elif change > 0:
                        change_str = f"[green]¥{change:,.0f}[/green]"
                    type_table.add_row(
                        group_name,
                        f"¥{before_val:,.0f}",
                        f"¥{after_val:,.0f}",
                        change_str,
                        f"{change_rate:.2f}%",
                    )

            console.print(type_table)

            click.echo("\n📋 产品对比明细 (Top 20):")
            table = Table(title="产品对比明细", show_lines=False)
            table.add_column("产品名称", style="cyan")
            table.add_column("类型", style="green")
            table.add_column("之前金额", justify="right")
            table.add_column("之后金额", justify="right")
            table.add_column("变化", justify="right")
            table.add_column("收益率", justify="right")

            for detail in result["comparison"]["details"][:20]:
                change_str = f"¥{detail.amount_change:,.2f}"
                if detail.amount_change < 0:
                    change_str = f"[red]¥{detail.amount_change:,.2f}[/red]"
                elif detail.amount_change > 0:
                    change_str = f"[green]¥{detail.amount_change:,.2f}[/green]"
                table.add_row(
                    detail.name,
                    detail.type,
                    f"¥{detail.amount_before:,.2f}",
                    f"¥{detail.amount_after:,.2f}",
                    change_str,
                    f"{detail.return_rate:.2f}%",
                )

            console.print(table)

            click.echo("\n✅ 对比分析完成！")

        except Exception as e:
            click.echo(f"❌ 对比分析失败: {e}", err=True)

    @cli.command("snapshot")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def create_snapshot(data_mode: str | None):
        """创建投资组合快照"""
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📸 创建投资组合快照")
        click.echo("=" * 60)

        try:
            products = load_products()
            if not products:
                click.echo("❌ 无法加载投资产品数据", err=True)
                return

            today = datetime.now().strftime("%Y-%m-%d")
            snapshot_dir = Path("data/real") / today
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            import shutil

            source_file = Path("data/sample_data/投资产品.csv")
            if source_file.exists():
                shutil.copy(source_file, snapshot_dir / "投资产品.csv")

            click.echo(f"✅ 快照已创建: {snapshot_dir}")
            click.echo(f"   包含 {len(products)} 个投资产品")

        except Exception as e:
            click.echo(f"❌ 创建快照失败: {e}", err=True)


def _get_historical_products(days: int) -> list:
    """获取历史投资产品数据"""
    from datetime import datetime
    from pathlib import Path

    from asset_lens.data.csv_parser import CSVParser

    history_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    snapshot_dir = Path("data/real") / history_date
    if snapshot_dir.exists():
        return CSVParser.load_data_from_dir(snapshot_dir)

    return []


def _get_initial_products(current_products: list) -> list:
    """获取初始投资产品数据（基于初始金额）"""
    from copy import deepcopy

    initial_products = []
    for p in current_products:
        initial_p = deepcopy(p)
        initial_p.current_amount = p.initial_amount
        initial_p.return_rate = 0
        initial_p.profit_amount = 0
        initial_products.append(initial_p)

    return initial_products
