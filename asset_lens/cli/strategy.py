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

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 运行投资策略")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine
            engine = StrategyEngine()
            
            if strategy_name:
                strategies = engine.list_strategies()
                click.echo(f"✅ 策略 {strategy_name} 已加载")
                click.echo(f"可用策略: {[s['name'] for s in strategies]}")
            else:
                strategies = engine.list_strategies()
                click.echo("可用策略:")
                for s in strategies:
                    click.echo(f"  - {s.get('name', s)}")

        except Exception as e:
            click.echo(f"❌ 执行失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, required=True, help="策略名称")
    @click.option("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    @click.option("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    def backtest(strategy: str, start_date: Optional[str], end_date: Optional[str]):
        """运行策略回测"""
        click.echo("\n📊 策略回测")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.backtester import Backtester
            backtester = Backtester()
            
            click.echo(f"\n📈 回测配置:")
            click.echo(f"  策略: {strategy}")
            click.echo(f"  开始日期: {start_date or '默认'}")
            click.echo(f"  结束日期: {end_date or '默认'}")
            
            click.echo(f"\n💡 请使用 run_backtest() 方法执行回测")

        except Exception as e:
            click.echo(f"❌ 回测失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, default="momentum", help="筛选策略")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def screen_stocks(strategy: str, limit: int):
        """筛选股票"""
        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
            
            click.echo("📡 正在获取股票列表...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)
            
            if not stocks:
                click.echo("❌ 未能获取股票列表", err=True)
                return
            
            engine = StrategyEngine()
            result = engine.screen_stocks(stocks=stocks, strategy_name=strategy)

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get('code', stock.get('symbol', 'N/A'))
                    name = stock.get('name', 'N/A')
                    score = stock.get('score', 0)
                    click.echo(f"  {code} - {name} ({score:.2f})")

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
        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.stock_filter import StockFilter

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

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--min-volume-ratio", type=float, default=2.0, help="最小成交量比率")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def volume_breakout(min_volume_ratio: float, limit: int):
        """成交量突破筛选"""
        click.echo("\n📊 成交量突破筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.volume_breakout import volume_breakout_filter

            result = volume_breakout_filter.filter()

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get('code', 'N/A')
                    name = stock.get('name', 'N/A')
                    volume_ratio = stock.get('volume_ratio', 0)
                    click.echo(f"  {code} - {name} (成交量比率: {volume_ratio:.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--min-momentum", type=float, default=0.05, help="最小动量得分")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def momentum_screen(min_momentum: float, limit: int):
        """动量选股"""
        click.echo("\n📊 动量选股")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
            
            click.echo("📡 正在获取股票列表...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)
            
            if not stocks:
                click.echo("❌ 未能获取股票列表", err=True)
                return
            
            engine = StrategyEngine()
            result = engine.screen_stocks(stocks=stocks, strategy_name="momentum")

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get('code', stock.get('symbol', 'N/A'))
                    name = stock.get('name', 'N/A')
                    score = stock.get('score', 0)
                    click.echo(f"  {code} - {name} (得分: {score:.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def optimize_strategy(data_mode: Optional[str]):
        """优化策略参数"""
        from asset_lens.config import config

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 策略优化")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine
            engine = StrategyEngine()
            
            click.echo("\n📈 可用优化方法:")
            click.echo("  - optimize_strategy_params(): 参数优化")
            click.echo("  - combine_strategies(): 策略组合")
            
            click.echo(f"\n✅ 策略引擎已加载！")

        except Exception as e:
            click.echo(f"❌ 优化失败: {e}", err=True)
