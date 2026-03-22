"""
CLI Interactive Commands.
CLI 交互式命令
"""

import click

from ..config import config


def interactive_analyze():
    """交互式分析投资组合"""
    click.echo("\n📊 投资组合分析")
    click.echo("-" * 40)

    data_mode = click.prompt(
        "选择数据模式",
        type=click.Choice(["sample", "real"]),
        default="sample",
    )

    output_format = click.prompt(
        "选择输出格式",
        type=click.Choice(["console", "csv", "json", "all"]),
        default="console",
    )

    click.echo(f"\n正在分析 {data_mode} 数据...")
    click.echo(f"请运行: make analyze DATA_MODE={data_mode}")


def interactive_calculate():
    """交互式计算收益率"""
    click.echo("\n💰 收益率计算")
    click.echo("-" * 40)

    principal = click.prompt("请输入本金金额", type=click.FLOAT)
    current = click.prompt("请输入当前金额", type=click.FLOAT)
    days = click.prompt("请输入投资天数", type=click.INT, default=365)

    profit = current - principal
    profit_rate = (profit / principal) * 100
    annual_return = (profit_rate / days) * 365 if days > 0 else 0

    click.echo("\n📊 计算结果:")
    click.echo(f"  本金: ¥{principal:,.2f}")
    click.echo(f"  当前: ¥{current:,.2f}")
    click.echo(f"  收益: ¥{profit:,.2f}")
    click.echo(f"  收益率: {profit_rate:.2f}%")
    click.echo(f"  年化收益率: {annual_return:.2f}%")


def interactive_fetch_stock():
    """交互式查询股票行情"""
    click.echo("\n📈 股票行情查询")
    click.echo("-" * 40)

    code = click.prompt("请输入股票代码（如 sh600519）")

    click.echo(f"\n正在查询 {code}...")
    click.echo(f'请运行: make fetch-stock CODES="{code}"')


def interactive_fetch_fund():
    """交互式查询基金净值"""
    click.echo("\n📉 基金净值查询")
    click.echo("-" * 40)

    code = click.prompt("请输入基金代码（如 000001）")

    click.echo(f"\n正在查询 {code}...")
    click.echo(f'请运行: make fetch-fund CODES="{code}"')


def interactive_search_fund():
    """交互式搜索基金"""
    click.echo("\n🔍 基金搜索")
    click.echo("-" * 40)

    keyword = click.prompt("请输入搜索关键词（如 沪深300）")

    click.echo(f"\n正在搜索 '{keyword}'...")
    click.echo(f'请运行: make search-fund KEYWORD="{keyword}"')


def interactive_update_market():
    """交互式更新市场数据"""
    click.echo("\n🌍 市场数据更新")
    click.echo("-" * 40)

    api = click.prompt(
        "选择数据源",
        type=click.Choice(["sina", "eastmoney", "finnhub"]),
        default="eastmoney",
    )

    async_mode = click.confirm("是否使用异步模式", default=True)

    click.echo(f"\n正在更新市场数据（数据源: {api}）...")
    if async_mode:
        click.echo(f"请运行: make update-market-async API={api}")
    else:
        click.echo(f"请运行: make update-market API={api}")


def interactive_report():
    """交互式生成报告"""
    click.echo("\n📝 投资报告生成")
    click.echo("-" * 40)

    report_type = click.prompt(
        "选择报告类型",
        type=click.Choice(["strategy", "pool", "comparison", "risk"]),
        default="strategy",
    )

    click.echo(f"\n正在生成 {report_type} 报告...")
    click.echo(f"请运行: make report-{report_type}")


def interactive_settings():
    """交互式系统设置"""
    click.echo("\n⚙️  系统设置")
    click.echo("-" * 40)

    click.echo("当前设置:")
    click.echo(f"  数据模式: {config.data_mode}")
    click.echo(f"  USD 汇率: {config.default_usd_rate}")
    click.echo(f"  HKD 汇率: {config.default_hkd_rate}")
    click.echo(f"  输出目录: {config.output_path}")

    if click.confirm("\n是否修改设置"):
        click.echo("\n💡 请修改 config/settings.json 文件来更新设置")


def interactive_menu():
    """交互式主菜单"""
    while True:
        click.echo("\n" + "=" * 50)
        click.echo("  asset-lens - 个人资产操作系统")
        click.echo("=" * 50)
        click.echo("\n请选择操作:")
        click.echo("  1. 分析投资组合")
        click.echo("  2. 计算收益率")
        click.echo("  3. 查询股票行情")
        click.echo("  4. 查询基金净值")
        click.echo("  5. 搜索基金")
        click.echo("  6. 更新市场数据")
        click.echo("  7. 生成报告")
        click.echo("  8. 系统设置")
        click.echo("  0. 退出")

        choice = click.prompt("\n请输入选项", type=click.INT, default=0)

        if choice == 1:
            interactive_analyze()
        elif choice == 2:
            interactive_calculate()
        elif choice == 3:
            interactive_fetch_stock()
        elif choice == 4:
            interactive_fetch_fund()
        elif choice == 5:
            interactive_search_fund()
        elif choice == 6:
            interactive_update_market()
        elif choice == 7:
            interactive_report()
        elif choice == 8:
            interactive_settings()
        elif choice == 0:
            click.echo("\n👋 感谢使用，再见！")
            break
        else:
            click.echo("❌ 无效选项，请重新选择")
