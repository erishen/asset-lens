"""
CLI Strategy Commands.
CLI 策略命令
"""

import click
from typing import Optional


def list_strategies():
    """列出所有策略"""
    from ..data.strategy_engine import StrategyEngine

    engine = StrategyEngine()
    strategies = engine.list_strategies()

    click.echo(f"\n📋 可用策略列表")
    click.echo("=" * 60)

    for strategy in strategies:
        click.echo(f"  {strategy.get('name', '未知')}: {strategy.get('description', '无描述')}")

    click.echo("=" * 60)


def show_strategy(name: str):
    """显示策略详情"""
    from ..data.strategy_engine import StrategyEngine

    engine = StrategyEngine()
    strategy = engine.get_strategy(name)

    if not strategy:
        click.echo(f"❌ 策略不存在: {name}")
        return

    click.echo(f"\n📊 策略详情: {name}")
    click.echo("=" * 60)
    click.echo(f"  名称: {strategy.name}")
    click.echo(f"  描述: {strategy.description}")
    click.echo(f"  买入条件数: {len(strategy.buy_conditions)}")
    click.echo(f"  卖出条件数: {len(strategy.sell_conditions)}")
    click.echo(f"  仓位大小: {strategy.position_size}")
    click.echo(f"  最大持仓: {strategy.max_positions}")
    click.echo(f"  止损: {strategy.stop_loss}")
    click.echo(f"  止盈: {strategy.take_profit}")

    click.echo("=" * 60)


def run_backtest(strategy_name: str, days: int = 365):
    """运行策略回测"""
    from ..data.strategy_engine import StrategyEngine

    engine = StrategyEngine()

    click.echo(f"\n📊 策略回测: {strategy_name}")
    click.echo("=" * 60)

    try:
        result = engine.validate_strategy(strategy_name, {})
        if result and result.get("valid"):
            click.echo(f"  ✅ 策略验证通过")
            click.echo(f"  总收益率: {result.get('total_return', 0):.2f}%")
            click.echo(f"  胜率: {result.get('win_rate', 0):.2f}%")
        else:
            click.echo(f"  ❌ 回测失败: {result.get('reason', '未知原因')}")
    except Exception as e:
        click.echo(f"  ❌ 回测失败: {e}")

    click.echo("=" * 60)


def show_stock_pool(pool_name: Optional[str] = None):
    """显示股票池"""
    from ..data.stock_pool import StockPool

    pool = StockPool()

    click.echo(f"\n📊 股票池状态")
    click.echo("=" * 60)

    try:
        stocks = pool.get_stocks(pool_name)
        if stocks:
            for stock in stocks[:20]:
                click.echo(f"  {stock.get('code', '')} - {stock.get('name', '')} ({stock.get('status', '')})")
            if len(stocks) > 20:
                click.echo(f"  ... 还有 {len(stocks) - 20} 只股票")
        else:
            click.echo("  股票池为空")
    except Exception as e:
        click.echo(f"  ❌ 获取股票池失败: {e}")

    click.echo("=" * 60)


def add_to_stock_pool(code: str, name: Optional[str] = None, status: str = "watching"):
    """添加股票到股票池"""
    from ..data.stock_pool import StockPool

    pool = StockPool()

    try:
        pool.add_stock(code, name=name, status=status)
        click.echo(f"✅ 已添加 {code} 到股票池")
    except Exception as e:
        click.echo(f"❌ 添加失败: {e}")


def remove_from_stock_pool(code: str):
    """从股票池移除股票"""
    from ..data.stock_pool import StockPool

    pool = StockPool()

    try:
        pool.remove_stock(code)
        click.echo(f"✅ 已从股票池移除 {code}")
    except Exception as e:
        click.echo(f"❌ 移除失败: {e}")


def screen_stocks_with_strategy(strategy_name: str, limit: int = 20):
    """使用策略筛选股票"""
    from ..data.strategy_engine import StrategyEngine

    engine = StrategyEngine()

    click.echo(f"\n📊 策略选股: {strategy_name}")
    click.echo("=" * 60)

    try:
        results = engine.screen_stocks([], strategy_name, min_score=60)
        if results:
            for stock in results:
                click.echo(f"  {stock.get('code', '')} - {stock.get('name', '')} (得分: {stock.get('score', 0):.2f})")
        else:
            click.echo("  未找到符合条件的股票")
    except Exception as e:
        click.echo(f"  ❌ 筛选失败: {e}")

    click.echo("=" * 60)
