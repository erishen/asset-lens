"""
对比分析 CLI 命令
"""

from decimal import Decimal

import click
from rich.console import Console
from rich.table import Table


def register_compare_commands(cli: click.Group) -> None:
    """注册对比命令到 CLI 组"""

    @cli.command("compare")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--before", type=str, help="对比前日期 (YYYY-MM-DD)")
    @click.option("--after", type=str, help="对比后日期 (YYYY-MM-DD)")
    def compare(data_mode: str | None, before: str | None, after: str | None):
        """投资组合对比分析"""
        from pathlib import Path

        from asset_lens.cli.helpers import setup_data_mode
        from asset_lens.core.comparison import ComparisonAnalyzer
        from asset_lens.data.csv_parser import CSVParser

        setup_data_mode(data_mode)

        click.echo("\n📊 投资组合对比分析")
        click.echo("=" * 60)

        try:
            data_dir = Path("data")
            real_dir = data_dir / "real"

            if real_dir.exists():
                data_dirs = sorted([d for d in real_dir.iterdir() if d.is_dir()], key=lambda x: x.name)
            else:
                data_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

            if not data_dirs:
                click.echo("❌ 没有找到数据目录", err=True)
                return

            if len(data_dirs) < 2:
                click.echo("❌ 需要至少两个数据目录进行对比", err=True)
                click.echo(f"💡 当前找到 {len(data_dirs)} 个目录: {[d.name for d in data_dirs]}", err=True)
                return

            before_dir = data_dirs[-2] if not before else next((d for d in data_dirs if before in d.name), data_dirs[-2])
            after_dir = data_dirs[-1] if not after else next((d for d in data_dirs if after in d.name), data_dirs[-1])

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
            click.echo("\n💰 总体变化:")
            click.echo(f"  之前总金额: ¥{trend.total_amount_before:,.2f}")
            click.echo(f"  之后总金额: ¥{trend.total_amount_after:,.2f}")
            click.echo(f"  总变化: ¥{trend.total_change:,.2f}")
            click.echo(f"  总收益率: {trend.total_return_rate:.2f}%")

            click.echo("\n📊 按资产类型分类统计:")
            click.echo("-" * 60)

            type_groups = {
                '权益': ['基金', '定投基金', 'ETF', '美股（美元）', '个人养老金', '券商理财'],
                '理财': ['理财'],
                '债券': ['债券'],
                '货币': ['货币', '现金', '现金（港元）'],
                '高端理财': ['高端理财'],
                '美元基金': ['美元基金（美元）'],
                '特别国债': ['特别国债'],
                '黄金': ['黄金'],
                '公募固收': ['公募固收'],
            }

            type_stats = {}
            for group_name, types in type_groups.items():
                type_stats[group_name] = {
                    'before': Decimal('0'),
                    'after': Decimal('0'),
                    'count': 0
                }

            for detail in result["comparison"]["details"]:
                for group_name, types in type_groups.items():
                    if detail.type in types:
                        type_stats[group_name]['before'] += detail.amount_before
                        type_stats[group_name]['after'] += detail.amount_after
                        type_stats[group_name]['count'] += 1
                        break

            type_table = Table(title="资产类型变化", show_lines=False)
            type_table.add_column("资产类型", style="cyan")
            type_table.add_column("之前金额", justify="right")
            type_table.add_column("之后金额", justify="right")
            type_table.add_column("变化", justify="right")
            type_table.add_column("变化率", justify="right")

            sorted_stats = sorted(type_stats.items(), key=lambda x: abs(x[1]['after'] - x[1]['before']), reverse=True)

            console = Console()

            for group_name, stats in sorted_stats:
                if stats['before'] > 0 or stats['after'] > 0:
                    change = stats['after'] - stats['before']
                    change_rate = (change / stats['before'] * 100) if stats['before'] > 0 else Decimal('0')
                    change_str = f"¥{change:,.0f}"
                    if change < 0:
                        change_str = f"[red]¥{change:,.0f}[/red]"
                    elif change > 0:
                        change_str = f"[green]¥{change:,.0f}[/green]"
                    type_table.add_row(
                        group_name,
                        f"¥{stats['before']:,.0f}",
                        f"¥{stats['after']:,.0f}",
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

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def analyze_by_time(data_mode: str | None):
        """按投资时间分组分析"""
        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.core.time_group import TimeGroupAnalyzer

        setup_data_mode(data_mode)

        click.echo("\n📊 按投资时间分组分析")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            analyzer = TimeGroupAnalyzer()
            result = analyzer.analyze_by_holding_period(products)

            click.echo("\n📈 总体统计:")
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
                        group["group"],
                        group["description"],
                        str(group["count"]),
                        f"¥{group['total_amount']:,.0f}",
                        f"¥{group['total_profit']:,.0f}",
                        f"{group['avg_return_rate']:.2f}%",
                        f"{group['avg_holding_days']:.0f}天",
                    )

                console.print(table)

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
