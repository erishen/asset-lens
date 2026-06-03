import click
import pandas as pd


def register_data_commands(cli: click.Group) -> None:
    @cli.command()
    @click.argument("codes", nargs=-1, required=True)
    def fetch_stock(codes: tuple[str, ...]):
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
    def fetch_fund(codes: tuple[str, ...]):
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
    def fetch_portfolio_funds(data_mode: str | None):
        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes

        setup_data_mode(data_mode)

        click.echo("\n📊 自动获取投资组合基金净值")
        click.echo("=" * 60)

        result = fetch_portfolio_fund_quotes()

        if result.get("data"):
            click.echo(f"\n✅ 成功获取 {len(result['data'])} 只基金净值")
            click.echo("📁 数据已缓存到: cache/fund_quotes.json")
        else:
            click.echo("\n❌ 未能获取任何基金净值", err=True)

    @cli.command("update-market-data")
    @click.option("--fast", is_flag=True, help="快速模式（仅更新关键指数）")
    def update_market_data(fast: bool):
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        click.echo("\n📊 更新市场指数数据")
        click.echo("=" * 60)
        click.echo("📌 使用增强版数据获取器")
        click.echo("   - 多数据源冗余（AkShare、腾讯财经、东方财富等）")
        click.echo("   - 智能缓存（1小时有效期）")
        click.echo("")

        try:
            if fast:
                click.echo("🚀 快速模式：仅更新关键指数")
                domestic_result = enhanced_market_data_fetcher.fetch_domestic_indexes_fast()
                domestic_ok = bool(domestic_result and domestic_result.get("指数数据"))
                success = domestic_ok
            else:
                domestic_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
                foreign_result = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
                domestic_ok = bool(domestic_result and domestic_result.get("指数数据"))
                foreign_ok = bool(foreign_result and foreign_result.get("指数数据"))
                success = domestic_ok and foreign_ok

            if success:
                click.echo("\n✅ 市场指数数据更新成功！")
            else:
                click.echo("\n❌ 市场指数数据更新失败！", err=True)

        except Exception as e:
            click.echo(f"❌ 更新失败: {e}", err=True)

    @cli.command("update-all-data")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def update_all_data(data_mode: str | None):
        from asset_lens.cli_modules.cli.helpers import setup_data_mode
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher
        from asset_lens.data.fund_fetcher import fetch_portfolio_fund_quotes
        from asset_lens.data.stock_fetcher import stock_fetcher

        setup_data_mode(data_mode)

        click.echo("\n📊 更新所有数据")
        click.echo("=" * 60)

        click.echo("\n1️⃣ 更新市场指数数据...")
        try:
            domestic_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            foreign_result = enhanced_market_data_fetcher.fetch_all_foreign_indexes()
            domestic_ok = bool(domestic_result and domestic_result.get("指数数据"))
            foreign_ok = bool(foreign_result and foreign_result.get("指数数据"))
            if domestic_ok and foreign_ok:
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
    @click.option(
        "--type",
        "data_type",
        type=click.Choice(["stock_cn", "stock_us", "fund_cn", "index"]),
        required=True,
        help="数据类型",
    )
    @click.argument("symbol")
    def fetch_unified(data_type: str, symbol: str):
        from asset_lens.data.providers import DataType
        from asset_lens.data.unified_data_fetcher import unified_data_fetcher

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
            click.echo("\n✅ 成功获取数据:")
            for key, value in result.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo("\n❌ 未能获取数据", err=True)

    @cli.command("provider-health")
    @click.option("--provider", "provider_name", default=None, help="指定数据源名称")
    @click.option("--json", "output_json", is_flag=True, help="输出 JSON 格式")
    def provider_health(provider_name: str | None, output_json: bool):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.providers import provider_registry

        health_data = provider_registry.get_health(provider_name) if provider_name else provider_registry.get_health()

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
        click.echo("\n📈 汇总:")
        click.echo(f"   总数据源: {summary['total_providers']}")
        click.echo(f"   可用数据源: {summary['available_providers']}")
        click.echo(f"   整体成功率: {summary['overall_success_rate']}%")

    @cli.command("cache-stats")
    def cache_stats():
        from rich.console import Console

        from asset_lens.data.providers.cache import provider_cache

        Console()

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
    @click.option(
        "--type", "data_type", type=click.Choice(["stock_quote", "fund_quote", "market_index", "all"]), help="缓存类型"
    )
    def cache_clear(data_type: str | None):
        from asset_lens.data.providers.cache import provider_cache

        provider_cache.clear(data_type)

        if data_type:
            click.echo(f"✅ 已清空 {data_type} 缓存")
        else:
            click.echo("✅ 已清空所有缓存")

    @cli.command("fetch-market-stocks")
    @click.option("--save", is_flag=True, help="保存到缓存文件")
    @click.option("--limit", "limit", type=int, default=0, help="限制获取数量（0=不限制）")
    def fetch_market_stocks(save: bool, limit: int):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher

        console = Console()

        click.echo("\n📊 获取A股市场股票列表")
        click.echo("=" * 60)

        fetcher = MarketStockFetcher()
        stocks = fetcher.fetch_all_cn_stocks()

        if not stocks:
            click.echo("\n❌ 未能获取股票列表", err=True)
            return

        if limit > 0:
            stocks = stocks[:limit]
            click.echo(f"\n📋 限制获取前 {limit} 只股票")

        click.echo(f"\n✅ 成功获取 {len(stocks)} 只股票")

        if save:
            fetcher.save_market_stocks(stocks)
            click.echo("📁 数据已保存到缓存文件")

        table = Table(title="股票列表预览（前20只）")
        table.add_column("代码", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("现价", style="yellow")
        table.add_column("涨跌幅", style="magenta")
        table.add_column("市值(亿)", style="blue")

        for stock in stocks[:20]:
            change = stock.get("change_percent", 0)
            change_str = f"{change:+.2f}%" if change else "-"
            table.add_row(
                stock.get("code", ""),
                stock.get("name", ""),
                f"{stock.get('current_price', 0):.2f}",
                change_str,
                f"{stock.get('market_cap', 0):.1f}",
            )

        console.print(table)

        click.echo("\n💡 使用 --save 保存到缓存，用于ML训练")

    @cli.command("fetch-history-batch")
    @click.option("--codes", "codes_str", help="股票代码列表（逗号分隔）")
    @click.option("--days", default=250, help="历史天数")
    @click.option(
        "--source",
        "data_source",
        default="auto",
        type=click.Choice(["auto", "akshare", "baostock", "tushare"]),
        help="数据源",
    )
    @click.option("--delay", default=0.3, type=float, help="请求间隔（秒）")
    @click.option("--use-market-stocks", is_flag=True, help="使用市场股票列表")
    @click.option("--limit", default=0, type=int, help="限制股票数量（0=不限制）")
    @click.option("--skip-existing", is_flag=True, default=False, help="跳过已有历史数据的股票")
    @click.option("--concurrent", is_flag=True, default=False, help="使用并发获取（更快）")
    @click.option("--workers", default=5, type=int, help="并发数（仅并发模式有效）")
    def fetch_history_batch(
        codes_str: str | None,
        days: int,
        data_source: str,
        delay: float,
        use_market_stocks: bool,
        limit: int,
        skip_existing: bool,
        concurrent: bool,
        workers: int,
    ):
        from rich.console import Console

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher

        Console()

        click.echo("\n📊 批量获取股票历史K线数据")
        click.echo("=" * 60)

        codes = []
        if use_market_stocks:
            click.echo("📋 使用市场股票列表...")
            fetcher = MarketStockFetcher()
            stocks = fetcher.get_cached_market_stocks()
            if not stocks:
                click.echo("⚠️ 缓存中没有市场股票数据，正在获取...")
                stocks = fetcher.fetch_all_cn_stocks()
                if stocks:
                    fetcher.save_market_stocks(stocks)

            if stocks:
                codes = [s.get("code", "") for s in stocks if s.get("code")]
                click.echo(f"✅ 获取到 {len(codes)} 只股票代码")
        elif codes_str:
            codes = [c.strip() for c in codes_str.split(",") if c.strip()]

        if not codes:
            click.echo("\n❌ 请指定股票代码列表或使用 --use-market-stocks", err=True)
            return

        if skip_existing:
            from asset_lens.db.database import db_manager

            existing_codes = db_manager.get_stock_codes_with_klines()
            original_count = len(codes)
            codes = [c for c in codes if c not in existing_codes]
            skipped = original_count - len(codes)
            if skipped > 0:
                click.echo(f"📋 跳过已有历史数据的股票: {skipped} 只")

        if limit > 0:
            codes = codes[:limit]
            click.echo(f"📋 限制获取前 {limit} 只股票")

        click.echo("\n📊 开始获取历史数据:")
        click.echo(f"   股票数量: {len(codes)}")
        click.echo(f"   历史天数: {days}")
        click.echo(f"   数据源: {data_source}")
        if concurrent:
            click.echo(f"   并发模式: 开启 ({workers} 个线程)")
        else:
            click.echo(f"   请求间隔: {delay}秒")

        from asset_lens.db.migration import DataMigration

        migration = DataMigration()
        if concurrent:
            result = migration.fetch_and_store_history_concurrent(
                codes=codes,
                days=days,
                data_source=data_source,
                max_workers=workers,
            )
        else:
            result = migration.fetch_and_store_history(
                codes=codes,
                days=days,
                data_source=data_source,
                delay=delay,
            )

        click.echo("\n📊 获取结果:")
        click.echo(f"   ✅ 成功: {result.get('success', 0)}")
        click.echo(f"   ❌ 失败: {result.get('failed', 0)}")
        click.echo(f"   📈 K线总数: {result.get('total_klines', 0)}")

        if result.get("errors"):
            click.echo("\n⚠️ 失败的股票:")
            for err in result["errors"][:10]:
                click.echo(f"   {err.get('code')}: {err.get('error')}")

        click.echo("\n💡 使用 'asset-lens ml-train-db' 训练模型")

    from .data_flow_commands import register_data_flow_commands

    register_data_flow_commands(cli)
