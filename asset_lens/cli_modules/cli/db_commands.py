import click


def register_db_sync_commands(db_group: click.Group) -> None:
    @db_group.command()
    @click.option("--codes", "codes_str", help="股票代码列表（逗号分隔）")
    @click.option("--days", default=250, help="历史天数")
    @click.option("--source", default="auto", type=click.Choice(["auto", "akshare", "baostock", "tushare"]), help="数据源")
    @click.option("--delay", default=0.3, type=float, help="请求间隔（秒）")
    def fetch(codes_str: str | None, days: int, source: str, delay: float):
        from asset_lens.db.migration import DataMigration

        click.echo("\n📊 获取股票历史K线数据")
        click.echo("=" * 60)

        if not codes_str:
            click.echo("❌ 请指定股票代码列表", err=True)
            return

        codes = [c.strip() for c in codes_str.split(",") if c.strip()]

        migration = DataMigration()
        result = migration.fetch_and_store_history(codes=codes, days=days, data_source=source, delay=delay)

        click.echo(f"\n✅ 成功: {result.get('success', 0)}, ❌ 失败: {result.get('failed', 0)}")

    @db_group.command("update-missing")
    @click.option("--days", default=250, help="历史天数")
    @click.option("--limit", default=0, type=int, help="限制数量（0=不限制）")
    @click.option("--delay", default=0.3, type=float, help="请求间隔（秒）")
    @click.option("--source", default="auto", type=click.Choice(["auto", "akshare", "baostock", "tushare"]), help="数据源")
    def update_missing(days: int, limit: int, delay: float, source: str) -> None:
        from rich.console import Console

        from asset_lens.db.database import db_manager

        Console()

        click.echo("\n📊 更新缺失的K线数据")
        click.echo("=" * 60)

        missing_codes = db_manager.get_stock_codes_without_klines()

        if not missing_codes:
            click.echo("✅ 没有缺失的K线数据")
            return

        click.echo(f"📋 找到 {len(missing_codes)} 只股票缺少K线数据")

        if limit > 0:
            missing_codes = missing_codes[:limit]
            click.echo(f"📋 限制更新前 {limit} 只股票")

        from asset_lens.db.migration import DataMigration

        migration = DataMigration()
        result = migration.fetch_and_store_history(codes=missing_codes, days=days, data_source=source, delay=delay)

        click.echo(f"\n📊 更新结果:")
        click.echo(f"   ✅ 成功: {result.get('success', 0)}")
        click.echo(f"   ❌ 失败: {result.get('failed', 0)}")
        click.echo(f"   📈 K线总数: {result.get('total_klines', 0)}")

    @db_group.command("auto-sync")
    @click.option("--days", default=250, help="历史天数")
    @click.option("--daily-limit", default=100, type=int, help="每日同步限制")
    @click.option("--update-limit", default=50, type=int, help="更新限制")
    @click.option("--delay", default=0.3, type=float, help="请求间隔（秒）")
    @click.option("--fast", is_flag=True, help="快速模式")
    def auto_sync(days: int, daily_limit: int, update_limit: int, delay: float, fast: bool):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.db.database import db_manager

        console = Console()

        click.echo("\n🔄 自动同步股票历史数据")
        click.echo("=" * 60)

        try:
            sync_result = db_manager.auto_sync_history(
                fast=fast,
                days=days,
                daily_limit=daily_limit,
                update_limit=update_limit,
            )

            synced = sync_result.get("synced", 0)
            updated = sync_result.get("updated", 0)
            failed = sync_result.get("failed", 0)

            click.echo(f"\n📊 同步结果:")
            click.echo(f"   ✅ 新同步: {synced} 只股票")
            click.echo(f"   🔄 已更新: {updated} 只股票")
            click.echo(f"   ❌ 失败: {failed} 只股票")

            if fast:
                click.echo("\n💡 快速模式：仅同步部分股票数据")

            stats = db_manager.get_statistics()
            table = Table(title="数据库统计")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")

            table.add_row("K线数据", f"{stats['kline_count']:,} 条")
            table.add_row("股票数量", str(stats['stock_count']))
            table.add_row("ML模型数", str(stats['model_count']))
            table.add_row("预测记录", str(stats['prediction_count']))

            console.print(table)

        except Exception as e:
            click.echo(f"\n❌ 同步失败: {e}", err=True)


def register_db_kline_commands(db_group: click.Group) -> None:
    @db_group.command()
    @click.argument("code")
    @click.option("--start", help="开始日期 (YYYY-MM-DD)")
    @click.option("--end", help="结束日期 (YYYY-MM-DD)")
    @click.option("--limit", default=10, type=int, help="显示条数")
    def kline(code: str, start: str | None, end: str | None, limit: int):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.db.database import db_manager

        console = Console()

        click.echo(f"\n📊 查询K线数据: {code}")
        click.echo("=" * 60)

        klines = db_manager.get_klines(code, start_date=start, end_date=end, limit=limit)

        if not klines:
            click.echo("❌ 没有找到K线数据", err=True)
            return

        table = Table(title=f"K线数据: {code}")
        table.add_column("日期", style="cyan")
        table.add_column("开盘", style="green")
        table.add_column("收盘", style="green")
        table.add_column("最高", style="red")
        table.add_column("最低", style="green")
        table.add_column("成交量", style="yellow")

        for k in klines[:limit]:
            table.add_row(
                str(k.get("date", "")),
                f"{k.get('open', 0):.2f}",
                f"{k.get('close', 0):.2f}",
                f"{k.get('high', 0):.2f}",
                f"{k.get('low', 0):.2f}",
                f"{k.get('volume', 0):,}",
            )

        console.print(table)

    @db_group.command()
    @click.option("--days", default=30, type=int, help="清理多少天前的数据")
    def clean(days: int):
        from asset_lens.db.database import db_manager

        click.echo(f"\n🧹 清理 {days} 天前的K线数据")
        click.echo("=" * 60)

        result = db_manager.clean_old_klines(days)

        click.echo(f"✅ 已清理 {result} 条K线数据")

    @db_group.command()
    def verify():
        from asset_lens.db.database import db_manager

        click.echo("\n🔍 验证K线数据完整性")
        click.echo("=" * 60)

        result = db_manager.verify_kline_data()

        click.echo(f"✅ 验证完成: {result.get('valid', 0)} 条有效, {result.get('invalid', 0)} 条无效")

    @db_group.command()
    @click.argument("code")
    def info(code: str):
        from asset_lens.db.database import db_manager

        click.echo(f"\n📊 股票信息: {code}")
        click.echo("=" * 60)

        info = db_manager.get_stock_info(code)

        if info:
            for key, value in info.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo("❌ 未找到股票信息", err=True)

    @db_group.command()
    def codes():
        from asset_lens.db.database import db_manager

        click.echo("\n📊 数据库中的股票代码列表")
        click.echo("=" * 60)

        code_list = db_manager.get_stock_codes_with_klines()

        if code_list:
            click.echo(f"共 {len(code_list)} 只股票:")
            for code in code_list[:50]:
                click.echo(f"  {code}")
            if len(code_list) > 50:
                click.echo(f"  ... 还有 {len(code_list) - 50} 只")
        else:
            click.echo("❌ 数据库中没有K线数据", err=True)
