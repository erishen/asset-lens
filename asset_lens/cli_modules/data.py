"""
CLI Data Commands.
CLI 数据命令
"""

import click
from typing import Optional


def fetch_stock_data(codes: str, data_mode: Optional[str] = None):
    """获取股票行情数据"""
    from ..data.stock_fetcher import StockDataFetcher

    fetcher = StockDataFetcher()
    code_list = codes.split()

    click.echo(f"\n📈 获取股票行情...")
    click.echo("=" * 60)

    for code in code_list:
        try:
            data = fetcher.fetch_stock_quote_akshare(code)
            if data:
                click.echo(f"  ✅ {code}: ¥{data.get('current_price', 0):.2f}")
            else:
                click.echo(f"  ❌ {code}: 获取失败")
        except Exception as e:
            click.echo(f"  ❌ {code}: {e}")

    click.echo("=" * 60)


def fetch_fund_data(codes: str, data_mode: Optional[str] = None):
    """获取基金净值数据"""
    from ..data.fund_fetcher import FundDataFetcher

    fetcher = FundDataFetcher()
    code_list = codes.split()

    click.echo(f"\n📊 获取基金净值...")
    click.echo("=" * 60)

    for code in code_list:
        try:
            data = fetcher.fetch_fund_quote_akshare(code)
            if data:
                click.echo(f"  ✅ {code}: ¥{data.get('net_value', 0):.4f}")
            else:
                click.echo(f"  ❌ {code}: 获取失败")
        except Exception as e:
            click.echo(f"  ❌ {code}: {e}")

    click.echo("=" * 60)


def search_fund_data(keyword: str):
    """搜索基金"""
    from ..data.fund_fetcher import FundDataFetcher

    fetcher = FundDataFetcher()

    click.echo(f"\n🔍 搜索基金: {keyword}")
    click.echo("=" * 60)

    try:
        results = fetcher.search_fund(keyword)
        if results:
            for fund in results[:10]:
                click.echo(f"  {fund.get('code', '')} - {fund.get('name', '')}")
        else:
            click.echo("  未找到匹配的基金")
    except Exception as e:
        click.echo(f"  ❌ 搜索失败: {e}")

    click.echo("=" * 60)


def update_market_data(api: str = "eastmoney"):
    """更新市场数据"""
    from ..data.market_data_fetcher import MarketDataFetcher

    fetcher = MarketDataFetcher()

    click.echo(f"\n🌍 更新市场数据（数据源: {api}）...")
    click.echo("=" * 60)

    try:
        if api == "finnhub":
            data = fetcher.fetch_all_foreign_indexes()
            click.echo(f"  ✅ 更新了 {len(data)} 个国外指数")
        else:
            data = fetcher.fetch_all_domestic_indexes()
            click.echo(f"  ✅ 更新了 {len(data)} 个国内指数")
    except Exception as e:
        click.echo(f"  ❌ 更新失败: {e}")

    click.echo("=" * 60)


def update_all_data():
    """更新所有数据"""
    from ..data.csv_parser import CSVParser
    from ..data.market_data_fetcher import MarketDataFetcher
    from ..data.fund_fetcher import FundDataFetcher
    from ..data.stock_fetcher import StockDataFetcher

    click.echo(f"\n🔄 更新所有数据...")
    click.echo("=" * 60)

    # 更新市场数据
    try:
        fetcher = MarketDataFetcher()
        domestic = fetcher.fetch_all_domestic_indexes()
        foreign = fetcher.fetch_all_foreign_indexes()
        click.echo(f"  ✅ 市场数据: 国内 {len(domestic)} 个, 国外 {len(foreign)} 个")
    except Exception as e:
        click.echo(f"  ❌ 市场数据更新失败: {e}")

    # 更新基金净值
    try:
        products = CSVParser.load_data()
        fund_codes = [getattr(p, 'name', '') for p in products if getattr(p, 'investment_type', None) and getattr(p, 'investment_type').value == "基金"]
        if fund_codes:
            fund_fetcher = FundDataFetcher()
            updated = 0
            for code in fund_codes[:20]:  # 限制数量
                try:
                    data = fund_fetcher.fetch_fund_quote_akshare(code)
                    if data:
                        updated += 1
                except Exception:
                    pass
            click.echo(f"  ✅ 基金净值: 更新了 {updated} 只")
    except Exception as e:
        click.echo(f"  ❌ 基金净值更新失败: {e}")

    click.echo("=" * 60)
