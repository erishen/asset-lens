"""
CLI Analysis Commands.
CLI 分析命令
"""

import click
from typing import Optional, Dict


def analyze_portfolio(data_mode: Optional[str] = None):
    """分析投资组合"""
    from ..data.csv_parser import CSVParser
    from ..config import config

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n📊 投资组合分析")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        if not products:
            click.echo("  未找到投资数据")
            return

        total_amount: float = 0.0
        by_type: Dict[str, float] = {}
        by_platform: Dict[str, float] = {}

        for product in products:
            amount = float(getattr(product, 'current_amount', 0) or 0)
            total_amount += amount

            ptype = getattr(product, 'investment_type', None)
            ptype_str = ptype.value if ptype else "未知"
            by_type[ptype_str] = by_type.get(ptype_str, 0) + amount

            platform = getattr(product, 'platform', '未知') or "未知"
            by_platform[platform] = by_platform.get(platform, 0) + amount

        click.echo(f"  总金额: ¥{total_amount:,.2f}")
        click.echo("")
        click.echo("  按类型:")
        for ptype, amount in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            pct = (amount / total_amount * 100) if total_amount > 0 else 0
            click.echo(f"    {ptype}: ¥{amount:,.2f} ({pct:.1f}%)")

        click.echo("")
        click.echo("  按平台:")
        for platform, amount in sorted(by_platform.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (amount / total_amount * 100) if total_amount > 0 else 0
            click.echo(f"    {platform}: ¥{amount:,.2f} ({pct:.1f}%)")

    except Exception as e:
        click.echo(f"  ❌ 分析失败: {e}")

    click.echo("=" * 60)


def calculate_returns(data_mode: Optional[str] = None):
    """计算收益率"""
    from ..data.csv_parser import CSVParser
    from ..config import config

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n💰 收益率计算")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        if not products:
            click.echo("  未找到投资数据")
            return

        total_cost: float = 0.0
        total_current: float = 0.0

        for product in products:
            cost = float(getattr(product, 'cost', 0) or 0)
            amount = float(getattr(product, 'amount', 0) or 0)
            total_cost += cost
            total_current += amount

        profit = total_current - total_cost
        return_rate = (profit / total_cost * 100) if total_cost > 0 else 0

        click.echo(f"  总成本: ¥{total_cost:,.2f}")
        click.echo(f"  当前价值: ¥{total_current:,.2f}")
        click.echo(f"  收益: ¥{profit:,.2f}")
        click.echo(f"  收益率: {return_rate:.2f}%")

    except Exception as e:
        click.echo(f"  ❌ 计算失败: {e}")

    click.echo("=" * 60)


def show_pnl(data_mode: Optional[str] = None):
    """显示盈亏明细"""
    from ..data.csv_parser import CSVParser
    from ..config import config

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n📊 盈亏明细")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        if not products:
            click.echo("  未找到投资数据")
            return

        for product in products[:20]:
            name = product.name or getattr(product, 'code', '未知') or "未知"
            cost = float(getattr(product, 'cost', 0) or 0)
            amount = float(getattr(product, 'amount', 0) or 0)
            profit = amount - cost
            return_rate = (profit / cost * 100) if cost > 0 else 0

            status = "✅" if profit >= 0 else "❌"
            click.echo(f"  {status} {name}: ¥{profit:,.2f} ({return_rate:.1f}%)")

        if len(products) > 20:
            click.echo(f"  ... 还有 {len(products) - 20} 个产品")

    except Exception as e:
        click.echo(f"  ❌ 获取失败: {e}")

    click.echo("=" * 60)


def calculate_irr(data_mode: Optional[str] = None):
    """计算内部收益率"""
    from ..core.irr_calculator import IRRCalculator
    from ..config import config

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n📈 内部收益率计算")
    click.echo("=" * 60)

    try:
        calculator = IRRCalculator()
        irr = calculator.calculate_irr([])

        if irr is not None:
            click.echo(f"  内部收益率 (IRR): {irr:.2f}%")
        else:
            click.echo("  无法计算 IRR")

    except Exception as e:
        click.echo(f"  ❌ 计算失败: {e}")

    click.echo("=" * 60)


def estimate_returns(data_mode: Optional[str] = None):
    """估算收益"""
    from ..data.csv_parser import CSVParser
    from ..data.market_data_fetcher import MarketDataFetcher
    from ..config import config

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n📊 收益估算")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        if not products:
            click.echo("  未找到投资数据")
            return

        fetcher = MarketDataFetcher()
        total_estimated: float = 0.0

        for product in products[:10]:
            name = product.name or getattr(product, 'name', '') or "未知"
            amount = float(getattr(product, 'current_amount', 0) or 0)

            # 简单估算
            change = 0.0
            product_code = getattr(product, 'name', None)
            if product_code:
                from ..data.fund_fetcher import FundDataFetcher
                fund_fetcher = FundDataFetcher()
                fund_data = fund_fetcher.fetch_fund_quote_akshare(product_code)
                if fund_data:
                    change = float(fund_data.get('change_percent', 0) or 0)
            estimated_change = amount * change / 100
            total_estimated += estimated_change

            click.echo(f"  {name}: ¥{amount:,.2f} ({change:+.2f}%)")

        click.echo(f"\n  预估总变动: ¥{total_estimated:,.2f}")

    except Exception as e:
        click.echo(f"  ❌ 估算失败: {e}")

    click.echo("=" * 60)


def show_market_sentiment():
    """显示市场风向"""
    from ..data.market_environment import market_environment_analyzer

    click.echo(f"\n🌡️ 市场风向")
    click.echo("=" * 60)

    try:
        env = market_environment_analyzer.analyze_environment()
        if env:
            click.echo(f"  市场类型: {env.market_type}")
            click.echo(f"  市场情绪: {env.sentiment}")
            click.echo(f"  风险等级: {env.risk_level}")
        else:
            click.echo("  无法获取市场环境")

    except Exception as e:
        click.echo(f"  ❌ 获取失败: {e}")

    click.echo("=" * 60)
