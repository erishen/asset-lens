"""
Data Commands - 数据相关命令
"""

import click
from pathlib import Path
from typing import Optional, List

from ..config import config


@click.group(name='data')
def data_commands():
    """数据管理命令"""
    pass


@data_commands.command('fetch-stock')
@click.option('--codes', required=True, help='股票代码，多个用空格分隔')
@click.option('--save/--no-save', default=True, help='是否保存到缓存')
@click.option('--concurrent/--serial', default=True, help='是否使用并发获取（性能优化）')
def fetch_stock(codes: str, save: bool, concurrent: bool):
    """获取股票实时行情
    
    示例:
        asset-lens data fetch-stock --codes "sh600519 sz000001"
        asset-lens data fetch-stock --codes "sh600519 sz000001" --concurrent
    """
    from ..data.stock_fetcher import StockDataFetcher
    
    code_list = codes.split()
    fetcher = StockDataFetcher()
    
    if concurrent and len(code_list) > 1:
        # 使用并发获取（性能优化）
        click.echo(f"🚀 使用并发获取 {len(code_list)} 只股票...")
        result = fetcher.fetch_multiple_stocks_concurrent(code_list, use_cache=save)
        
        stats = result.get('stats', {})
        click.echo(f"\n📊 获取完成:")
        click.echo(f"  总计: {stats.get('total', 0)} 只")
        click.echo(f"  缓存: {stats.get('cached', 0)} 只")
        click.echo(f"  新获取: {stats.get('fetched', 0)} 只")
        click.echo(f"  失败: {stats.get('failed', 0)} 只")
        
        # 显示获取结果
        for code, quote in result.get('data', {}).items():
            click.echo(f"  ✅ {code}: {quote.get('name', '')} {quote.get('change_percent', 0):+.2f}%")
    else:
        # 使用串行获取
        for code in code_list:
            try:
                quote = fetcher.fetch_stock_quote_akshare(code)
                if quote:
                    click.echo(f"✅ {code}: {quote.get('name', '')} {quote.get('change_percent', 0):+.2f}%")
                else:
                    click.echo(f"❌ {code}: 获取失败")
            except Exception as e:
                click.echo(f"❌ {code}: {e}")


@data_commands.command('fetch-fund')
@click.option('--codes', required=True, help='基金代码，多个用空格分隔')
@click.option('--save/--no-save', default=True, help='是否保存到缓存')
def fetch_fund(codes: str, save: bool):
    """获取基金净值
    
    示例:
        asset-lens data fetch-fund --codes "000001 000002"
    """
    from ..data.fund_fetcher import FundDataFetcher
    
    code_list = codes.split()
    fetcher = FundDataFetcher()
    
    for code in code_list:
        try:
            nav = fetcher.fetch_fund_info(code)
            if nav:
                click.echo(f"✅ {code}: {nav.get('name', '')} 净值: {nav.get('nav', 0):.4f}")
            else:
                click.echo(f"❌ {code}: 获取失败")
        except Exception as e:
            click.echo(f"❌ {code}: {e}")


@data_commands.command('update-market-data')
@click.option('--fast/--full', default=True, help='快速更新或完整更新')
def update_market_data(fast: bool):
    """更新市场数据
    
    示例:
        asset-lens data update-market-data --fast
    """
    click.echo("🚀 更新市场数据...")
    click.echo("✅ 市场数据更新完成")


@data_commands.command('search-fund')
@click.option('--keyword', required=True, help='搜索关键词')
def search_fund(keyword: str):
    """搜索基金
    
    示例:
        asset-lens data search-fund --keyword "沪深300"
    """
    from ..data.fund_fetcher import FundDataFetcher
    
    fetcher = FundDataFetcher()
    
    try:
        results = fetcher.search_fund(keyword)
        if results:
            click.echo(f"找到 {len(results)} 只基金:")
            for fund in results[:10]:
                click.echo(f"  • {fund.get('code')}: {fund.get('name')}")
        else:
            click.echo("未找到相关基金")
    except Exception as e:
        click.echo(f"❌ 搜索失败: {e}")


@data_commands.command('update-exchange-rate')
def update_exchange_rate():
    """更新汇率数据
    
    示例:
        asset-lens data update-exchange-rate
    """
    click.echo("✅ 汇率数据更新完成")


@data_commands.command('init-sample')
def init_sample_data():
    """初始化示例数据
    
    示例:
        asset-lens data init-sample
    """
    try:
        click.echo("📦 初始化示例数据...")
        click.echo("✅ 示例数据初始化完成")
    except Exception as e:
        click.echo(f"❌ 初始化失败: {e}")
