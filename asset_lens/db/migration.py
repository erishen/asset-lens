"""
Data migration tool for asset-lens.
数据迁移工具 - 将JSON缓存迁移到数据库
"""

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from ..config import config
from .database import DatabaseManager

console = Console()


class DataMigration:
    """数据迁移工具"""

    def __init__(self, db_manager: DatabaseManager | None = None):
        self.db = db_manager or DatabaseManager()
        self.cache_path = config.cache_path

    def migrate_history_cache(
        self,
        cache_file: Path | None = None,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """
        迁移历史K线数据缓存到数据库

        Args:
            cache_file: 缓存文件路径
            batch_size: 批量处理大小

        Returns:
            迁移结果统计
        """
        if cache_file is None:
            cache_file = self.cache_path / "stock_history_baostock.json"

        if not cache_file.exists():
            console.print(f"[yellow]缓存文件不存在: {cache_file}[/yellow]")
            return {"status": "skipped", "reason": "cache_not_found"}

        console.print("[bold blue]开始迁移历史数据缓存...[/bold blue]")
        console.print(f"  源文件: {cache_file}")

        with open(cache_file, encoding="utf-8") as f:
            cache_data: dict[str, Any] = json.load(f)

        histories: dict[str, dict[str, Any]] = cache_data.get("data", {})
        total_stocks = len(histories)

        if total_stocks == 0:
            console.print("[yellow]缓存数据为空[/yellow]")
            return {"status": "skipped", "reason": "empty_cache"}

        console.print(f"  股票数量: {total_stocks}")

        result: dict[str, Any] = {
            "status": "success",
            "total_stocks": total_stocks,
            "total_klines": 0,
            "success_count": 0,
            "failed_count": 0,
            "errors": [],
        }

        log_id = self.db.log_sync(
            data_type="kline",
            data_source="migration",
            records_total=total_stocks,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("迁移中...", total=total_stocks)

            for _i, (code, history) in enumerate(histories.items()):
                try:
                    klines: list[dict[str, Any]] = history.get("klines", [])
                    data_source = history.get("data_source", "Unknown")

                    if klines:
                        self.db.save_klines(code, klines, data_source)
                        result["total_klines"] += len(klines)
                        result["success_count"] += 1
                    else:
                        result["failed_count"] += 1

                except Exception as e:
                    result["failed_count"] += 1
                    result["errors"].append({"code": code, "error": str(e)})

                progress.update(task, advance=1, description=f"迁移 {code}")

        self.db.update_sync_log(
            log_id,
            records_success=result["success_count"],
            records_failed=result["failed_count"],
            status="success" if result["failed_count"] == 0 else "partial",
        )

        console.print("\n[bold green]迁移完成![/bold green]")
        console.print(f"  成功: {result['success_count']} 只股票")
        console.print(f"  失败: {result['failed_count']} 只股票")
        console.print(f"  K线总数: {result['total_klines']} 条")

        return result

    def fetch_and_store_history(
        self,
        codes: list[str],
        days: int = 250,
        data_source: str = "auto",
        delay: float = 0.3,
    ) -> dict[str, Any]:
        """
        获取并存储历史K线数据

        Args:
            codes: 股票代码列表
            days: 历史天数
            data_source: 数据源 (auto/tushare/baostock/akshare)
            delay: 请求间隔

        Returns:
            获取结果统计
        """
        from ..data.stock_history_fetcher import StockHistoryFetcher

        console.print("[bold blue]开始获取历史数据...[/bold blue]")
        console.print(f"  股票数量: {len(codes)}")
        console.print(f"  历史天数: {days}")
        console.print(f"  数据源: {data_source}")

        fetcher = StockHistoryFetcher()
        result: dict[str, Any] = {
            "total": len(codes),
            "success": 0,
            "failed": 0,
            "total_klines": 0,
            "errors": [],
        }

        log_id = self.db.log_sync(
            data_type="kline",
            data_source=data_source,
            records_total=len(codes),
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("获取中...", total=len(codes))

            for code in codes:
                try:
                    if data_source == "tushare":
                        history = fetcher.fetch_history_tushare(code, days)
                    elif data_source == "baostock":
                        history = fetcher.fetch_history_baostock(code, days)
                    elif data_source == "akshare":
                        history = fetcher.fetch_history_akshare_daily(code, days)
                    else:
                        history = fetcher.fetch_history(code, days)

                    if history:
                        klines: list[dict[str, Any]] = history.get("klines", [])
                        source = history.get("data_source", "Unknown")
                        self.db.save_klines(code, klines, source)
                        result["success"] += 1
                        result["total_klines"] += len(klines)
                    else:
                        result["failed"] += 1

                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append({"code": code, "error": str(e)})

                progress.update(task, advance=1, description=f"获取 {code}")

                if delay > 0:
                    import time

                    time.sleep(delay)

        fetcher.baostock_logout()

        self.db.update_sync_log(
            log_id,
            records_success=result["success"],
            records_failed=result["failed"],
            status="success" if result["failed"] == 0 else "partial",
        )

        console.print("\n[bold green]获取完成![/bold green]")
        console.print(f"  成功: {result['success']} 只股票")
        console.print(f"  失败: {result['failed']} 只股票")
        console.print(f"  K线总数: {result['total_klines']} 条")

        return result

    def fetch_and_store_history_concurrent(
        self,
        codes: list[str],
        days: int = 250,
        data_source: str = "auto",
        max_workers: int = 5,
        batch_delay: float = 0.1,
    ) -> dict[str, Any]:
        """
        并发获取并存储历史K线数据

        Args:
            codes: 股票代码列表
            days: 历史天数
            data_source: 数据源 (auto/tushare/baostock/akshare)
            max_workers: 最大并发数
            batch_delay: 批次间隔

        Returns:
            获取结果统计
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from ..data.stock_history_fetcher import StockHistoryFetcher

        console.print("[bold blue]开始并发获取历史数据...[/bold blue]")
        console.print(f"  股票数量: {len(codes)}")
        console.print(f"  历史天数: {days}")
        console.print(f"  数据源: {data_source}")
        console.print(f"  并发数: {max_workers}")

        fetcher = StockHistoryFetcher()
        result: dict[str, Any] = {
            "total": len(codes),
            "success": 0,
            "failed": 0,
            "total_klines": 0,
            "errors": [],
        }
        result_lock = threading.Lock()

        def fetch_single(code: str) -> tuple[str, dict[str, Any] | None, str | None]:
            try:
                if data_source == "tushare":
                    history = fetcher.fetch_history_tushare(code, days)
                elif data_source == "baostock":
                    history = fetcher.fetch_history_baostock(code, days)
                elif data_source == "akshare":
                    history = fetcher.fetch_history_akshare_daily(code, days)
                else:
                    history = fetcher.fetch_history(code, days)
                return (code, history, None)
            except Exception as e:
                return (code, None, str(e))

        log_id = self.db.log_sync(
            data_type="kline",
            data_source=data_source,
            records_total=len(codes),
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("并发获取中...", total=len(codes))
            completed = 0

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_single, code): code for code in codes}

                for future in as_completed(futures):
                    code, history, error = future.result()

                    with result_lock:
                        if history:
                            klines: list[dict[str, Any]] = history.get("klines", [])
                            source = history.get("data_source", "Unknown")
                            self.db.save_klines(code, klines, source)
                            result["success"] += 1
                            result["total_klines"] += len(klines)
                        else:
                            result["failed"] += 1
                            if error:
                                result["errors"].append({"code": code, "error": error})

                    completed += 1
                    progress.update(task, completed=completed, description=f"获取 {code}")

                    if batch_delay > 0 and completed % max_workers == 0:
                        import time

                        time.sleep(batch_delay)

        fetcher.baostock_logout()

        self.db.update_sync_log(
            log_id,
            records_success=result["success"],
            records_failed=result["failed"],
            status="success" if result["failed"] == 0 else "partial",
        )

        console.print("\n[bold green]并发获取完成![/bold green]")
        console.print(f"  成功: {result['success']} 只股票")
        console.print(f"  失败: {result['failed']} 只股票")
        console.print(f"  K线总数: {result['total_klines']} 条")

        return result

    def show_statistics(self):
        """显示数据库统计信息"""
        stats = self.db.get_statistics()

        table = Table(title="数据库统计")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        table.add_row("K线数据总数", f"{stats['kline_count']:,}")
        table.add_row("股票数量", f"{stats['stock_count']:,}")
        table.add_row("ML模型数量", str(stats["model_count"]))
        table.add_row("预测记录数", str(stats["prediction_count"]))
        table.add_row("最新数据日期", stats["latest_date"] or "无数据")

        console.print(table)

        if stats["data_sources"]:
            source_table = Table(title="数据来源分布")
            source_table.add_column("数据源", style="cyan")
            source_table.add_column("记录数", style="green")

            for source, count in stats["data_sources"].items():
                source_table.add_row(source, f"{count:,}")

            console.print(source_table)

    def verify_data(self, sample_size: int = 10) -> dict[str, Any]:
        """
        验证数据完整性

        Args:
            sample_size: 抽样检查数量

        Returns:
            验证结果
        """
        console.print("[bold blue]验证数据完整性...[/bold blue]")

        codes = self.db.get_stock_codes()
        if not codes:
            return {"status": "no_data"}

        import random

        sample_codes = random.sample(codes, min(sample_size, len(codes)))

        result: dict[str, Any] = {
            "total_stocks": len(codes),
            "sample_size": len(sample_codes),
            "issues": [],
        }

        for code in sample_codes:
            klines = self.db.get_klines(code, limit=500)
            if len(klines) < 30:
                result["issues"].append(
                    {
                        "code": code,
                        "issue": "数据不足",
                        "count": len(klines),
                    }
                )

        if result["issues"]:
            console.print(f"[yellow]发现 {len(result['issues'])} 个问题[/yellow]")
        else:
            console.print("[green]数据验证通过[/green]")

        return result


def migrate_from_json():
    """从JSON缓存迁移到数据库"""
    migration = DataMigration()
    return migration.migrate_history_cache()


def fetch_history_to_db(codes: list[str], days: int = 250, data_source: str = "auto"):
    """获取历史数据并存储到数据库"""
    migration = DataMigration()
    return migration.fetch_and_store_history(codes, days, data_source)
