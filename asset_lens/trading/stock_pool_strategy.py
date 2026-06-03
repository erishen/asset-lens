import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..config import config


@dataclass
class StockPosition:
    code: str
    name: str
    buy_price: float
    buy_date: str
    shares: int = 100
    current_price: float = 0.0
    sell_price: float | None = None
    sell_date: str | None = None
    status: str = "watching"
    notes: str = ""
    first_selected_date: str = ""
    selected_count: int = 1
    selected_history: list[dict[str, Any]] = field(default_factory=list)
    max_profit_rate: float = 0.0
    min_profit_rate: float = 0.0


@dataclass
class StockPoolConfig:
    max_pool_size: int = 50
    auto_update: bool = True
    update_interval_days: int = 1
    min_score: float = 60.0
    strategy_name: str = "default"


class StockPoolStrategyMixin:
    def add_stocks_by_strategy(
        self,
        strategy_name: str,
        stocks: list[dict[str, Any]],
        min_score: float = 60.0,
        max_stocks: int = 10,
        auto_remove_low_score: bool = False,
    ) -> dict[str, Any]:
        from ..strategy.engine import strategy_engine

        screened_stocks = strategy_engine.screen_stocks(
            stocks=stocks,
            strategy_name=strategy_name,
            min_score=min_score,
        )

        stocks_to_add = screened_stocks[:max_stocks]

        added_count = 0
        updated_count = 0

        for stock in stocks_to_add:
            code = stock.get("code", "")
            name = stock.get("name", "")
            score = stock.get("strategy_score", 0)

            if code in self.positions:
                existing = self.positions[code]
                existing.selected_count += 1
                existing.selected_history.append(
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "strategy": strategy_name,
                        "score": score,
                    }
                )
                updated_count += 1
            else:
                self.add_stock(
                    code=code,
                    name=name,
                    price=0.0,
                    status="watching",
                    notes=f"策略 {strategy_name} 选入，评分: {score:.1f}",
                )
                self.positions[code].first_selected_date = datetime.now().strftime("%Y-%m-%d")
                self.positions[code].selected_count = 1
                self.positions[code].selected_history = [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "strategy": strategy_name,
                        "score": score,
                    }
                ]
                added_count += 1

        removed_count = 0
        if auto_remove_low_score:
            for code, position in list(self.positions.items()):
                if position.status == "watching":
                    found = False
                    for stock in stocks_to_add:
                        if stock.get("code") == code:
                            found = True
                            break
                    if not found:
                        self.remove_stock(code, reason=f"策略 {strategy_name} 得分低于 {min_score}")
                        removed_count += 1

        self._save_pool()

        return {
            "success": True,
            "strategy": strategy_name,
            "total_screened": len(screened_stocks),
            "added": added_count,
            "updated": updated_count,
            "removed": removed_count,
            "stocks_added": [
                {"code": s.get("code"), "name": s.get("name"), "score": s.get("strategy_score")} for s in stocks_to_add
            ],
        }

    def get_strategy_top_stocks(self, strategy_name: str, top_n: int = 10) -> list[dict[str, Any]]:
        stocks = self.list_stocks()

        strategy_stocks = []
        for stock in stocks:
            history = stock.get("selected_history", [])
            for entry in history:
                if entry.get("strategy") == strategy_name:
                    strategy_stocks.append(
                        {
                            **stock,
                            "strategy_score": entry.get("score", 0),
                        }
                    )
                    break

        strategy_stocks.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return strategy_stocks[:top_n]

    def clear_strategy_stocks(self, strategy_name: str) -> dict[str, Any]:
        removed_codes = []

        for code, position in list(self.positions.items()):
            if position.status == "watching":
                for entry in position.selected_history:
                    if entry.get("strategy") == strategy_name:
                        self.remove_stock(code, reason=f"清除策略 {strategy_name} 股票")
                        removed_codes.append(code)
                        break

        return {
            "success": True,
            "strategy": strategy_name,
            "removed_count": len(removed_codes),
            "removed_codes": removed_codes,
        }
