import click


@click.group()
def db():
    pass


@db.command()
def stats():
    from rich.console import Console
    from rich.table import Table

    from asset_lens.db.database import db_manager

    console = Console()

    click.echo("\n📊 数据库统计信息")
    click.echo("=" * 60)

    statistics = db_manager.get_statistics()

    table = Table(title="数据库统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("K线数据", f"{statistics['kline_count']:,} 条")
    table.add_row("股票数量", str(statistics['stock_count']))
    table.add_row("ML模型数", str(statistics['model_count']))
    table.add_row("预测记录", str(statistics['prediction_count']))

    console.print(table)


@db.command()
@click.argument("target", type=float)
@click.option("--enhance", is_flag=True, help="增强覆盖率")
def coverage(target: float, enhance: bool):
    from asset_lens.db.database import db_manager

    click.echo("\n📊 数据库覆盖率分析")
    click.echo("=" * 60)

    result = db_manager.check_coverage(target)  # type: ignore[attr-defined]

    click.echo(f"当前覆盖率: {result.get('coverage', 0):.1f}%")
    click.echo(f"目标覆盖率: {target:.1f}%")

    if result.get("coverage", 0) >= target:
        click.echo("✅ 覆盖率已达标")
    else:
        click.echo(f"⚠️ 覆盖率不足，还差 {target - result.get('coverage', 0):.1f}%")

    if enhance:
        click.echo("\n🔄 增强覆盖率...")
        sync_result = db_manager.auto_sync_history(fast=True)
        click.echo(f"✅ 已同步 {sync_result.get('synced', 0)} 只股票")


@db.command()
@click.argument("cache_file", type=click.Path(exists=True))
def migrate(cache_file: str):
    from asset_lens.db.migration import DataMigration

    click.echo("\n📊 迁移缓存数据到数据库")
    click.echo("=" * 60)

    migration = DataMigration()
    result = migration.migrate_from_cache(cache_file)  # type: ignore[attr-defined]

    click.echo(f"✅ 迁移完成: {result.get('migrated', 0)} 条记录")


@db.command("clean-old")
@click.option("--days", default=30, type=int, help="清理多少天前的数据")
@click.option("--confirm", is_flag=True, help="确认清理")
def clean_old(days: int, confirm: bool):
    from asset_lens.db.database import db_manager

    click.echo(f"\n🧹 清理 {days} 天前的旧数据")
    click.echo("=" * 60)

    if not confirm:
        click.echo("⚠️ 请使用 --confirm 确认清理操作")
        return

    result = db_manager.clean_old_data(days)  # type: ignore[attr-defined]
    click.echo(f"✅ 已清理 {result} 条旧数据")


@db.command()
def optimize():
    from asset_lens.db.database import db_manager

    click.echo("\n⚡ 优化数据库")
    click.echo("=" * 60)

    db_manager.optimize()  # type: ignore[attr-defined]
    click.echo("✅ 数据库优化完成")


@db.command()
def indexes():
    from asset_lens.db.database import db_manager

    click.echo("\n📊 数据库索引信息")
    click.echo("=" * 60)

    result = db_manager.check_indexes()  # type: ignore[attr-defined]

    if result:
        for name, info in result.items():
            click.echo(f"  {name}: {info}")
    else:
        click.echo("ℹ️ 没有索引信息")


@db.command()
@click.option("--query", default="SELECT 1", help="测试查询")
@click.option("--iterations", default=100, type=int, help="迭代次数")
def benchmark(query: str, iterations: int):
    import time

    from asset_lens.db.database import db_manager

    click.echo("\n📊 数据库性能基准测试")
    click.echo("=" * 60)

    start = time.time()
    for _ in range(iterations):
        db_manager.execute_query(query)  # type: ignore[attr-defined]
    elapsed = time.time() - start

    click.echo(f"✅ {iterations} 次查询完成，耗时 {elapsed:.3f} 秒")
    click.echo(f"   平均: {elapsed / iterations * 1000:.3f} ms/查询")


@db.command()
def vacuum():
    from asset_lens.db.database import db_manager

    click.echo("\n🧹 数据库VACUUM")
    click.echo("=" * 60)

    db_manager.vacuum()  # type: ignore[attr-defined]
    click.echo("✅ VACUUM完成")


from .db_commands import register_db_kline_commands, register_db_sync_commands

register_db_sync_commands(db)
register_db_kline_commands(db)


def register_db_commands(cli_group):
    cli_group.add_command(db)


if __name__ == "__main__":
    db()
