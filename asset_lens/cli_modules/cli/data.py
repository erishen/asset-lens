"""
Data CLI commands for asset-lens.
数据管理命令模块 - 包含 fetch-stock, fetch-fund, search-fund, update-market-data, fetch-portfolio-funds, update-all-data
"""

import click
import pandas as pd


def register_data_commands(cli: click.Group) -> None:
    """注册数据管理命令到 CLI 组"""

    @cli.command()
    @click.argument("codes", nargs=-1, required=True)
    def fetch_stock(codes: tuple[str, ...]):
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
    def fetch_fund(codes: tuple[str, ...]):
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
    def fetch_portfolio_funds(data_mode: str | None):
        """自动获取投资组合中所有基金的净值

        自动匹配基金代码并获取净值
        """
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
        """更新市场指数数据

        使用增强版数据获取器，支持多数据源冗余和智能缓存
        """
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
        """更新所有数据（市场指数、基金净值、股票行情）

        一键更新所有需要的数据
        """
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
    @click.option(
        "--type",
        "data_type",
        type=click.Choice(["stock_cn", "stock_us", "fund_cn", "index"]),
        required=True,
        help="数据类型",
    )
    @click.argument("symbol")
    def fetch_unified(data_type: str, symbol: str):
        """使用 Provider Registry 获取数据

        示例:
            asset-lens fetch-unified --type stock_cn 600519
            asset-lens fetch-unified --type fund_cn 000001
            asset-lens fetch-unified --type stock_us AAPL
        """
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
        """显示数据源健康状态

        示例:
            asset-lens provider-health
            asset-lens provider-health --provider akshare
            asset-lens provider-health --json
        """
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
        """显示缓存统计信息"""
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
        """清空缓存数据"""
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
        """获取A股市场股票列表（用于ML训练数据）

        示例:
            asset-lens fetch-market-stocks --save
            asset-lens fetch-market-stocks --limit 100
        """
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
        """批量获取股票历史K线数据（用于ML训练）

        示例:
            asset-lens fetch-history-batch --codes sh600519,sz000001 --days 250
            asset-lens fetch-history-batch --use-market-stocks --limit 50 --days 250
            asset-lens fetch-history-batch --use-market-stocks --source akshare
        """
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

    @cli.command("north-flow")
    @click.option("--days", default=30, type=int, help="查看最近N天的北向资金")
    def north_flow(days: int):
        """北向资金分析"""
        from rich.console import Console
        from rich.table import Table

        from asset_lens.data.fundamental_fetcher import MoneyFlowFetcher

        console = Console()
        console.print("\n📈 北向资金分析")
        console.print("=" * 60)

        try:
            fetcher = MoneyFlowFetcher()
            df = fetcher.get_north_money_flow(days=days)

            if df is None or df.empty:
                console.print("[yellow]⚠️ 无法获取北向资金数据[/yellow]")
                return

            data_source = df["data_source"].iloc[0] if "data_source" in df.columns else "历史数据"
            console.print(f"\n📊 最近 {len(df)} 天北向资金流向 (数据来源: {data_source})")

            table = Table()
            table.add_column("日期", style="cyan")
            table.add_column("净流入(亿)", justify="right")
            table.add_column("趋势", justify="center")

            total_inflow = 0
            for _, row in df.iterrows():
                net_inflow = row.get("north_net_inflow", 0)
                if net_inflow:
                    total_inflow += net_inflow
                    trend = "🟢 流出" if net_inflow < 0 else "🔴 流入"
                    table.add_row(
                        str(row.get("date", "")),
                        f"{net_inflow:.2f}",
                        trend,
                    )

            console.print(table)

            console.print("\n📊 汇总:")
            console.print(f"   总净流入: {total_inflow:.2f} 亿")
            if total_inflow > 0:
                console.print("   [red]整体趋势: 北向资金净流入[/red]")
            else:
                console.print("   [green]整体趋势: 北向资金净流出[/green]")

        except Exception as e:
            console.print(f"[red]❌ 获取北向资金数据失败: {e}[/red]")

    @cli.command("north-industry")
    @click.option("--save", is_flag=True, help="保存到数据库")
    @click.option("--history", "show_history", is_flag=True, help="显示历史数据")
    @click.option("--days", default=7, type=int, help="历史天数(默认7天)")
    @click.option("--trend", "industry_name", help="显示指定行业的趋势")
    @click.option("--skip-fetch", is_flag=True, help="跳过数据获取，只显示历史数据")
    @click.option("--force", is_flag=True, help="强制获取数据（即使在开市时间）")
    def north_industry(save: bool, show_history: bool, days: int, industry_name: str | None, skip_fetch: bool, force: bool):
        """北向资金行业流向分析"""
        from datetime import datetime

        from rich.console import Console

        from asset_lens.data.fundamental_fetcher import MoneyFlowFetcher
        from asset_lens.db.database import db_manager

        console = Console()
        console.print("\n🏭 北向资金行业流向分析")
        console.print("=" * 60)

        # 检查是否在开市时间
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        is_trading_time = (9 <= current_hour < 15) or (current_hour == 9 and current_minute >= 30)

        if is_trading_time and not force and not skip_fetch:
            console.print("\n[yellow]⏰ 当前是开市时间 (9:30-15:00)[/yellow]")
            console.print("[yellow]⚠️  北向资金行业数据获取需要15-45秒，建议在非开市时间获取[/yellow]")
            console.print("\n[cyan]💡 可用选项：[/cyan]")
            console.print("   1. 使用缓存数据（如果有）")
            console.print("   2. 查看历史数据: make north-industry-history")
            console.print("   3. 强制获取: make north-industry --force")
            console.print("")

            # 尝试使用缓存
            try:
                fetcher = MoneyFlowFetcher()
                df = fetcher.get_north_flow_by_industry(use_cache=True)
                if not df.empty:
                    console.print("✅ 使用缓存数据：")
                    console.print(f"   数据来源: {df['data_source'].iloc[0]}")
                    _display_industry_flow_table(console, df.to_dict('records'))
                    return
                else:
                    console.print("[yellow]⚠️  没有缓存数据[/yellow]")
                    console.print("\n请使用以下命令：")
                    console.print("   - 查看历史: make north-industry-history")
                    console.print("   - 强制获取: make north-industry --force")
                    return
            except Exception as e:
                console.print(f"[red]❌ 获取缓存失败: {e}[/red]")
                return

        try:
            if show_history:
                console.print(f"\n📊 显示最近 {days} 天的历史数据...")
                dates = db_manager.get_north_industry_flow_dates(days=days)

                if not dates:
                    console.print("[yellow]⚠️ 数据库中没有历史数据,请先使用 --save 保存数据[/yellow]")
                    return

                console.print(f"✅ 找到 {len(dates)} 天的历史数据")

                for date in dates[:5]:
                    flow_data = db_manager.get_north_industry_flow(date=date)
                    if flow_data:
                        _display_industry_flow_table(console, flow_data, date)

                if len(dates) > 5:
                    console.print(f"\n... 还有 {len(dates) - 5} 天的数据未显示")

                return

            if industry_name:
                console.print(f"\n📈 {industry_name} 行业流向趋势(最近{days}天)...")
                trend_data = db_manager.get_north_industry_flow_trend(industry=industry_name, days=days)

                if not trend_data:
                    console.print(f"[yellow]⚠️ 数据库中没有 {industry_name} 的历史数据[/yellow]")
                    return

                _display_industry_trend(console, trend_data, industry_name)
                return

            # 检查是否跳过数据获取
            if skip_fetch:
                console.print("\n⏭️ 跳过数据获取，显示最近的历史数据...")
                dates = db_manager.get_north_industry_flow_dates(days=1)
                if dates:
                    flow_data = db_manager.get_north_industry_flow(date=dates[0])
                    if flow_data:
                        _display_industry_flow_table(console, flow_data, dates[0])
                    else:
                        console.print("[yellow]⚠️ 没有找到历史数据[/yellow]")
                else:
                    console.print("[yellow]⚠️ 数据库中没有历史数据[/yellow]")
                return

            fetcher = MoneyFlowFetcher()
            df = fetcher.get_north_flow_by_industry(force=force)

            if df.empty:
                console.print("\n[yellow]⚠️ 无法获取北向资金行业流向数据[/yellow]")
                console.print("\n[cyan]💡 建议使用以下替代方案：[/cyan]")
                console.print("   1. 查看历史数据: make north-industry-history")
                console.print("   2. 稍后重试（非开市时间成功率更高）")
                console.print("   3. 强制获取: make north-industry --force")
                console.print("\n[dim]提示: 北向资金行业数据获取需要30-60秒，且经常超时[/dim]")
                return

            # 安全地获取数据源
            data_source = None
            if 'data_source' in df.columns and not df.empty:
                data_source = df['data_source'].iloc[0] if len(df) > 0 else None

            if data_source:
                console.print(f"\n📊 北向资金行业流向分析 (数据来源: {data_source})")

                # 根据数据源显示不同说明
                if "5日" in str(data_source):
                    console.print("   说明: 显示北向资金近5日在各行业的净流入变化，单位：亿元")
                    console.print("   计算: 5日净流入 = 今日持仓 - 5日前持仓")
                else:
                    console.print("   说明: 显示北向资金在各行业的持仓市值分布，单位：亿元")
            else:
                console.print("\n📊 北向资金行业流向分析")

            if save:
                from datetime import datetime, timedelta
                date = datetime.now().strftime("%Y-%m-%d")
                industry_data = df.to_dict('records')
                result = db_manager.save_north_industry_flow(date, industry_data)

                if result['added'] > 0:
                    console.print(f"\n✅ 已保存 {result['added']} 条新数据到数据库")
                elif result['updated'] > 0:
                    console.print(f"\n✅ 已更新 {result['updated']} 条数据到数据库")
                else:
                    console.print("\n✅ 数据已是最新，无需保存")

                # 计算流向变化
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                yesterday_data = db_manager.get_north_industry_flow(date=yesterday)

                if yesterday_data:
                    console.print(f"\n📈 行业流向变化分析 (对比 {yesterday}):")

                    # 计算变化
                    yesterday_df = pd.DataFrame(yesterday_data)
                    merged = df.merge(yesterday_df[['industry', 'net_inflow']],
                                     on='industry',
                                     suffixes=('', '_yesterday'))

                    merged['flow_change'] = merged['net_inflow'] - merged['net_inflow_yesterday']
                    merged['flow_change_pct'] = (merged['flow_change'] / merged['net_inflow_yesterday'].abs() * 100).fillna(0)

                    # 显示流入增加最多的行业
                    inflow_increase = merged[merged['flow_change'] > 0.01].nlargest(5, 'flow_change')
                    if not inflow_increase.empty:
                        console.print("\n   🔴 流入增加TOP5:")
                        for i, (_, row) in enumerate(inflow_increase.iterrows(), 1):
                            console.print(f"      {i}. {row['industry']}: +{row['flow_change']:.2f}亿 ({row['flow_change_pct']:+.1f}%)")

                    # 显示流出最多的行业（持仓减少）
                    outflow_increase = merged[merged['flow_change'] < -0.01].nsmallest(5, 'flow_change')
                    if not outflow_increase.empty:
                        console.print("\n   🟢 流出增加TOP5:")
                        for i, (_, row) in enumerate(outflow_increase.iterrows(), 1):
                            console.print(f"      {i}. {row['industry']}: {row['flow_change']:.2f}亿 ({row['flow_change_pct']:+.1f}%)")

                    # 如果没有明显变化，显示提示
                    if inflow_increase.empty and outflow_increase.empty:
                        max_change = merged['flow_change'].abs().max()
                        console.print(f"\n   💡 今日持仓变化很小 (最大变化: {max_change:.2f}亿)")
                        console.print("      这说明北向资金持仓相对稳定，没有明显的行业轮动")
                else:
                    console.print(f"\n💡 提示: 没有找到昨天({yesterday})的数据，明天可以看到流向变化")

            _display_industry_flow_table(console, df.to_dict('records'))

        except Exception as e:
            console.print(f"[red]❌ 分析失败: {e}[/red]")
            import traceback
            traceback.print_exc()


def _display_industry_flow_table(console, flow_data: list, date: str | None = None):
    """显示行业流向表格"""
    import pandas as pd
    from rich.table import Table

    df = pd.DataFrame(flow_data) if not isinstance(flow_data, pd.DataFrame) else flow_data

    if date:
        console.print(f"\n📅 {date}")

    inflow_df = df[df['net_inflow'] > 0].head(10)
    outflow_df = df[df['net_inflow'] < 0].head(10)

    # 判断是否是5日流向变化
    is_flow_change = "5日" in df['data_source'].iloc[0] if 'data_source' in df.columns else False

    if not inflow_df.empty:
        if is_flow_change:
            title = "\n🔴 5日净流入TOP10"
            col_name = "净流入(亿)"
        else:
            title = "\n🔴 持仓市值TOP10"
            col_name = "持仓市值(亿)"

        inflow_table = Table(title=title, show_header=True, header_style="bold red")
        inflow_table.add_column("排名", style="cyan", width=6)
        inflow_table.add_column("行业", style="white", width=20)
        inflow_table.add_column(col_name, justify="right", style="red", width=12)
        inflow_table.add_column("变化率", justify="right", style="yellow", width=10)

        for i, (_, row) in enumerate(inflow_df.iterrows(), 1):
            # 格式化变化率显示
            change_rate = row['change_rate']
            if abs(change_rate) >= 1000:
                change_rate_str = f"{change_rate:+.0f}%"
            elif abs(change_rate) >= 100:
                change_rate_str = f"{change_rate:+.1f}%"
            else:
                change_rate_str = f"{change_rate:+.2f}%"

            inflow_table.add_row(
                str(i),
                row['industry'],
                f"+{row['net_inflow']:.2f}",
                change_rate_str
            )

        console.print(inflow_table)

    if not outflow_df.empty:
        if is_flow_change:
            title = "\n🟢 5日净流出TOP10"
            col_name = "净流出(亿)"
        else:
            title = "\n🟢 持仓较少行业"
            col_name = "持仓市值(亿)"

        outflow_table = Table(title=title, show_header=True, header_style="bold green")
        outflow_table.add_column("排名", style="cyan", width=6)
        outflow_table.add_column("行业", style="white", width=20)
        outflow_table.add_column(col_name, justify="right", style="green", width=12)
        outflow_table.add_column("变化率", justify="right", style="yellow", width=10)

        for i, (_, row) in enumerate(outflow_df.iterrows(), 1):
            # 格式化变化率显示
            change_rate = row['change_rate']
            if abs(change_rate) >= 1000:
                change_rate_str = f"{change_rate:+.0f}%"
            elif abs(change_rate) >= 100:
                change_rate_str = f"{change_rate:+.1f}%"
            else:
                change_rate_str = f"{change_rate:+.2f}%"

            outflow_table.add_row(
                str(i),
                row['industry'],
                f"{row['net_inflow']:.2f}",
                change_rate_str
            )

        console.print(outflow_table)

    total_inflow = df[df['net_inflow'] > 0]['net_inflow'].sum()
    total_outflow = df[df['net_inflow'] < 0]['net_inflow'].sum()
    net_total = total_inflow + total_outflow

    console.print("\n📊 汇总统计:")

    if is_flow_change:
        console.print(f"   净流入行业数: {len(inflow_df)} 个")
        console.print(f"   净流出行业数: {len(outflow_df)} 个")
        console.print(f"   总净流入: {total_inflow:.2f} 亿")
        console.print(f"   总净流出: {total_outflow:.2f} 亿")
        console.print(f"   净流入合计: {net_total:.2f} 亿")
    else:
        console.print(f"   行业数量: {len(df)} 个")
        console.print(f"   总持仓市值: {net_total:.2f} 亿")

        if len(inflow_df) > 0:
            top1 = inflow_df.iloc[0]
            top1_ratio = (top1['net_inflow'] / net_total * 100) if net_total > 0 else 0
            console.print(f"   第一大行业: {top1['industry']} ({top1_ratio:.1f}%)")

    console.print("\n💡 分析建议:")
    if not inflow_df.empty:
        top_inflow = inflow_df.iloc[0]
        if is_flow_change:
            console.print(f"   🔴 5日净流入最多: {top_inflow['industry']} (净流入 {top_inflow['net_inflow']:.2f} 亿)")
        else:
            console.print(f"   🔴 北向资金重仓: {top_inflow['industry']} (持仓 {top_inflow['net_inflow']:.2f} 亿)")

        if not is_flow_change and len(inflow_df) >= 3:
            console.print("\n   📈 北向资金持仓TOP3:")
            for i, (_, row) in enumerate(inflow_df.head(3).iterrows(), 1):
                ratio = (row['net_inflow'] / net_total * 100) if net_total > 0 else 0
                console.print(f"      {i}. {row['industry']}: {row['net_inflow']:.2f}亿 ({ratio:.1f}%)")

    if is_flow_change and not outflow_df.empty:
        top_outflow = outflow_df.iloc[0]
        console.print(f"   🟢 5日净流出最多: {top_outflow['industry']} (净流出 {abs(top_outflow['net_inflow']):.2f} 亿)")


def _display_industry_trend(console, trend_data: list, industry_name: str):
    """显示行业趋势"""
    from rich.table import Table

    if not trend_data:
        return

    table = Table(title=f"\n📈 {industry_name} 行业流向趋势", show_header=True, header_style="bold magenta")
    table.add_column("日期", style="cyan", width=12)
    table.add_column("净流入(亿)", justify="right", width=12)
    table.add_column("变化率", justify="right", width=10)
    table.add_column("趋势", justify="center", width=8)

    prev_inflow = None
    for data in trend_data:
        net_inflow = data['net_inflow']
        change_rate = data['change_rate']

        if prev_inflow is not None:
            if net_inflow > prev_inflow:
                trend = "📈 上升"
            elif net_inflow < prev_inflow:
                trend = "📉 下降"
            else:
                trend = "➡️ 持平"
        else:
            trend = "-"

        table.add_row(
            data['date'],
            f"{net_inflow:+.2f}",
            f"{change_rate:+.2f}%",
            trend
        )
        prev_inflow = net_inflow

    console.print(table)

    avg_inflow = sum(d['net_inflow'] for d in trend_data) / len(trend_data)
    console.print("\n📊 统计:")
    console.print(f"   平均净流入: {avg_inflow:+.2f} 亿")
    console.print(f"   数据天数: {len(trend_data)} 天")

    if avg_inflow > 0:
        console.print(f"   💡 结论: 北向资金整体看好 {industry_name} 行业")
    else:
        console.print(f"   💡 结论: 北向资金整体看空 {industry_name} 行业")
