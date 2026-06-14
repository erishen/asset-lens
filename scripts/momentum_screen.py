#!/usr/bin/env python
"""
Momentum strategy screener.
使用动量策略筛选股票
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from asset_lens.data.market_stock_fetcher import MarketStockFetcher
from asset_lens.strategy.engine import StrategyEngine

console = Console()


def momentum_screen():
    """执行动量策略筛选"""
    console.print("\n📊 动量策略筛选股票")
    console.print("=" * 60)

    fetcher = MarketStockFetcher()
    stocks = fetcher.get_cached_market_stocks()
    console.print(f"市场股票总数: {len(stocks)}")

    engine = StrategyEngine()
    momentum_strategy = engine.strategies.get("momentum")

    console.print(f"\n策略: {momentum_strategy.description}")
    console.print("买入条件:")
    for cond in momentum_strategy.buy_conditions:
        console.print(f"  - {cond.name}: {cond.description}")

    results = []
    for stock in stocks:
        result = engine.evaluate_stock(stock, "momentum")
        if result.get("passed", False):
            results.append({
                "code": stock.get("code", ""),
                "name": stock.get("name", ""),
                "score": result.get("score", 0),
                "change_percent": stock.get("change_percent", 0),
                "turnover_rate": stock.get("turnover_rate", 0),
                "market_cap": stock.get("market_cap", 0),
                "current_price": stock.get("current_price", 0),
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    console.print(f"\n筛选结果: {len(results)} 只股票符合动量策略")

    if results:
        table = Table(title="动量策略筛选结果")
        table.add_column("代码", style="cyan")
        table.add_column("名称", style="white")
        table.add_column("评分", justify="right")
        table.add_column("涨幅%", justify="right")
        table.add_column("换手%", justify="right")
        table.add_column("市值(亿)", justify="right")

        for r in results[:50]:
            change_color = "green" if r["change_percent"] >= 0 else "red"
            table.add_row(
                r["code"],
                r["name"],
                f"{r['score']:.2f}",
                f"[{change_color}]{r['change_percent']:.2f}[/{change_color}]",
                f"{r['turnover_rate']:.2f}",
                f"{r['market_cap']:.1f}",
            )

        console.print(table)

    codes = [r["code"] for r in results]
    console.print(f"\n股票代码列表 ({len(codes)} 只):")
    console.print(" ".join(codes[:30]))
    if len(codes) > 30:
        console.print(" ".join(codes[30:60]))
    if len(codes) > 60:
        console.print(f"... 还有 {len(codes) - 60} 只")

    return codes


if __name__ == "__main__":
    momentum_screen()
