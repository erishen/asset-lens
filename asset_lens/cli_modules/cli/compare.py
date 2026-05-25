"""
对比分析 CLI 命令
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table


def _get_data_dirs() -> list[Path]:
    data_dir = Path("data")
    real_dir = data_dir / "real"
    ts_demo_data_dir = Path("../ts-demo/data")

    data_dirs = []
    if real_dir.exists():
        data_dirs = sorted([d for d in real_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

    if len(data_dirs) < 2 and ts_demo_data_dir.exists():
        ts_dirs = sorted(
            [d for d in ts_demo_data_dir.iterdir() if d.is_dir() and d.name.startswith("money_csv_")],
            key=lambda x: x.name,
        )
        existing_names = {d.name for d in data_dirs}
        for d in ts_dirs:
            if d.name not in existing_names:
                data_dirs.append(d)
        data_dirs.sort(key=lambda x: x.name)

    return data_dirs


def _load_products_with_returns(data_dir: Path) -> dict[str, dict]:
    from asset_lens.data.csv_parser import CSVParser
    from asset_lens.data.parsers.investment_calculator import InvestmentCalculator

    products = CSVParser.load_data_from_dir(data_dir)
    result = {}

    for p in products:
        if not p.name or not p.start_date:
            continue

        InvestmentCalculator.calculate_product_returns(p)

        key = f"{p.name}@{_get_main_platform(p)}"
        result[key] = {
            "name": p.name,
            "platform": _get_main_platform(p),
            "annual_return": float(p.annual_return) if p.annual_return else 0,
            "return_rate": float(p.return_rate) if p.return_rate else 0,
            "current_amount": float(p.current_amount or 0),
            "initial_amount": float(p.initial_amount or 0),
            "investment_days": p.investment_days or 0,
            "type": p.investment_type.value if p.investment_type else "",
            "start_date": str(p.start_date) if p.start_date else "",
        }

    return result


def _get_main_platform(product) -> str:
    from asset_lens.data.models import InvestmentType

    if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
        return "富途"
    elif product.investment_type in [InvestmentType.HK_STOCK, InvestmentType.HK_CASH, InvestmentType.HK_DIVIDEND_FUND]:
        return "港招"

    platform_fields = ["微信", "中金", "支付宝", "富途", "招商", "港招", "交通", "浦发", "建设", "中信", "民生", "工商", "中银"]
    for field in platform_fields:
        val = getattr(product, field, None)
        if val and float(val) > 0:
            return field
    return "-"


def _format_return(value: float) -> str:
    if value == 0:
        return "  0.00%"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def register_compare_commands(cli: click.Group) -> None:
    """注册对比命令到 CLI 组"""

    @cli.command("compare")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--before", type=str, help="对比前日期 (YYYYMMDD)")
    @click.option("--after", type=str, help="对比后日期 (YYYYMMDD)")
    @click.option("--days", type=int, default=7, help="对比天数（默认7天）")
    @click.option("--trend", is_flag=True, default=False, help="显示所有时间点收益率趋势")
    @click.option("--limit", type=int, default=10, help="趋势分析最多使用的时间点数（默认10）")
    def compare(data_mode: str | None, before: str | None, after: str | None, days: int, trend: bool, limit: int):
        """投资组合对比分析（收益率趋势对比）"""
        from asset_lens.cli_modules.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        console = Console()

        data_dirs = _get_data_dirs()

        if (trend or (not before and not after)) and len(data_dirs) >= 2:
            _show_trend_analysis(console, data_dirs[-limit:], before, after)
            return

        if len(data_dirs) >= 2:
            before_dir = (
                data_dirs[-2] if not before else next((d for d in data_dirs if before.replace("-", "") in d.name), data_dirs[-2])
            )
            after_dir = (
                data_dirs[-1] if not after else next((d for d in data_dirs if after.replace("-", "") in d.name), data_dirs[-1])
            )

            _show_two_date_comparison(console, before_dir, after_dir)
        else:
            _show_initial_comparison(console)

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


def _show_trend_analysis(console: Console, data_dirs: list[Path], before: str | None, after: str | None):
    """显示所有时间点的收益率趋势分析（类似 ts-demo npm run compare）"""
    console.print("\n[bold blue]📅 所有时间点收益趋势分析[/bold blue]")
    console.print("─" * 80)

    if before and after:
        before_dir = next((d for d in data_dirs if before.replace("-", "") in d.name), None)
        after_dir = next((d for d in data_dirs if after.replace("-", "") in d.name), None)
        if before_dir and after_dir:
            _show_two_date_comparison(console, before_dir, after_dir)
            return

    all_data: dict[str, dict[str, dict]] = {}
    dir_dates = []

    for d in data_dirs:
        date_str = d.name.replace("money_csv_", "")
        products = _load_products_with_returns(d)
        all_data[date_str] = products
        dir_dates.append(date_str)

    if len(dir_dates) < 2:
        console.print("[yellow]⚠️  需要至少两个时间点的数据才能进行比较[/yellow]")
        return

    product_trends: dict[str, list[float]] = {}
    for date_str in dir_dates:
        for key, info in all_data[date_str].items():
            if key not in product_trends:
                product_trends[key] = []
            product_trends[key].append(info["annual_return"])

    consistently_improving = []
    consistently_deteriorating = []
    for key, returns in product_trends.items():
        if len(returns) < 3:
            continue
        improving_count = sum(1 for i in range(1, len(returns)) if returns[i] - returns[i - 1] > 1.0)
        deteriorating_count = sum(1 for i in range(1, len(returns)) if returns[i] - returns[i - 1] < -1.0)
        total_change = returns[-1] - returns[0]

        if improving_count >= len(returns) - 1 and total_change > 5:
            consistently_improving.append((key, returns[0], returns[-1], total_change))
        elif deteriorating_count >= len(returns) - 1 and total_change < -5:
            consistently_deteriorating.append((key, returns[0], returns[-1], total_change))

    if consistently_improving:
        console.print(f"\n[bold red]🚀 持续上涨产品[/bold red] ({len(consistently_improving)}个):")
        for key, first, last, change in consistently_improving[:5]:
            name = key.split("@")[0]
            console.print(
                f"  • {name:<20s} {_format_return(first)} → {_format_return(last)} "
                f"[red](总上涨+{change:.2f}%)[/red]"
            )

    if consistently_deteriorating:
        console.print(f"\n[bold green]🔻 持续下跌产品[/bold green] ({len(consistently_deteriorating)}个):")
        for key, first, last, change in consistently_deteriorating[:5]:
            name = key.split("@")[0]
            console.print(
                f"  • {name:<20s} {_format_return(first)} → {_format_return(last)} "
                f"[green](总下跌{change:.2f}%)[/green]"
            )

    for i in range(1, len(dir_dates)):
        current_date = dir_dates[i]
        previous_date = dir_dates[i - 1]
        current_data = all_data[current_date]
        previous_data = all_data[previous_date]

        improving = 0
        deteriorating = 0
        max_improving = ("", 0)
        max_deteriorating = ("", 0)

        for key, info in current_data.items():
            if key in previous_data:
                change = info["annual_return"] - previous_data[key]["annual_return"]
                if change > 0.5:
                    improving += 1
                    if change > max_improving[1]:
                        max_improving = (info["name"], change)
                elif change < -0.5:
                    deteriorating += 1
                    if change < max_deteriorating[1]:
                        max_deteriorating = (info["name"], change)

        console.print(f"\n[bold cyan]时间段: {previous_date} → {current_date}[/bold cyan]")
        console.print(
            f"  上涨: [red]{improving}个[/red], 下跌: [green]{deteriorating}个[/green]"
        )
        if max_improving[0]:
            console.print(f"  最大上涨: {max_improving[0]} [red]+{max_improving[1]:.2f}%[/red]")
        if max_deteriorating[0]:
            console.print(f"  最大下跌: {max_deteriorating[0]} [green]{max_deteriorating[1]:.2f}%[/green]")

    first_data = all_data[dir_dates[0]]
    last_data = all_data[dir_dates[-1]]
    first_avg = sum(v["annual_return"] for v in first_data.values()) / len(first_data) if first_data else 0
    last_avg = sum(v["annual_return"] for v in last_data.values()) / len(last_data) if last_data else 0
    total_change = last_avg - first_avg

    console.print(f"\n{'─' * 80}")
    console.print("[bold magenta]📈 总体投资趋势分析[/bold magenta]")
    console.print(f"• 平均年化收益率: {first_avg:.2f}% → {last_avg:.2f}%")
    change_str = f"+{total_change:.2f}%" if total_change >= 0 else f"{total_change:.2f}%"
    console.print(f"• 总体变化: {'[red]' if total_change >= 0 else '[green]'}{change_str}[/]")
    console.print(f"• 分析时间范围: {dir_dates[0]} - {dir_dates[-1]} ({len(dir_dates)}个时间点)")

    console.print("\n[bold red]💡 投资建议:[/bold red]")
    if total_change > 3:
        console.print("✅ 投资策略有效，继续保持当前方向")
    elif total_change > 0:
        console.print("⚠️  收益增长缓慢，考虑优化投资组合")
    else:
        console.print("❌ 需要重新评估投资策略，考虑调整资产配置")

    console.print("\n[bold yellow]📌 重要说明:[/bold yellow]")
    console.print("   本工具比较的是【年化收益率】的变化")
    console.print("   ⚠️  对于有交易记录的产品，年化收益率会剧烈波动")
    console.print("   ✅ 适用于观察长期趋势、发现新增或卖出的产品")


def _show_two_date_comparison(console: Console, before_dir: Path, after_dir: Path):
    """显示两个时间点的收益率对比"""
    before_date = before_dir.name.replace("money_csv_", "")
    after_date = after_dir.name.replace("money_csv_", "")

    console.print("\n[bold blue]📊 投资收益比较报告[/bold blue]")
    console.print(f"[blue]对比时间: {before_date} → {after_date}[/blue]")
    console.print("─" * 80)

    before_data = _load_products_with_returns(before_dir)
    after_data = _load_products_with_returns(after_dir)

    improving = []
    deteriorating = []
    stable = []
    new_products = []
    sold_products = []

    for key, after_info in after_data.items():
        if key in before_data:
            before_info = before_data[key]
            change = after_info["annual_return"] - before_info["annual_return"]
            entry = {
                "name": after_info["name"],
                "platform": after_info["platform"],
                "before_return": before_info["annual_return"],
                "after_return": after_info["annual_return"],
                "change": change,
                "current_amount": after_info["current_amount"],
                "initial_amount": after_info["initial_amount"],
                "type": after_info["type"],
            }
            if change > 0.5:
                improving.append(entry)
            elif change < -0.5:
                deteriorating.append(entry)
            else:
                stable.append(entry)
        else:
            new_products.append({
                "name": after_info["name"],
                "platform": after_info["platform"],
                "return": after_info["annual_return"],
                "days": after_info["investment_days"],
                "current_amount": after_info["current_amount"],
                "type": after_info["type"],
            })

    for key, before_info in before_data.items():
        if key not in after_data:
            sold_products.append({
                "name": before_info["name"],
                "platform": before_info["platform"],
                "return": before_info["annual_return"],
                "initial_amount": before_info["initial_amount"],
                "type": before_info["type"],
            })

    if improving:
        improving.sort(key=lambda x: x["change"], reverse=True)
        console.print(f"\n[bold red]📈 收益上涨产品[/bold red] ({len(improving)}个):")
        for item in improving[:8]:
            console.print(
                f"  • {item['name']:<20s} {_format_return(item['before_return'])} → {_format_return(item['after_return'])} "
                f"[red](+{item['change']:.2f}%)[/red]"
            )

    if deteriorating:
        deteriorating.sort(key=lambda x: x["change"])
        console.print(f"\n[bold green]📉 收益下跌产品[/bold green] ({len(deteriorating)}个):")
        for item in deteriorating[:8]:
            console.print(
                f"  • {item['name']:<20s} {_format_return(item['before_return'])} → {_format_return(item['after_return'])} "
                f"[green]({item['change']:.2f}%)[/green]"
            )

    if new_products:
        console.print(f"\n[bold cyan]🆕 新增投资产品[/bold cyan] ({len(new_products)}个):")
        for item in new_products[:5]:
            amount_str = f"{item['current_amount'] / 10000:.1f}万元" if item['current_amount'] >= 10000 else f"¥{item['current_amount']:,.0f}"
            console.print(
                f"  • {item['name']:<20s} {_format_return(item['return'])} ({item['days']}天) "
                f"金额: {amount_str}"
            )

    if sold_products:
        console.print(f"\n[bold yellow]💰 已卖出产品[/bold yellow] ({len(sold_products)}个):")
        for item in sold_products[:5]:
            amount_str = f"{item['initial_amount'] / 10000:.1f}万元" if item['initial_amount'] >= 10000 else f"¥{item['initial_amount']:,.0f}"
            console.print(
                f"  • {item['name']:<20s} 卖出时收益 {_format_return(item['return'])} "
                f"投入: {amount_str}"
            )

    console.print(f"\n[gray bold]⚖️  收益稳定产品[/gray bold]: {len(stable)}个")

    new_capital = sum(p["current_amount"] for p in new_products)
    sold_capital = sum(p["initial_amount"] for p in sold_products)
    improving_capital = sum(p["current_amount"] for p in improving)
    deteriorating_capital = sum(p["current_amount"] for p in deteriorating)
    net_flow = new_capital - sold_capital

    console.print("\n[bold magenta]💸 资金流动分析:[/bold magenta]")
    console.print(f"• 新增投资资金: [cyan]{new_capital / 10000:.1f}万元[/cyan]")
    console.print(f"• 卖出回收资金: [yellow]{sold_capital / 10000:.1f}万元[/yellow]")
    console.print(f"• 上涨产品资金: [red]{improving_capital / 10000:.1f}万元[/red]")
    console.print(f"• 下跌产品资金: [green]{deteriorating_capital / 10000:.1f}万元[/green]")
    net_str = f"+{net_flow / 10000:.1f}" if net_flow >= 0 else f"{net_flow / 10000:.1f}"
    console.print(f"• 净资金流动: {'[red]' if net_flow >= 0 else '[green]'}{net_str}万元[/]")

    console.print(f"\n{'─' * 80}")
    console.print("[bold magenta]📋 详细统计摘要:[/bold magenta]")
    console.print(f"• 总产品数量: {len(before_data) + len(new_products)}")
    console.print(f"• 收益上涨: [red]{len(improving)}个[/red]")
    console.print(f"• 收益下跌: [green]{len(deteriorating)}个[/green]")
    console.print(f"• 新增投资: [cyan]{len(new_products)}个[/cyan]")
    console.print(f"• 已卖出: [yellow]{len(sold_products)}个[/yellow]")


def _show_initial_comparison(console: Console):
    """显示当前数据与初始投资的对比"""
    from asset_lens.cli_modules.cli.helpers import load_products

    console.print("\n[bold blue]📊 投资组合对比分析[/bold blue]")
    console.print("=" * 60)
    console.print("📁 对比当前数据与初始投资")

    products_after = load_products()
    if not products_after:
        console.print("[red]❌ 无法加载当前投资产品数据[/red]")
        return

    products_before = _get_initial_products(products_after)
    if not products_before:
        console.print("[red]❌ 无法获取初始投资数据[/red]")
        return

    from asset_lens.config import config
    from asset_lens.core.comparison import ComparisonAnalyzer
    from asset_lens.data.csv_parser import CSVParser

    usd_rate = Decimal(str(config.default_usd_rate))
    hkd_rate = Decimal(str(config.default_hkd_rate))
    try:
        latest_data_dir = config.get_latest_data_dir()
        if latest_data_dir:
            usd_rate_f, hkd_rate_f = CSVParser.get_exchange_rates(latest_data_dir)
            usd_rate = Decimal(str(usd_rate_f))
            hkd_rate = Decimal(str(hkd_rate_f))
    except (ValueError, TypeError):
        pass

    analyzer = ComparisonAnalyzer()
    result = analyzer.generate_comparison_report(
        products_before, products_after, "初始投资对比", usd_rate, hkd_rate
    )

    trend = result["comparison"]["trend"]
    console.print("\n💰 总体变化:")
    console.print(f"  之前总金额: ¥{trend.total_amount_before:,.2f}")
    console.print(f"  之后总金额: ¥{trend.total_amount_after:,.2f}")
    console.print(f"  总变化: ¥{trend.total_change:,.2f}")
    console.print(f"  总收益率: {trend.total_return_rate:.2f}%")

    table = Table(title="产品对比明细 (Top 20)", show_lines=False)
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
    console.print("\n✅ 对比分析完成！")


def _get_initial_products(current_products: list) -> list:
    """获取初始投资产品数据（基于初始金额，考虑汇率转换）"""
    from copy import deepcopy

    from asset_lens.config import config
    from asset_lens.data.models import InvestmentType

    usd_rate = Decimal(str(config.default_usd_rate))
    hkd_rate = Decimal(str(config.default_hkd_rate))
    try:
        from asset_lens.data.csv_parser import CSVParser

        data_dir = config.get_latest_data_dir()
        if data_dir:
            usd_rate_f, hkd_rate_f = CSVParser.get_exchange_rates(data_dir)
            usd_rate = Decimal(str(usd_rate_f))
            hkd_rate = Decimal(str(hkd_rate_f))
    except (ValueError, TypeError):
        pass

    initial_products = []
    for p in current_products:
        initial_p = deepcopy(p)

        initial_amount = p.initial_amount or Decimal("0")
        if initial_amount > 0:
            if p.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                rate = Decimal(str(p.usd_rate)) if p.usd_rate else usd_rate
                initial_amount = initial_amount * rate
            elif p.investment_type in [
                InvestmentType.HK_STOCK,
                InvestmentType.HK_CASH,
                InvestmentType.HK_DIVIDEND_FUND,
            ]:
                rate = Decimal(str(p.hkd_rate)) if p.hkd_rate else hkd_rate
                initial_amount = initial_amount * rate

        initial_p.current_amount = initial_amount
        initial_p.return_rate = 0
        initial_p.profit_amount = 0
        initial_products.append(initial_p)

    return initial_products
