"""
Database CLI commands for asset-lens.
数据库管理命令
"""

from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def db():
    """数据库管理命令"""
    pass


@db.command()
def stats():
    """显示数据库统计信息"""
    from asset_lens.db.database import db_manager

    stats_data = db_manager.get_statistics()

    table = Table(title="数据库统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("K线数据总数", f"{stats_data['kline_count']:,}")
    table.add_row("股票数量", f"{stats_data['stock_count']:,}")
    table.add_row("ML模型数量", str(stats_data["model_count"]))
    table.add_row("预测记录数", str(stats_data["prediction_count"]))
    table.add_row("最新数据日期", stats_data["latest_date"] or "无数据")

    console.print(table)

    if stats_data["data_sources"]:
        source_table = Table(title="数据来源分布")
        source_table.add_column("数据源", style="cyan")
        source_table.add_column("记录数", style="green")

        for source, count in stats_data["data_sources"].items():
            source_table.add_row(source, f"{count:,}")

        console.print(source_table)


@db.command()
@click.option("--target", default=95.0, help="目标覆盖率 (默认 95%)")
@click.option("--enhance", is_flag=True, help="自动提升覆盖率")
def coverage(target: float, enhance: bool):
    """检查数据覆盖率

    示例:
        asset-lens db coverage              # 检查覆盖率
        asset-lens db coverage --enhance    # 自动提升覆盖率
        asset-lens db coverage --target 98  # 设置目标覆盖率
    """
    from asset_lens.data.data_coverage_analyzer import data_coverage_analyzer, data_coverage_enhancer

    console.print(Panel.fit("📊 数据覆盖率分析", style="bold blue"))

    if enhance:
        console.print(f"\n[yellow]正在提升覆盖率到 {target}%...[/yellow]")
        enhance_result = data_coverage_enhancer.enhance(target)

        if enhance_result["before"]:
            console.print(f"\n提升前覆盖率: [red]{enhance_result['before']['coverage']:.1f}%[/red]")
        if enhance_result["after"]:
            console.print(f"提升后覆盖率: [green]{enhance_result['after']['coverage']:.1f}%[/green]")

        if enhance_result["actions"]:
            console.print("\n[bold]执行的动作:[/bold]")
            for action in enhance_result["actions"]:
                console.print(f"  • {action}")

        if enhance_result["improvements"]:
            console.print("\n[bold]改进结果:[/bold]")
            for imp in enhance_result["improvements"]:
                console.print(f"  ✅ {imp}")
    else:
        result = data_coverage_analyzer.analyze()

        coverage_color = "green" if result.overall_coverage >= target else "red"
        console.print(f"\n整体覆盖率: [{coverage_color}]{result.overall_coverage:.1f}%[/{coverage_color}]")
        console.print(f"缺失数据点: {result.missing_data_points:,}")
        console.print(f"总数据点: {result.total_data_points:,}")

        table = Table(title="分类覆盖率")
        table.add_column("类别", style="cyan")
        table.add_column("预期", style="blue")
        table.add_column("实际", style="green")
        table.add_column("覆盖率", style="yellow")
        table.add_column("状态", style="bold")

        for category, report in result.categories.items():
            status = "✅" if report.coverage_rate >= target else "❌"
            table.add_row(
                category,
                str(report.total_expected),
                str(report.total_actual),
                f"{report.coverage_rate:.1f}%",
                status,
            )

        console.print(table)

        if result.recommendations:
            console.print("\n[bold yellow]建议:[/bold yellow]")
            for rec in result.recommendations:
                console.print(f"  • {rec}")


@db.command()
@click.option("--cache-file", type=click.Path(exists=True), help="JSON缓存文件路径")
def migrate(cache_file):
    """从JSON缓存迁移数据到数据库"""
    from pathlib import Path

    from asset_lens.db.migration import DataMigration

    migration = DataMigration()

    if cache_file:
        result = migration.migrate_history_cache(Path(cache_file))
    else:
        result = migration.migrate_history_cache()

    if result.get("status") == "success":
        console.print("[green]迁移成功![/green]")
        console.print(f"  股票数: {result.get('success_count', 0)}")
        console.print(f"  K线数: {result.get('total_klines', 0)}")
    else:
        console.print(f"[yellow]迁移结果: {result}[/yellow]")


@db.command("clean-old")
@click.option("--days", default=180, help="保留最近N天的数据")
@click.option("--confirm", is_flag=True, help="确认执行清理")
def clean_old(days, confirm):
    """清理旧数据，只保留最近N天的数据

    示例:
        asset-lens db clean-old              # 查看会清理多少数据
        asset-lens db clean-old --confirm    # 确认执行清理
        asset-lens db clean-old --days 90    # 只保留90天数据
    """
    from datetime import datetime, timedelta

    from asset_lens.db.database import db_manager
    from asset_lens.db.models import StockKline

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    console.print("[bold blue]🧹 清理旧数据[/bold blue]")
    console.print(f"   保留天数: {days} 天")
    console.print(f"   截止日期: {cutoff_date}")

    session = db_manager.get_session()
    try:
        old_count = session.query(StockKline).filter(StockKline.date < cutoff_date).count()
        total_count = session.query(StockKline).count()

        console.print("\n📊 数据统计:")
        console.print(f"   总K线数: {total_count:,}")
        console.print(f"   旧数据数: {old_count:,} (将删除)")
        console.print(f"   保留数据: {total_count - old_count:,}")

        if old_count == 0:
            console.print("\n[green]✅ 没有需要清理的旧数据！[/green]")
            return

        if not confirm:
            console.print(f"\n[yellow]⚠️ 将删除 {old_count:,} 条旧数据[/yellow]")
            console.print("[yellow]   使用 --confirm 参数确认执行[/yellow]")
            return

        deleted = session.query(StockKline).filter(StockKline.date < cutoff_date).delete()
        session.commit()

        console.print("\n[green]✅ 清理完成！[/green]")
        console.print(f"   删除: {deleted:,} 条")

    finally:
        session.close()


@db.command()
@click.argument("codes", nargs=-1, required=True)
@click.option("--days", default=250, help="历史天数")
@click.option("--source", default="auto", help="数据源 (auto/tushare/baostock/akshare)")
@click.option("--delay", default=0.3, help="请求间隔秒数")
def fetch(codes, days, source, delay):
    """获取股票历史数据并存储到数据库

    示例:
        asset-lens db fetch sh600519 sz000001 --days 365
    """
    from asset_lens.db.migration import DataMigration

    codes_list = list(codes)
    migration = DataMigration()

    result = migration.fetch_and_store_history(
        codes=codes_list,
        days=days,
        data_source=source,
        delay=delay,
    )

    console.print("\n[green]获取完成![/green]")
    console.print(f"  成功: {result['success']}")
    console.print(f"  失败: {result['failed']}")


@db.command()
@click.argument("code")
@click.option("--start", help="起始日期 (YYYY-MM-DD)")
@click.option("--end", help="结束日期 (YYYY-MM-DD)")
@click.option("--limit", default=30, help="返回数量限制")
def kline(code, start, end, limit):
    """查询股票K线数据

    示例:
        asset-lens db kline sh600519 --limit 10
    """
    from asset_lens.db.database import db_manager

    klines = db_manager.get_klines(code, start, end, limit)

    if not klines:
        console.print(f"[yellow]未找到 {code} 的K线数据[/yellow]")
        return

    table = Table(title=f"{code} K线数据 (最近{len(klines)}条)")
    table.add_column("日期", style="cyan")
    table.add_column("开盘", style="white")
    table.add_column("收盘", style="white")
    table.add_column("最高", style="green")
    table.add_column("最低", style="red")
    table.add_column("涨跌幅", style="yellow")
    table.add_column("换手率", style="blue")

    for k in klines[-20:]:
        change_color = "green" if k.get("change_percent", 0) >= 0 else "red"
        table.add_row(
            k.get("date", ""),
            f"{k.get('open', 0):.2f}",
            f"{k.get('close', 0):.2f}",
            f"{k.get('high', 0):.2f}",
            f"{k.get('low', 0):.2f}",
            f"[{change_color}]{k.get('change_percent', 0):.2f}%[/{change_color}]",
            f"{k.get('turnover_rate', 0):.2f}%",
        )

    console.print(table)


@db.command()
@click.option("--days", default=365, help="保留最近N天的数据")
def clean(days):
    """清理旧数据"""
    from asset_lens.db.database import db_manager

    console.print(f"[yellow]正在清理 {days} 天前的旧数据...[/yellow]")
    deleted = db_manager.clear_old_data(days)
    console.print(f"[green]已删除 {deleted} 条旧数据[/green]")


@db.command()
def verify():
    """验证数据完整性"""
    from asset_lens.db.migration import DataMigration

    migration = DataMigration()
    result = migration.verify_data()

    if result.get("status") == "no_data":
        console.print("[yellow]数据库中没有数据[/yellow]")
        return

    console.print("[green]验证完成[/green]")
    console.print(f"  总股票数: {result.get('total_stocks', 0)}")
    console.print(f"  抽样检查: {result.get('sample_size', 0)}")

    if result.get("issues"):
        console.print(f"[yellow]发现问题: {len(result['issues'])} 个[/yellow]")
        for issue in result["issues"][:5]:
            console.print(f"  - {issue['code']}: {issue['issue']} ({issue['count']}条)")


@db.command()
@click.argument("code", required=False)
def info(code):
    """查看股票基本信息

    示例:
        asset-lens db info sh600519
    """
    from asset_lens.db.database import db_manager

    if code:
        stock_info = db_manager.get_stock_info(code)
        if stock_info:
            table = Table(title=f"{code} 基本信息")
            table.add_column("字段", style="cyan")
            table.add_column("值", style="green")

            for key, value in stock_info.items():
                table.add_row(str(key), str(value))

            console.print(table)
        else:
            console.print(f"[yellow]未找到 {code} 的基本信息[/yellow]")
    else:
        console.print("[yellow]请提供股票代码[/yellow]")


@db.command()
def codes():
    """列出所有有数据的股票代码"""
    from asset_lens.db.database import db_manager

    all_codes = db_manager.get_stock_codes()

    if not all_codes:
        console.print("[yellow]数据库中没有股票数据[/yellow]")
        return

    console.print(f"[green]共 {len(all_codes)} 只股票[/green]")

    table = Table(show_header=True)
    table.add_column("序号", style="dim")
    table.add_column("代码", style="cyan")

    for i, code in enumerate(all_codes[:50]):
        table.add_row(str(i + 1), code)

    if len(all_codes) > 50:
        table.add_row("...", f"... 还有 {len(all_codes) - 50} 只")

    console.print(table)


@db.command("update-missing")
@click.option("--days", default=250, help="检查最近N天的数据")
@click.option("--limit", default=50, help="最多更新N只股票")
@click.option("--delay", default=0.3, help="请求间隔秒数")
@click.option("--source", default="auto", help="数据源 (auto/tushare/baostock/akshare)")
def update_missing(days, limit, delay, source) -> None:
    """智能更新缺失或过期的股票历史数据

    自动检测数据库中哪些股票的数据缺失或过期，并只更新这些股票。

    示例:
        asset-lens db update-missing              # 更新缺失数据的股票
        asset-lens db update-missing --days 365   # 检查最近一年数据
        asset-lens db update-missing --limit 100  # 最多更新100只
    """
    from datetime import datetime, timedelta

    from asset_lens.db.database import db_manager
    from asset_lens.db.migration import DataMigration

    console.print("[bold blue]🔍 检查需要更新的股票...[/bold blue]")

    session = db_manager.get_session()
    try:
        from sqlalchemy import func as sql_func  # pylint: disable=not-callable

        from asset_lens.db.models import StockKline

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        stocks_with_data = (
            session.query(
                StockKline.code,
                sql_func.max(StockKline.date).label("latest_date"),
                sql_func.count(StockKline.id).label("count"),  # pylint: disable=not-callable
            )
            .group_by(StockKline.code)
            .all()
        )

        stocks_to_update: list[dict[str, Any]] = []
        for stock in stocks_with_data:
            latest_date = stock.latest_date
            count = stock.count

            if latest_date < cutoff_date:
                stocks_to_update.append(
                    {
                        "code": stock.code,
                        "reason": "数据过期",
                        "latest_date": latest_date,
                        "count": count,
                    }
                )
            elif count < days * 0.5:
                stocks_to_update.append(
                    {
                        "code": stock.code,
                        "reason": "数据不足",
                        "latest_date": latest_date,
                        "count": count,
                    }
                )

        stocks_to_update.sort(key=lambda x: x["latest_date"])

        if not stocks_to_update:
            console.print("[green]✅ 所有股票数据都是最新的！[/green]")
            return

        console.print(f"\n[yellow]发现 {len(stocks_to_update)} 只股票需要更新:[/yellow]")

        table = Table(show_header=True)
        table.add_column("代码", style="cyan")
        table.add_column("原因", style="yellow")
        table.add_column("最新日期", style="white")
        table.add_column("数据量", style="dim")

        for stock in stocks_to_update[:20]:  # type: ignore
            table.add_row(
                stock.get("code", ""),
                stock.get("reason", ""),
                stock.get("latest_date", ""),
                str(stock.get("count", 0)),
            )

        if len(stocks_to_update) > 20:
            table.add_row("...", f"... 还有 {len(stocks_to_update) - 20} 只", "", "")

        console.print(table)

        codes_to_fetch = [s["code"] for s in stocks_to_update[:limit]]
        console.print(f"\n[bold blue]📥 开始更新 {len(codes_to_fetch)} 只股票...[/bold blue]")

        migration = DataMigration()
        result = migration.fetch_and_store_history(
            codes=codes_to_fetch,
            days=days,
            data_source=source,
            delay=delay,
        )

        console.print("\n[bold green]✅ 更新完成![/bold green]")
        console.print(f"  成功: {result['success']}")
        console.print(f"  失败: {result['failed']}")
        console.print(f"  K线总数: {result['total_klines']}")

    finally:
        session.close()


@db.command("auto-sync")
@click.option("--days", default=90, help="历史天数")
@click.option("--daily-limit", default=50, help="每日新增股票数量限制")
@click.option("--update-limit", default=30, help="每日更新股票数量限制")
@click.option("--delay", default=0.2, help="请求间隔秒数")
@click.option("--fast", is_flag=True, help="快速模式：跳过详细检查，直接返回状态")
def auto_sync(days, daily_limit, update_limit, delay, fast):
    """智能同步股票历史数据（适合 make daily 使用）

    自动检测并执行以下操作：
    1. 如果数据库为空，自动开始批量下载
    2. 如果数据库有数据，检查并更新缺失的数据
    3. 每天自动补全一定数量的新股票

    示例:
        asset-lens db auto-sync              # 智能同步
        asset-lens db auto-sync --fast       # 快速模式（跳过更新）
        asset-lens db auto-sync --days 250   # 获取250天历史
        asset-lens db auto-sync --daily-limit 100  # 每天新增100只
    """
    from datetime import datetime, timedelta

    from asset_lens.data.market_stock_fetcher import MarketStockFetcher
    from asset_lens.db.database import db_manager
    from asset_lens.db.migration import DataMigration

    console.print("[bold blue]🔄 智能同步股票历史数据[/bold blue]")
    console.print("=" * 60)

    session = db_manager.get_session()
    try:
        from sqlalchemy import func as sql_func  # pylint: disable=not-callable

        from asset_lens.db.models import StockKline

        stats = db_manager.get_statistics()
        db_stock_count = stats["stock_count"]
        db_kline_count = stats["kline_count"]
        latest_date = stats["latest_date"]

        if fast:
            console.print("\n⚡ 快速模式")
            console.print(f"   数据库股票数: {db_stock_count}")
            console.print(f"   数据库K线数: {db_kline_count:,}")
            console.print(f"   最新日期: {latest_date or '无数据'}")

            if db_stock_count > 100 and latest_date:
                latest = datetime.strptime(latest_date, "%Y-%m-%d")
                days_ago = (datetime.now() - latest).days
                if days_ago <= 3:
                    console.print(f"\n[green]✅ 数据较新（{days_ago}天前更新），跳过同步[/green]")
                    return

            console.print("\n[cyan]继续执行同步...[/cyan]")

        fetcher = MarketStockFetcher()
        cached_stocks = fetcher.get_cached_market_stocks(max_age_hours=48)
        total_market_stocks = len(cached_stocks) if cached_stocks else 5193

        console.print("\n📊 当前状态:")
        console.print(f"   数据库股票数: {db_stock_count}")
        console.print(f"   数据库K线数: {db_kline_count:,}")
        console.print(f"   市场股票总数: {total_market_stocks}")
        console.print(
            f"   覆盖率: {db_stock_count / total_market_stocks * 100:.1f}%"
            if total_market_stocks > 0
            else "   覆盖率: 0%"
        )

        migration = DataMigration()

        if db_stock_count < 100:
            console.print("\n[yellow]⚠️ 数据库股票数量较少，开始批量下载...[/yellow]")
            console.print(f"   本次下载: {daily_limit} 只股票")
            console.print(f"   历史天数: {days} 天")

            if cached_stocks:
                codes_to_fetch = [str(s.get("code")) for s in cached_stocks[:daily_limit] if s.get("code")]
            else:
                codes_to_fetch = []

            result = migration.fetch_and_store_history(
                codes=codes_to_fetch,
                days=days,
                data_source="auto",
                delay=delay,
            )

            console.print("\n[green]✅ 批量下载完成![/green]")
            console.print(f"   成功: {result['success']}")
            console.print(f"   失败: {result['failed']}")
            console.print(f"   K线总数: {result['total_klines']}")

        else:
            today = datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            weekday = today.weekday()
            is_weekend = weekday >= 5

            stale_days = 7
            stale_date = (today - timedelta(days=stale_days)).strftime("%Y-%m-%d")

            min_data_ratio = 0.3
            min_data_count = int(days * min_data_ratio)

            stocks_with_data = (
                session.query(
                    StockKline.code,
                    sql_func.max(StockKline.date).label("latest_date"),
                    sql_func.count(StockKline.id).label("count"),
                )
                .group_by(StockKline.code)
                .all()
            )

            stocks_to_update = []
            skipped_stale = 0
            skipped_insufficient = 0

            for stock in stocks_with_data:
                if stock.latest_date >= stale_date:
                    continue

                stock_count = int(getattr(stock, "count", 0) or 0)

                if stock.latest_date < stale_date:
                    if is_weekend and stock.latest_date >= (today - timedelta(days=3)).strftime("%Y-%m-%d"):
                        skipped_stale += 1
                        continue

                    stocks_to_update.append(
                        {
                            "code": stock.code,
                            "reason": "数据过期",
                            "latest_date": stock.latest_date,
                        }
                    )
                elif stock_count < min_data_count:
                    if stock_count < 10:
                        stocks_to_update.append(
                            {
                                "code": stock.code,
                                "reason": "数据严重不足",
                                "latest_date": stock.latest_date,
                            }
                        )
                    else:
                        skipped_insufficient += 1

            if skipped_stale > 0:
                console.print(f"\n[dim]⏭️ 跳过 {skipped_stale} 只股票（周末数据仍有效）[/dim]")
            if skipped_insufficient > 0:
                console.print(f"[dim]⏭️ 跳过 {skipped_insufficient} 只股票（数据量可接受）[/dim]")

            if stocks_to_update:
                stocks_to_update.sort(key=lambda x: x["latest_date"])
                console.print(f"\n[yellow]发现 {len(stocks_to_update)} 只股票需要更新[/yellow]")

                codes_to_update = [s["code"] for s in stocks_to_update[:update_limit]]
                console.print(f"   本次更新: {len(codes_to_update)} 只")

                result = migration.fetch_and_store_history(
                    codes=codes_to_update,
                    days=days,
                    data_source="auto",
                    delay=delay,
                )

                console.print("\n[green]✅ 更新完成![/green]")
                console.print(f"   成功: {result['success']}")
                console.print(f"   失败: {result['failed']}")

            missing_count = total_market_stocks - db_stock_count
            if missing_count > 0:
                console.print(f"\n[cyan]📥 发现 {missing_count} 只股票未下载数据[/cyan]")
                console.print(f"   本次新增: {min(daily_limit, missing_count)} 只")

                if cached_stocks:
                    existing_codes = {s.code for s in stocks_with_data}
                    new_codes = [
                        s.get("code") for s in cached_stocks if s.get("code") and s.get("code") not in existing_codes
                    ][:daily_limit]
                else:
                    new_codes = []

                if new_codes:
                    result = migration.fetch_and_store_history(
                        codes=[str(code) for code in new_codes if code],
                        days=days,
                        data_source="auto",
                        delay=delay,
                    )

                console.print("\n[green]✅ 新增完成![/green]")
                console.print(f"   成功: {result['success']}")
                console.print(f"   失败: {result['failed']}")

            if not stocks_to_update and missing_count <= 0:
                console.print("\n[green]✅ 所有股票数据都是最新的！[/green]")

        new_stats = db_manager.get_statistics()
        console.print("\n📊 更新后状态:")
        console.print(f"   数据库股票数: {new_stats['stock_count']}")
        console.print(f"   数据库K线数: {new_stats['kline_count']:,}")
        console.print(f"   最新日期: {new_stats['latest_date']}")

    finally:
        session.close()


@db.command()
def optimize():
    """优化数据库性能

    执行以下优化操作：
    1. 启用 WAL 模式（提升并发性能）
    2. 优化 PRAGMA 设置
    3. 创建优化索引
    4. 分析表统计信息

    示例:
        asset-lens db optimize
    """
    from asset_lens.db.database import db_manager
    from asset_lens.db.optimizer import db_optimizer

    console.print("[bold blue]⚡ 数据库优化[/bold blue]")
    console.print("=" * 60)

    session = db_manager.get_session()
    try:
        result = db_optimizer.run_full_optimization(session)

        console.print(f"\n开始时间: {result['start_time']}")
        console.print(f"结束时间: {result['end_time']}")

        for opt in result["optimizations"]:
            status_emoji = "✅" if opt["status"] == "success" else "❌"
            console.print(f"\n{status_emoji} {opt['action']}")
            console.print(f"   {opt['message']}")

            if opt["action"] == "create_indexes":
                if opt["created"]:
                    console.print(f"   新建索引: {', '.join(opt['created'])}")
                if opt["skipped"]:
                    console.print(f"   已存在: {len(opt['skipped'])} 个")

            if opt["action"] == "optimize_pragmas":
                for pragma, value in opt["settings"].items():
                    console.print(f"   {pragma}: {value}")

        console.print("\n[bold green]✅ 优化完成![/bold green]")
        console.print(f"   成功: {result['summary']['success']}")
        console.print(f"   失败: {result['summary']['failed']}")

        stats = db_optimizer.get_table_stats(session)
        console.print("\n📊 表统计:")
        for table, info in stats.items():
            console.print(f"   {table}: {info['row_count']:,} 行")

    finally:
        session.close()


@db.command()
def indexes():
    """查看数据库索引

    示例:
        asset-lens db indexes
    """
    from asset_lens.db.database import db_manager
    from asset_lens.db.optimizer import db_optimizer

    session = db_manager.get_session()
    try:
        indexes_list = db_optimizer.get_index_usage(session)

        if not indexes_list:
            console.print("[yellow]没有找到索引[/yellow]")
            return

        table = Table(title=f"数据库索引 (共 {len(indexes_list)} 个)")
        table.add_column("索引名", style="cyan")
        table.add_column("表名", style="green")

        for idx in indexes_list:
            table.add_row(idx["name"], idx["table"])

        console.print(table)

    finally:
        session.close()


@db.command()
@click.argument("query")
@click.option("--iterations", default=3, help="迭代次数")
def benchmark(query, iterations):
    """基准测试查询性能

    示例:
        asset-lens db benchmark "SELECT COUNT(*) FROM stock_klines"
    """
    from asset_lens.db.database import db_manager
    from asset_lens.db.optimizer import db_optimizer

    session = db_manager.get_session()
    try:
        console.print("[bold blue]📊 查询性能测试[/bold blue]")
        console.print(f"查询: {query}")
        console.print(f"迭代: {iterations} 次")
        console.print("")

        result = db_optimizer.benchmark_query(session, query, iterations)

        table = Table(title="测试结果")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        table.add_row("平均时间", f"{result['avg_time_ms']:.2f} ms")
        table.add_row("最小时间", f"{result['min_time_ms']:.2f} ms")
        table.add_row("最大时间", f"{result['max_time_ms']:.2f} ms")

        console.print(table)

    finally:
        session.close()


@db.command()
def vacuum():
    """清理数据库碎片，释放空间

    示例:
        asset-lens db vacuum
    """
    from asset_lens.db.optimizer import db_optimizer

    console.print("[bold blue]🧹 清理数据库碎片[/bold blue]")
    console.print("")

    result = db_optimizer.vacuum_database()

    if result["status"] == "success":
        console.print(f"[green]✅ {result['message']}[/green]")
        if result["before_size"] > 0:
            before_mb = result["before_size"] / 1024 / 1024
            after_mb = result["after_size"] / 1024 / 1024
            console.print(f"   清理前: {before_mb:.2f} MB")
            console.print(f"   清理后: {after_mb:.2f} MB")
            console.print(f"   释放: {result['freed_mb']:.2f} MB")
    else:
        console.print(f"[red]❌ 清理失败: {result['message']}[/red]")
