"""
Database CLI commands for asset-lens.
数据库管理命令
"""

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def db():
    """数据库管理命令"""
    pass


@db.command()
def stats():
    """显示数据库统计信息"""
    from ..db.database import db_manager

    stats_data = db_manager.get_statistics()

    table = Table(title="数据库统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("K线数据总数", f"{stats_data['kline_count']:,}")
    table.add_row("股票数量", f"{stats_data['stock_count']:,}")
    table.add_row("ML模型数量", str(stats_data['model_count']))
    table.add_row("预测记录数", str(stats_data['prediction_count']))
    table.add_row("最新数据日期", stats_data['latest_date'] or "无数据")

    console.print(table)

    if stats_data['data_sources']:
        source_table = Table(title="数据来源分布")
        source_table.add_column("数据源", style="cyan")
        source_table.add_column("记录数", style="green")

        for source, count in stats_data['data_sources'].items():
            source_table.add_row(source, f"{count:,}")

        console.print(source_table)


@db.command()
@click.option("--cache-file", type=click.Path(exists=True), help="JSON缓存文件路径")
def migrate(cache_file):
    """从JSON缓存迁移数据到数据库"""
    from pathlib import Path

    from ..db.migration import DataMigration

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
    from ..db.migration import DataMigration

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
    from ..db.database import db_manager

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
    from ..db.database import db_manager

    console.print(f"[yellow]正在清理 {days} 天前的旧数据...[/yellow]")
    deleted = db_manager.clear_old_data(days)
    console.print(f"[green]已删除 {deleted} 条旧数据[/green]")


@db.command()
def verify():
    """验证数据完整性"""
    from ..db.migration import DataMigration

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
    from ..db.database import db_manager

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
    from ..db.database import db_manager

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
