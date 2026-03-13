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


def add_stocks_to_pool_by_strategy(
    strategy_name: str,
    stocks: list = None,
    min_score: float = 60.0,
    max_stocks: int = 10,
    auto_remove: bool = False,
):
    """根据策略筛选股票并添加到股票池"""
    from ..data.stock_pool import StockPool
    from ..data.strategy_engine import StrategyEngine

    pool = StockPool()
    engine = StrategyEngine()

    click.echo(f"\n📊 策略选股入池: {strategy_name}")
    click.echo("=" * 60)

    # 如果没有提供股票列表，尝试获取市场股票
    if not stocks:
        click.echo("  ⚠️  未提供股票列表，请先获取股票数据")
        click.echo("  💡 使用 'make screen-stocks' 获取股票数据")
        return

    try:
        result = pool.add_stocks_by_strategy(
            strategy_name=strategy_name,
            stocks=stocks,
            min_score=min_score,
            max_stocks=max_stocks,
            auto_remove_low_score=auto_remove,
        )

        click.echo(f"\n  ✅ 筛选完成:")
        click.echo(f"     - 符合条件: {result['total_screened']} 只")
        click.echo(f"     - 新增入池: {result['added']} 只")
        click.echo(f"     - 更新评分: {result['updated']} 只")
        if result['removed'] > 0:
            click.echo(f"     - 移除低分: {result['removed']} 只")

        if result['stocks_added']:
            click.echo(f"\n  📈 入池股票:")
            for stock in result['stocks_added'][:10]:
                click.echo(f"     - {stock['code']} {stock['name']} (评分: {stock['score']:.1f})")

    except Exception as e:
        click.echo(f"  ❌ 选股入池失败: {e}")

    click.echo("=" * 60)


def show_strategy_pool_status(strategy_name: str):
    """显示股票池中某策略的股票状态"""
    from ..data.stock_pool import StockPool

    pool = StockPool()

    click.echo(f"\n📊 股票池策略状态: {strategy_name}")
    click.echo("=" * 60)

    try:
        stocks = pool.get_strategy_top_stocks(strategy_name, top_n=20)

        if stocks:
            click.echo(f"\n  {'代码':<12} {'名称':<10} {'状态':<8} {'评分':<8} {'收益率':<10}")
            click.echo("  " + "-" * 50)

            for stock in stocks:
                code = stock.get("code", "")
                name = stock.get("name", "")
                status = stock.get("status", "")
                score = stock.get("strategy_score", 0)
                profit_rate = stock.get("profit_rate", 0)

                click.echo(
                    f"  {code:<12} {name:<10} {status:<8} {score:<8.1f} {profit_rate:+.2f}%"
                )
        else:
            click.echo("  股票池中暂无该策略选入的股票")

    except Exception as e:
        click.echo(f"  ❌ 获取状态失败: {e}")

    click.echo("=" * 60)


def clear_strategy_from_pool(strategy_name: str):
    """清除股票池中某策略选入的股票"""
    from ..data.stock_pool import StockPool

    pool = StockPool()

    click.echo(f"\n🗑️  清除策略股票: {strategy_name}")
    click.echo("=" * 60)

    try:
        result = pool.clear_strategy_stocks(strategy_name)

        click.echo(f"  ✅ 已移除 {result['removed_count']} 只股票")

        if result['removed_codes']:
            click.echo(f"\n  移除的股票:")
            for code in result['removed_codes'][:10]:
                click.echo(f"     - {code}")

    except Exception as e:
        click.echo(f"  ❌ 清除失败: {e}")

    click.echo("=" * 60)
