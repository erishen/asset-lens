#!/usr/bin/env python
"""
Batch fetch stock history data to database.
批量获取股票历史K线数据到数据库
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from asset_lens.data.market_stock_fetcher import MarketStockFetcher
from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
from asset_lens.db.database import db_manager

console = Console()


def get_stock_codes(source: str = "market", limit: int = 0) -> list:
    """
    获取股票代码列表

    Args:
        source: 数据来源 (market/custom)
        limit: 限制数量，0表示不限制

    Returns:
        股票代码列表
    """
    if source == "market":
        fetcher = MarketStockFetcher()
        stocks = fetcher.get_cached_market_stocks()
        codes = [s.get("code", "") for s in stocks if s.get("code")]
    else:
        codes = []

    if limit > 0:
        codes = codes[:limit]

    return codes


def batch_fetch(
    codes: list,
    days: int = 250,
    batch_size: int = 50,
    delay: float = 0.2,
    data_source: str = "auto",
):
    """
    批量获取历史数据

    Args:
        codes: 股票代码列表
        days: 历史天数
        batch_size: 每批数量
        delay: 请求间隔
        data_source: 数据源
    """
    total = len(codes)
    success_count = 0
    failed_count = 0
    total_klines = 0
    failed_codes = []

    history_fetcher = StockHistoryFetcher()

    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("获取中...", total=total)

        for i, code in enumerate(codes):
            try:
                if data_source == "tushare":
                    history = history_fetcher.fetch_history_tushare(code, days)
                elif data_source == "baostock":
                    history = history_fetcher.fetch_history_baostock(code, days)
                elif data_source == "akshare":
                    history = history_fetcher.fetch_history_akshare_daily(code, days)
                else:
                    history = history_fetcher.fetch_history(code, days)

                if history and history.get("klines"):
                    klines = history.get("klines", [])
                    source = history.get("data_source", "Unknown")
                    db_manager.save_klines(code, klines, source)
                    success_count += 1
                    total_klines += len(klines)
                else:
                    failed_count += 1
                    failed_codes.append(code)

            except Exception:
                failed_count += 1
                failed_codes.append(code)

            progress.update(task, advance=1, description=f"获取 {code}")

            if delay > 0:
                time.sleep(delay)

            if (i + 1) % batch_size == 0:
                console.print(f"  批次完成: {i + 1}/{total} | 成功: {success_count} | 失败: {failed_count}")

    history_fetcher.baostock_logout()

    elapsed_time = time.time() - start_time

    console.print("\n✅ 批量获取完成!")
    console.print(f"   成功: {success_count} 只股票")
    console.print(f"   失败: {failed_count} 只股票")
    console.print(f"   K线总数: {total_klines:,} 条")
    console.print(f"   耗时: {elapsed_time/60:.1f} 分钟")

    if failed_codes and len(failed_codes) <= 20:
        console.print("\n⚠️ 失败的股票代码:")
        for code in failed_codes:
            console.print(f"   {code}")


def main():
    parser = argparse.ArgumentParser(description="批量获取股票历史数据")
    parser.add_argument("--days", type=int, default=250, help="历史天数 (默认: 250)")
    parser.add_argument("--limit", type=int, default=0, help="限制股票数量 (默认: 0=不限制)")
    parser.add_argument("--batch-size", type=int, default=50, help="每批数量 (默认: 50)")
    parser.add_argument("--delay", type=float, default=0.2, help="请求间隔秒数 (默认: 0.2)")
    parser.add_argument("--source", default="market", help="数据来源 (market/custom)")
    parser.add_argument("--data-source", default="auto", help="K线数据源 (auto/tushare/baostock/akshare)")
    parser.add_argument("--codes", nargs="+", help="指定股票代码列表")

    args = parser.parse_args()

    console.print("\n" + "=" * 60)
    console.print("  📦 批量获取股票历史数据")
    console.print("=" * 60)

    codes = args.codes or get_stock_codes(args.source, args.limit)

    if not codes:
        console.print("[red]❌ 没有找到股票代码[/red]")
        return

    console.print(f"\n📋 获取 {len(codes)} 只股票的历史数据...")
    console.print(f"   历史天数: {args.days}")
    console.print(f"   数据源: {args.data_source}")
    console.print(f"   请求间隔: {args.delay}秒")

    batch_fetch(
        codes=codes,
        days=args.days,
        batch_size=args.batch_size,
        delay=args.delay,
        data_source=args.data_source,
    )

    stats = db_manager.get_statistics()
    console.print("\n📊 数据库统计:")
    console.print(f"   K线数据: {stats['kline_count']:,} 条")
    console.print(f"   股票数量: {stats['stock_count']}")
    console.print(f"   最新日期: {stats['latest_date']}")


if __name__ == "__main__":
    main()
