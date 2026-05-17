"""
Risk Alert CLI commands for asset-lens.
风险预警命令
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def risk():
    """风险预警管理命令"""
    pass


@risk.command()
def status():
    """显示风险预警状态"""
    from asset_lens.monitoring.risk_alert import risk_alert_system

    summary = risk_alert_system.get_alert_summary()

    console.print(Panel.fit("[bold cyan]风险预警系统状态[/bold cyan]", subtitle=f"预警总数: {summary['total_alerts']}"))

    config_table = Table(title="预警配置")
    config_table.add_column("配置项", style="cyan")
    config_table.add_column("阈值", style="green")

    config = summary["config"]
    config_table.add_row("最大回撤阈值", f"{config['max_drawdown_threshold']}%")
    config_table.add_row("波动率阈值", f"{config['volatility_threshold']}%")
    config_table.add_row("集中度阈值", f"{config['concentration_threshold']}%")
    config_table.add_row("止损线", f"{config['stop_loss_percent']}%")
    config_table.add_row("止盈线", f"{config['take_profit_percent']}%")

    console.print(config_table)

    if summary["by_level"]:
        level_table = Table(title="预警级别分布")
        level_table.add_column("级别", style="cyan")
        level_table.add_column("数量", style="green")

        level_emoji = {"critical": "🔴", "danger": "🟠", "warning": "🟡", "info": "🔵"}
        for level, count in summary["by_level"].items():
            emoji = level_emoji.get(level, "⚪")
            level_table.add_row(f"{emoji} {level}", str(count))

        console.print(level_table)

    if summary["by_type"]:
        type_table = Table(title="预警类型分布")
        type_table.add_column("类型", style="cyan")
        type_table.add_column("数量", style="green")

        for type_, count in summary["by_type"].items():
            type_table.add_row(type_, str(count))

        console.print(type_table)


@risk.command()
@click.option("--hours", default=24, help="显示最近N小时的预警")
def alerts(hours):
    """显示最近的预警列表"""
    from asset_lens.monitoring.risk_alert import risk_alert_system

    active_alerts = risk_alert_system.get_active_alerts(hours)

    if not active_alerts:
        console.print(f"[green]✅ 最近 {hours} 小时内没有预警[/green]")
        return

    console.print(f"[bold yellow]最近 {hours} 小时内有 {len(active_alerts)} 条预警[/bold yellow]")

    table = Table(show_header=True)
    table.add_column("时间", style="dim")
    table.add_column("级别", style="cyan")
    table.add_column("类型", style="yellow")
    table.add_column("标题", style="white")
    table.add_column("建议", style="green")

    level_emoji = {"critical": "🔴", "danger": "🟠", "warning": "🟡", "info": "🔵"}

    for alert in active_alerts:
        emoji = level_emoji.get(alert.level.value, "⚪")
        table.add_row(
            alert.timestamp,
            f"{emoji} {alert.level.value}",
            alert.type.value,
            alert.title,
            alert.suggestion[:30] + "..." if len(alert.suggestion) > 30 else alert.suggestion,
        )

    console.print(table)


@risk.command()
def report():
    """生成风险预警报告"""
    from asset_lens.monitoring.risk_alert import risk_alert_system

    report_text = risk_alert_system.generate_alert_report()
    console.print(report_text)


@risk.command()
def check():
    """运行风险检查（基于当前投资组合）"""
    from asset_lens.data.csv_parser import CSVParser
    from asset_lens.monitoring.risk_alert import risk_alert_system
    from asset_lens.monitoring.risk_analyzer import RiskAnalyzer

    console.print("[bold blue]🔍 运行风险检查...[/bold blue]")

    try:
        parser = CSVParser()
        products = parser.load_data()

        if not products:
            console.print("[yellow]⚠️ 没有找到投资组合数据[/yellow]")
            return

        holdings = {}
        stocks = []
        total_value: float = 0.0
        cash_value: float = 0.0

        for product in products:
            current_value = float(product.current_amount or product.total_amount or 0)
            if current_value > 0:
                code = product.code if hasattr(product, "code") else (product.name or "unknown")
                holdings[code] = current_value
                total_value += current_value

                # 统计现金类资产和中低风险资产
                if hasattr(product, "investment_type"):
                    from asset_lens.data.models import InvestmentType
                    # 中低风险资产（不计入仓位）
                    low_risk_types = [
                        InvestmentType.CASH,
                        InvestmentType.HK_CASH,
                        InvestmentType.MONETARY,
                        InvestmentType.WEALTH,
                        InvestmentType.HIGH_END_WEALTH,
                        InvestmentType.BROKER_WEALTH,
                        InvestmentType.PUBLIC_FIXED_INCOME,
                        InvestmentType.FIXED_DEPOSIT,
                        InvestmentType.BOND,
                        InvestmentType.SPECIAL_TREASURY_BOND,
                    ]
                    if product.investment_type in low_risk_types:
                        cash_value += current_value

                cost = float(product.initial_amount or 0)
                if cost > 0:
                    change_percent = (current_value - cost) / cost * 100 if cost > 0 else 0
                    stocks.append(
                        {
                            "code": code,
                            "cost_price": cost,
                            "current_price": current_value,
                            "change_percent": change_percent,
                        }
                    )

        # 计算仓位：投资金额 / 总资产
        invested_value = total_value - cash_value
        position = (invested_value / total_value * 100) if total_value > 0 else 0

        portfolio_data = {
            "holdings": holdings,
            "position": position,
            "stocks": stocks,
        }

        analyzer = RiskAnalyzer()

        returns = [stock.get("change_percent", 0) / 100 for stock in stocks]

        if returns:
            volatility = analyzer.calculate_volatility(returns)
            portfolio_data["volatility"] = volatility

        alerts = risk_alert_system.run_all_checks(portfolio_data)

        if alerts:
            console.print(f"\n[bold yellow]发现 {len(alerts)} 条预警:[/bold yellow]")

            level_emoji = {"critical": "🔴", "danger": "🟠", "warning": "🟡", "info": "🔵"}

            for alert in alerts:
                emoji = level_emoji.get(alert.level.value, "⚪")
                console.print(f"\n{emoji} [{alert.type.value}] {alert.title}")
                console.print(f"   {alert.message}")
                console.print(f"   [green]建议: {alert.suggestion}[/green]")
        else:
            console.print("\n[green]✅ 风险检查通过，没有发现预警[/green]")

        console.print("\n[dim]检查项目: 最大回撤、波动率、集中度、止损止盈[/dim]")

    except Exception as e:
        console.print(f"[red]❌ 风险检查失败: {e}[/red]")


@risk.command()
@click.option("--max-drawdown", type=float, help="最大回撤阈值 (%)")
@click.option("--volatility", type=float, help="波动率阈值 (%)")
@click.option("--concentration", type=float, help="集中度阈值 (%)")
@click.option("--stop-loss", type=float, help="止损线 (%)")
@click.option("--take-profit", type=float, help="止盈线 (%)")
def config(max_drawdown, volatility, concentration, stop_loss, take_profit):
    """配置风险预警阈值"""
    from asset_lens.monitoring.risk_alert import risk_alert_system

    current_config = risk_alert_system.config

    if max_drawdown is not None:
        current_config.max_drawdown_threshold = max_drawdown
        console.print(f"[green]✅ 最大回撤阈值已设置为: {max_drawdown}%[/green]")

    if volatility is not None:
        current_config.volatility_threshold = volatility
        console.print(f"[green]✅ 波动率阈值已设置为: {volatility}%[/green]")

    if concentration is not None:
        current_config.concentration_threshold = concentration
        console.print(f"[green]✅ 集中度阈值已设置为: {concentration}%[/green]")

    if stop_loss is not None:
        current_config.stop_loss_percent = stop_loss
        console.print(f"[green]✅ 止损线已设置为: {stop_loss}%[/green]")

    if take_profit is not None:
        current_config.take_profit_percent = take_profit
        console.print(f"[green]✅ 止盈线已设置为: {take_profit}%[/green]")

    if not any([max_drawdown, volatility, concentration, stop_loss, take_profit]):
        console.print("[yellow]当前配置:[/yellow]")
        console.print(f"  最大回撤阈值: {current_config.max_drawdown_threshold}%")
        console.print(f"  波动率阈值: {current_config.volatility_threshold}%")
        console.print(f"  集中度阈值: {current_config.concentration_threshold}%")
        console.print(f"  止损线: {current_config.stop_loss_percent}%")
        console.print(f"  止盈线: {current_config.take_profit_percent}%")
        console.print("\n[dim]使用 --max-drawdown 等参数修改配置[/dim]")


@risk.command()
def clear():
    """清除所有预警"""
    from asset_lens.monitoring.risk_alert import risk_alert_system

    risk_alert_system.clear_alerts()
    console.print("[green]✅ 已清除所有预警[/green]")


def register_risk_commands(cli: click.Group) -> None:
    """注册风险预警命令到 CLI 组"""
    cli.add_command(risk)
