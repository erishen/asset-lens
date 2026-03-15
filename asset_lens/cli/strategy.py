"""
Strategy CLI commands for asset-lens.
策略命令模块 - 包含 strategy, backtest, screen-stocks, filter-stocks, volume-breakout, momentum-screen, optimize-strategy
"""

from pathlib import Path
from typing import Optional

import click


def register_strategy_commands(cli: click.Group) -> None:
    """注册策略命令到 CLI 组"""
    
    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--strategy-name", type=str, help="策略名称")
    def strategy(data_mode: Optional[str], strategy_name: Optional[str]):
        """运行投资策略"""
        from asset_lens.config import config
        from asset_lens.strategy.engine import StrategyEngine

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 运行投资策略")
        click.echo("=" * 60)

        try:
            engine = StrategyEngine()
            if strategy_name:
                result = engine.execute(strategy_name)
                click.echo(f"✅ 策略 {strategy_name} 执行完成")
            else:
                strategies = engine.get_available_strategies()
                click.echo("可用策略:")
                for s in strategies:
                    click.echo(f"  - {s}")

        except Exception as e:
            click.echo(f"❌ 执行失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, required=True, help="策略名称")
    @click.option("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    @click.option("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    def backtest(strategy: str, start_date: Optional[str], end_date: Optional[str]):
        """运行策略回测"""
        from asset_lens.strategy.backtester import Backtester

        click.echo("\n📊 策略回测")
        click.echo("=" * 60)

        try:
            backtester = Backtester()
            result = backtester.backtest(
                strategy_name=strategy,
                start_date=start_date,
                end_date=end_date,
            )

            click.echo(f"\n📈 回测结果:")
            click.echo(f"  总收益率: {result.total_return:.2f}%")
            click.echo(f"  年化收益率: {result.annual_return:.2f}%")
            click.echo(f"  最大回撤: {result.max_drawdown:.2f}%")
            click.echo(f"  夏普比率: {result.sharpe_ratio:.2f}")

            click.echo(f"\n✅ 回测完成！")

        except Exception as e:
            click.echo(f"❌ 回测失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, default="momentum", help="筛选策略")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def screen_stocks(strategy: str, limit: int):
        """筛选股票"""
        from asset_lens.strategy.stock_screener import StockScreener

        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        try:
            screener = StockScreener()
            result = screener.screen(strategy=strategy, limit=limit)

            click.echo(f"\n📈 筛选结果 ({len(result)} 只股票):")
            for stock in result[:20]:
                click.echo(f"  {stock.code} - {stock.name} ({stock.score:.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command("filter-stocks")
    @click.option("--config-file", type=click.Path(), help="筛选配置文件路径")
    @click.option("--stocks-file", type=click.Path(), help="股票数据文件路径")
    @click.option("--fetch-market", is_flag=True, help="从市场获取股票列表")
    @click.option("--max-pages", type=int, default=5, help="获取市场股票的最大页数")
    def filter_stocks(config_file: Optional[str], stocks_file: Optional[str], fetch_market: bool, max_pages: int):
        """筛选股票"""
        from asset_lens.strategy.stock_filter import StockFilter

        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        config_path = Path(config_file) if config_file else None
        stock_filter = StockFilter(config_path)

        click.echo(stock_filter.get_filter_summary())
        click.echo("")

        if fetch_market:
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher

            click.echo("📡 正在从市场获取股票列表...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=max_pages)

            if stocks:
                market_stock_fetcher.save_market_stocks(stocks)

        click.echo(f"\n✅ 筛选完成！")

    @cli.command()
    @click.option("--min-volume-ratio", type=float, default=2.0, help="最小成交量比率")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def volume_breakout(min_volume_ratio: float, limit: int):
        """成交量突破筛选"""
        from asset_lens.strategy.volume_breakout import volume_breakout_filter

        click.echo("\n📊 成交量突破筛选")
        click.echo("=" * 60)

        try:
            result = volume_breakout_filter.filter(
                min_volume_ratio=min_volume_ratio,
                limit=limit,
            )

            click.echo(f"\n📈 筛选结果 ({len(result)} 只股票):")
            for stock in result[:20]:
                click.echo(f"  {stock.get('code')} - {stock.get('name')} (成交量比率: {stock.get('volume_ratio', 0):.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--min-momentum", type=float, default=0.05, help="最小动量得分")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def momentum_screen(min_momentum: float, limit: int):
        """动量选股"""
        from asset_lens.strategy.momentum import momentum_screener

        click.echo("\n📊 动量选股")
        click.echo("=" * 60)

        try:
            result = momentum_screener.screen(
                min_momentum=min_momentum,
                limit=limit,
            )

            click.echo(f"\n📈 筛选结果 ({len(result)} 只股票):")
            for stock in result[:20]:
                click.echo(f"  {stock.get('code')} - {stock.get('name')} (动量: {stock.get('momentum', 0):.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def optimize_strategy(data_mode: Optional[str]):
        """优化策略参数"""
        from asset_lens.config import config
        from asset_lens.strategy.optimizer import StrategyOptimizer

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 策略优化")
        click.echo("=" * 60)

        try:
            optimizer = StrategyOptimizer()
            result = optimizer.optimize()

            click.echo(f"\n📈 优化结果:")
            click.echo(f"  最佳参数: {result.best_params}")
            click.echo(f"  最佳得分: {result.best_score:.2f}")

            click.echo(f"\n✅ 优化完成！")

        except Exception as e:
            click.echo(f"❌ 优化失败: {e}", err=True)
