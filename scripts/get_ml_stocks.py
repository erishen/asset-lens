#!/usr/bin/env python
"""
Get stock codes for ML training.
获取用于ML训练的股票代码
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from asset_lens.data.market_stock_fetcher import MarketStockFetcher

console = Console()


def get_ml_training_stocks(limit: int = 200):
    """获取用于ML训练的股票代码"""
    console.print("\n📊 获取ML训练股票")
    console.print("=" * 60)

    fetcher = MarketStockFetcher()
    stocks = fetcher.get_cached_market_stocks()
    console.print(f"市场股票总数: {len(stocks)}")

    filtered_stocks = []
    for stock in stocks:
        code = stock.get("code", "")
        name = stock.get("name", "")
        if not code or not name:
            continue
        if "ST" in name or "*" in name:
            continue
        market_cap = stock.get("market_cap", 0)
        if market_cap < 30:
            continue
        filtered_stocks.append({
            "code": code,
            "name": name,
            "market_cap": market_cap,
            "change_percent": stock.get("change_percent", 0),
            "turnover_rate": stock.get("turnover_rate", 0),
        })

    filtered_stocks.sort(key=lambda x: x["market_cap"], reverse=True)

    selected = filtered_stocks[:limit]

    console.print("\n筛选条件:")
    console.print("  - 排除ST股和退市股")
    console.print("  - 市值 >= 30亿")
    console.print(f"  - 挌市值排序取前{limit}只")

    console.print(f"\n选中 {len(selected)} 只股票用于ML训练")

    table = Table(title="选中股票列表")
    table.add_column("序号", style="dim")
    table.add_column("代码", style="cyan")
    table.add_column("名称", style="white")
    table.add_column("市值(亿)", justify="right")
    table.add_column("涨跌幅", justify="right")

    for i, s in enumerate(selected, 1):
        change_color = "green" if s["change_percent"] >= 0 else "red"
        table.add_row(
            str(i),
            s["code"],
            s["name"],
            f"{s['market_cap']:.0f}",
            f"[{change_color}]{s['change_percent']:+.2f}%[/{change_color}]",
        )

    console.print(table)

    codes = [s["code"] for s in selected]
    console.print("\n股票代码列表:")
    console.print(" ".join(codes[:50]))

    return codes


if __name__ == "__main__":
    get_ml_training_stocks(200)
