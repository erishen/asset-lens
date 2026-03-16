"""
Data CLI commands for asset-lens.
数据管理命令模块 - 包含 fetch-stock, fetch-fund, search-fund, update-market-data, fetch-portfolio-funds, update-all-data
"""

from typing import Optional, Tuple

import click


def register_data_commands(cli: click.Group) -> None:
    """注册数据管理命令到 CLI 组"""
    
    @cli.command()
    @click.argument("codes", nargs=-1, required=True)
    def fetch_stock(codes: Tuple[str, ...]):
        """获取股票实时行情

        示例:
            asset-lens fetch-stock sh600519 sz000001
            asset-lens fetch-stock hk00700
            asset-lens fetch-stock AAPL TSLA
        """
        from asset_lens.data.stock_fetcher import stock_fetcher

        click.echo("\n📊 获取股票实时行情")
        click.echo("=" * 60)

        result = stock_fetcher.fetch_multiple_stocks(list(codes))

        if result.get("data"):
            click.echo(f"\n✅ 成功获取 {len(result['data'])} 只股票行情")
            click.echo(f"📁 数据已缓存到: {stock_fetcher.stock_cache_file}")
        else:
            click.echo("\n❌ 未能获取任何股票行情", err=True)

    @cli.command()
    @click.argument("codes", nargs=-1, required=True)
    def fetch_fund(codes: Tuple[str, ...]):
        """获取基金净值

        示例:
            asset-lens fetch-fund 000001 110022
            asset-lens fetch-fund 519778
        """
        from asset_lens.data.fund_fetcher import fund_fetcher

        click.echo("\n📊 获取基金净值")
        click.echo("=" * 60)

        result = fund_fetcher.fetch_multiple_funds(list(codes))

        if result.get("data"):
            click.echo(f"\n✅ 成功获取 {len(result['data'])} 只基金净值")
            click.echo(f"📁 数据已缓存到: {fund_fetcher.fund_cache_file}")
        else:
            click.echo("\n❌ 未能获取任何基金净值", err=True)

    @cli.command()
    @click.argument("keyword")
    def search_fund(keyword: str):
        """搜索基金

        示例:
            asset-lens search-fund 沪深300
            asset-lens search-fund 易方达
        """
        from asset_lens.data.fund_fetcher import fund_fetcher

        click.echo(f"\n🔍 搜索基金: {keyword}")
        click.echo("=" * 60)

        results = fund_fetcher.search_fund(keyword)

        if results:
            click.echo(f"\n找到 {len(results)} 只基金:\n")
            for fund in results[:20]:
                click.echo(f"  {fund['code']} - {fund['name']} ({fund['type']})")
        else:
            click.echo("\n❌ 未找到相关基金", err=True)

    @cli.command("fetch-portfolio-funds")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def fetch_portfolio_funds(data_mode: Optional[str]):
        """自动获取投资组合中所有基金的净值

        自动匹配基金代码并获取净值
        """
        from asset_lens.config import config
        from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 自动获取投资组合基金净值")
        click.echo("=" * 60)

        result = fetch_portfolio_fund_quotes()

        if result.get("data"):
            click.echo(f"\n✅ 成功获取 {len(result['data'])} 只基金净值")
            click.echo("📁 数据已缓存到: cache/fund_quotes.json")
        else:
            click.echo("\n❌ 未能获取任何基金净值", err=True)

    @cli.command()
    @click.option(
        "--api",
        type=click.Choice(["finnhub", "alphavantage"]),
        default="alphavantage",
        help="选择海外市场数据 API (alphavantage: 完整历史数据, finnhub: 仅实时数据)",
    )
    @click.option("--async", "use_async", is_flag=True, help="使用异步并发获取数据")
    def update_market_data(api: str, use_async: bool):
        """更新市场指数数据

        API 选择说明：
        - alphavantage: 获取完整历史数据（最近一周OHLCV、周期表现、技术状态），免费版25次/天
        - finnhub: 仅获取实时报价数据，免费版60次/分钟

        推荐使用 alphavantage 以获得与 ts-demo 一致的数据格式
        """
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        click.echo("\n📊 更新市场指数数据")
        click.echo("=" * 60)

        if use_async:
            click.echo("🚀 使用增强版数据获取器")

            try:
                domestic_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
                foreign_result = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
                success = bool(domestic_result) and bool(foreign_result)

                if success:
                    click.echo("\n✅ 市场指数数据更新成功！")
                else:
                    click.echo("\n❌ 市场指数数据更新失败！", err=True)

            except Exception as e:
                click.echo(f"❌ 更新失败: {e}", err=True)
        else:
            click.echo("📌 使用增强版数据获取器")
            click.echo("   - 多数据源冗余（AkShare、腾讯财经、东方财富等）")
            click.echo("   - 智能缓存（1小时有效期）")
            click.echo("")

            try:
                domestic_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
                foreign_result = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
                success = bool(domestic_result.get("指数数据")) and bool(foreign_result.get("指数数据"))

                if success:
                    click.echo("\n✅ 市场指数数据更新成功！")
                    click.echo("💡 运行 'make estimate-pnl' 开始估算实时盈亏")
                else:
                    click.echo("\n❌ 市场指数数据更新失败！", err=True)
                    click.echo("💡 请检查网络连接或稍后重试")

            except Exception as e:
                click.echo(f"❌ 更新失败: {e}", err=True)

    @cli.command("update-all-data")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def update_all_data(data_mode: Optional[str]):
        """更新所有数据（市场指数、基金净值、股票行情）

        一键更新所有需要的数据
        """
        from asset_lens.config import config
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher
        from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes
        from asset_lens.data.stock_fetcher import stock_fetcher

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 更新所有数据")
        click.echo("=" * 60)

        click.echo("\n1️⃣ 更新市场指数数据...")
        try:
            domestic_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            foreign_result = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
            if domestic_result and foreign_result:
                click.echo("   ✅ 市场指数数据更新成功")
            else:
                click.echo("   ⚠️  市场指数数据部分更新失败")
        except Exception as e:
            click.echo(f"   ❌ 市场指数数据更新失败: {e}")

        click.echo("\n2️⃣ 更新基金净值数据...")
        try:
            result = fetch_portfolio_fund_quotes()
            if result.get("data"):
                click.echo(f"   ✅ 成功获取 {len(result['data'])} 只基金净值")
            else:
                click.echo("   ⚠️  未能获取基金净值数据")
        except Exception as e:
            click.echo(f"   ❌ 基金净值数据更新失败: {e}")

        click.echo("\n3️⃣ 更新股票行情数据...")
        try:
            stock_codes_map = stock_fetcher._load_stock_codes_config()
            stock_codes = list(set(stock_codes_map.values()))
            if stock_codes:
                result = stock_fetcher.fetch_multiple_stocks(stock_codes)
                if result.get("data"):
                    click.echo(f"   ✅ 成功获取 {len(result['data'])} 只股票行情")
                else:
                    click.echo("   ⚠️  未能获取股票行情数据")
            else:
                click.echo("   ℹ️  没有配置股票代码，跳过")
        except Exception as e:
            click.echo(f"   ❌ 股票行情数据更新失败: {e}")

        click.echo("\n✅ 所有数据更新完成！")
        click.echo("💡 运行 'make pnl' 查看更准确的盈亏估算")

    @cli.command("provider-info")
    def provider_info():
        """显示数据源信息（Provider Registry）"""
        from asset_lens.data.unified_data_fetcher import unified_data_fetcher

        click.echo("\n📊 数据源信息（Provider Registry）")
        click.echo("=" * 60)

        info = unified_data_fetcher.get_provider_info()
        
        if info:
            click.echo("\n可用数据源:")
            for data_type, providers in info.items():
                click.echo(f"  {data_type}: {', '.join(providers)}")
        else:
            click.echo("\n⚠️ 没有可用的数据源")

        click.echo("\n💡 使用 Provider Registry 自动选择最佳数据源")

    @cli.command("fetch-unified")
    @click.option("--type", "data_type", type=click.Choice(["stock_cn", "stock_us", "fund_cn", "index"]), required=True, help="数据类型")
    @click.argument("symbol")
    def fetch_unified(data_type: str, symbol: str):
        """使用 Provider Registry 获取数据

        示例:
            asset-lens fetch-unified --type stock_cn 600519
            asset-lens fetch-unified --type fund_cn 000001
            asset-lens fetch-unified --type stock_us AAPL
        """
        from asset_lens.data.unified_data_fetcher import unified_data_fetcher
        from asset_lens.data.providers import DataType

        click.echo(f"\n📊 获取 {data_type} 数据: {symbol}")
        click.echo("=" * 60)

        type_map = {
            "stock_cn": DataType.STOCK_CN,
            "stock_us": DataType.STOCK_US,
            "fund_cn": DataType.FUND_CN,
            "index": DataType.INDEX,
        }

        result = unified_data_fetcher.fetch(type_map[data_type], symbol)

        if result:
            click.echo(f"\n✅ 成功获取数据:")
            for key, value in result.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo(f"\n❌ 未能获取数据", err=True)

    @cli.command("provider-health")
    @click.option("--provider", "provider_name", default=None, help="指定数据源名称")
    @click.option("--json", "output_json", is_flag=True, help="输出 JSON 格式")
    def provider_health(provider_name: Optional[str], output_json: bool):
        """显示数据源健康状态

        示例:
            asset-lens provider-health
            asset-lens provider-health --provider akshare
            asset-lens provider-health --json
        """
        from asset_lens.data.providers import provider_registry
        from rich.console import Console
        from rich.table import Table

        if provider_name:
            health_data = provider_registry.get_health(provider_name)
        else:
            health_data = provider_registry.get_health()

        if not health_data:
            click.echo("\n⚠️ 没有注册的数据源")
            return

        if output_json:
            import json
            output = {name: h.to_dict() for name, h in health_data.items()}
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
            return

        console = Console()

        click.echo("\n📊 数据源健康状态")
        click.echo("=" * 60)

        table = Table(title="Provider Health")
        table.add_column("数据源", style="cyan")
        table.add_column("类型", style="blue")
        table.add_column("状态", style="green")
        table.add_column("成功率", style="yellow")
        table.add_column("平均响应", style="magenta")
        table.add_column("总请求", style="white")

        for name, health in health_data.items():
            status = "✅ 可用" if health.is_available else "❌ 不可用"
            success_rate = f"{health.success_rate * 100:.1f}%"
            avg_time = f"{health.avg_response_time * 1000:.0f}ms" if health.avg_response_time > 0 else "-"
            total = str(health.total_requests)

            table.add_row(
                name,
                health.provider_type,
                status,
                success_rate,
                avg_time,
                total,
            )

        console.print(table)

        summary = provider_registry.get_health_summary()
        click.echo(f"\n📈 汇总:")
        click.echo(f"   总数据源: {summary['total_providers']}")
        click.echo(f"   可用数据源: {summary['available_providers']}")
        click.echo(f"   整体成功率: {summary['overall_success_rate']}%")

    @cli.command("cache-stats")
    def cache_stats():
        """显示缓存统计信息"""
        from asset_lens.data.providers.cache import provider_cache
        from rich.console import Console
        from rich.table import Table

        console = Console()

        click.echo("\n📊 缓存统计")
        click.echo("=" * 60)

        stats = provider_cache.stats()

        memory_stats = stats["memory"]
        file_stats = stats["file"]

        click.echo("\n🔥 内存缓存:")
        click.echo(f"   条目数: {memory_stats['size']}/{memory_stats['max_size']}")
        click.echo(f"   总命中: {memory_stats['total_hits']}")

        click.echo("\n📁 文件缓存:")
        click.echo(f"   文件数: {file_stats['file_count']}")
        click.echo(f"   总大小: {file_stats['total_size_bytes'] / 1024:.1f} KB")
        click.echo(f"   缓存目录: {file_stats['cache_dir']}")

    @cli.command("cache-clear")
    @click.option("--type", "data_type", default=None, help="指定数据类型")
    def cache_clear(data_type: Optional[str]):
        """清空缓存
        
        示例:
            asset-lens cache-clear
            asset-lens cache-clear --type stock_quote
        """
        from asset_lens.data.providers.cache import provider_cache

        provider_cache.clear(data_type)
        
        if data_type:
            click.echo(f"✅ 已清空 {data_type} 缓存")
        else:
            click.echo("✅ 已清空所有缓存")
