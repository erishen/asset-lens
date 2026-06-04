import logging
from datetime import datetime
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache_dict, write_json_cache
from .stock_pool_strategy import StockPoolConfig, StockPoolStrategyMixin, StockPosition

logger = logging.getLogger(__name__)


class StockPool(StockPoolStrategyMixin):
    def __init__(self, pool_name: str = "default"):
        self.pool_name = pool_name
        self.pool_path = config.cache_path / "stock_pools"
        self.pool_path.mkdir(parents=True, exist_ok=True)
        self.pool_file = self.pool_path / f"{pool_name}_pool.json"
        self.positions: dict[str, StockPosition] = {}
        self.config = StockPoolConfig()
        self.history: list[dict[str, Any]] = []
        self._load_pool()

    def _load_pool(self) -> None:
        data = read_json_cache_dict(self.pool_file)
        if data is None:
            return

        for code, pos_data in data.get("positions", {}).items():
            self.positions[code] = StockPosition(
                code=pos_data.get("code", ""),
                name=pos_data.get("name", ""),
                buy_price=pos_data.get("buy_price", 0),
                buy_date=pos_data.get("buy_date", ""),
                shares=pos_data.get("shares", 100),
                current_price=pos_data.get("current_price", 0),
                sell_price=pos_data.get("sell_price"),
                sell_date=pos_data.get("sell_date"),
                status=pos_data.get("status", "watching"),
                notes=pos_data.get("notes", ""),
                first_selected_date=pos_data.get("first_selected_date", ""),
                selected_count=pos_data.get("selected_count", 1),
                selected_history=pos_data.get("selected_history", []),
                max_profit_rate=pos_data.get("max_profit_rate", 0.0),
                min_profit_rate=pos_data.get("min_profit_rate", 0.0),
            )

        self.history = data.get("history", [])

        config_data = data.get("config", {})
        self.config = StockPoolConfig(
            max_pool_size=config_data.get("max_pool_size", 50),
            auto_update=config_data.get("auto_update", True),
            update_interval_days=config_data.get("update_interval_days", 1),
            min_score=config_data.get("min_score", 60.0),
            strategy_name=config_data.get("strategy_name", "default"),
        )

    def _save_pool(self) -> None:
        data = {
            "pool_name": self.pool_name,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "max_pool_size": self.config.max_pool_size,
                "auto_update": self.config.auto_update,
                "update_interval_days": self.config.update_interval_days,
                "min_score": self.config.min_score,
                "strategy_name": self.config.strategy_name,
            },
            "positions": {
                code: {
                    "code": pos.code,
                    "name": pos.name,
                    "buy_price": pos.buy_price,
                    "buy_date": pos.buy_date,
                    "shares": pos.shares,
                    "current_price": pos.current_price,
                    "sell_price": pos.sell_price,
                    "sell_date": pos.sell_date,
                    "status": pos.status,
                    "notes": pos.notes,
                    "first_selected_date": pos.first_selected_date,
                    "selected_count": pos.selected_count,
                    "selected_history": pos.selected_history,
                    "max_profit_rate": pos.max_profit_rate,
                    "min_profit_rate": pos.min_profit_rate,
                }
                for code, pos in self.positions.items()
            },
            "history": self.history,
        }

        write_json_cache(self.pool_file, data)

    def add_stock(
        self,
        code: str,
        name: str,
        price: float,
        status: str = "watching",
        notes: str = "",
        strategy_score: float = 0,
    ) -> tuple[bool, str]:
        today = datetime.now().strftime("%Y-%m-%d")

        if code in self.positions:
            pos = self.positions[code]

            today_records = [h for h in pos.selected_history if h.get("date", "") == today]
            if today_records:
                return False, f"{name}({code}) 今日已入选，跳过重复记录"

            pos.selected_count += 1
            pos.selected_history.append(
                {
                    "date": today,
                    "price": price,
                    "score": strategy_score,
                    "notes": notes,
                }
            )
            pos.current_price = price
            pos.notes = notes

            self._add_history(
                "reselect",
                code,
                name,
                {
                    "price": price,
                    "score": strategy_score,
                    "count": pos.selected_count,
                },
            )
            self._save_pool()

            return True, f"{name}({code}) 再次入选，累计入选 {pos.selected_count} 次"

        if len(self.positions) >= self.config.max_pool_size:
            return False, f"股票池已满 (最大 {self.config.max_pool_size} 只)"

        position = StockPosition(
            code=code,
            name=name,
            buy_price=price if status == "holding" else 0,
            buy_date=today if status == "holding" else "",
            current_price=price,
            status=status,
            notes=notes,
            first_selected_date=today,
            selected_count=1,
            selected_history=[
                {
                    "date": today,
                    "price": price,
                    "score": strategy_score,
                    "notes": notes,
                }
            ],
        )

        self.positions[code] = position
        self._add_history("add", code, name, {"price": price, "status": status, "score": strategy_score})
        self._save_pool()

        return True, f"已添加 {name}({code}) 到股票池，状态: {status}"

    def remove_stock(self, code: str, reason: str = "") -> bool:
        if code not in self.positions:
            logger.warning(f"股票 {code} 不在股票池中")
            return False

        pos = self.positions[code]
        self._add_history("remove", code, pos.name, {"reason": reason})
        del self.positions[code]
        self._save_pool()

        logger.info(f"已从股票池移除 {pos.name}({code})")
        return True

    def clear_pool(self) -> int:
        count = len(self.positions)

        for code in list(self.positions.keys()):
            pos = self.positions[code]
            self._add_history("remove", code, pos.name, {"reason": "清空股票池"})

        self.positions.clear()
        self._save_pool()

        logger.info(f"已清空股票池，共移除 {count} 只股票")
        return count

    def buy_stock(self, code: str, price: float, shares: int = 100, notes: str = "") -> tuple[bool, str]:
        if code not in self.positions:
            return False, f"股票 {code} 不在股票池中，请先添加"

        pos = self.positions[code]
        today = datetime.now().strftime("%Y-%m-%d")

        if pos.status == "holding" and pos.buy_date == today:
            return False, f"股票 {pos.name}({code}) 今日已买入，跳过重复操作"

        if pos.status == "holding":
            return False, f"股票 {pos.name}({code}) 已持有"

        pos.status = "holding"
        pos.buy_price = price
        pos.buy_date = today
        pos.shares = shares
        pos.notes = notes

        self._add_history(
            "buy",
            code,
            pos.name,
            {
                "price": price,
                "shares": shares,
                "total": price * shares,
            },
        )
        self._save_pool()

        return True, f"模拟买入 {pos.name}({code}), 买入价: {price:.2f}, 股数: {shares}, 总金额: {price * shares:.2f}"

    def sell_stock(self, code: str, price: float, notes: str = "") -> tuple[bool, str]:
        if code not in self.positions:
            return False, f"股票 {code} 不在股票池中"

        pos = self.positions[code]
        if pos.status != "holding":
            return False, f"股票 {pos.name}({code}) 未持有"

        profit = (price - pos.buy_price) * pos.shares
        profit_rate = (price - pos.buy_price) / pos.buy_price * 100

        pos.status = "sold"
        pos.sell_price = price
        pos.sell_date = datetime.now().strftime("%Y-%m-%d")
        pos.notes = notes

        self._add_history(
            "sell",
            code,
            pos.name,
            {
                "buy_price": pos.buy_price,
                "sell_price": price,
                "shares": pos.shares,
                "profit": profit,
                "profit_rate": profit_rate,
            },
        )
        self._save_pool()

        return (
            True,
            f"模拟卖出 {pos.name}({code}), 买入价: {pos.buy_price:.2f}, 卖出价: {price:.2f}, 盈亏: {profit:+.2f} ({profit_rate:+.2f}%)",
        )

    def update_prices(self, prices: dict[str, float]) -> None:
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].current_price = price

        self._save_pool()

    def get_performance(self) -> dict[str, Any]:
        watching = []
        holding = []
        sold = []

        for pos in self.positions.values():
            if pos.status == "watching":
                watching.append(pos)
            elif pos.status == "holding":
                holding.append(pos)
            elif pos.status == "sold":
                sold.append(pos)

        total_profit: float = 0
        total_invested: float = 0
        win_count: int = 0
        lose_count: int = 0

        for pos in sold:
            if pos.sell_price and pos.buy_price:
                profit = (pos.sell_price - pos.buy_price) * pos.shares
                total_profit += float(profit)
                total_invested += float(pos.buy_price * pos.shares)
                if profit > 0:
                    win_count += 1
                else:
                    lose_count += 1

        for pos in holding:
            if pos.current_price and pos.buy_price:
                profit = (pos.current_price - pos.buy_price) * pos.shares
                total_profit += float(profit)
                total_invested += float(pos.buy_price * pos.shares)

        win_rate = (win_count / (win_count + lose_count) * 100) if (win_count + lose_count) > 0 else 0
        profit_rate = (total_profit / total_invested * 100) if total_invested > 0 else 0

        return {
            "pool_name": self.pool_name,
            "total_stocks": len(self.positions),
            "watching_count": len(watching),
            "holding_count": len(holding),
            "sold_count": len(sold),
            "total_profit": round(total_profit, 2),
            "profit_rate": round(profit_rate, 2),
            "win_count": win_count,
            "lose_count": lose_count,
            "win_rate": round(win_rate, 2),
            "total_invested": round(total_invested, 2),
        }

    def _add_history(self, action: str, code: str, name: str, data: dict[str, Any]) -> None:
        self.history.append(
            {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
                "code": code,
                "name": name,
                "data": data,
            }
        )

    def list_stocks(self, status: str | None = None) -> list[dict[str, Any]]:
        result = []
        for pos in self.positions.values():
            if status is None or pos.status == status:
                profit: float = 0
                profit_rate: float = 0
                if pos.status == "holding" and pos.current_price and pos.buy_price:
                    profit = float((pos.current_price - pos.buy_price) * pos.shares)
                    profit_rate = float((pos.current_price - pos.buy_price) / pos.buy_price * 100)
                elif pos.status == "sold" and pos.sell_price and pos.buy_price:
                    profit = float((pos.sell_price - pos.buy_price) * pos.shares)
                    profit_rate = float((pos.sell_price - pos.buy_price) / pos.buy_price * 100)

                result.append(
                    {
                        "code": pos.code,
                        "name": pos.name,
                        "status": pos.status,
                        "buy_price": pos.buy_price,
                        "current_price": pos.current_price,
                        "sell_price": pos.sell_price,
                        "shares": pos.shares,
                        "profit": round(profit, 2),
                        "profit_rate": round(profit_rate, 2),
                        "buy_date": pos.buy_date,
                        "sell_date": pos.sell_date,
                        "notes": pos.notes,
                        "selected_count": pos.selected_count,
                        "first_selected_date": pos.first_selected_date,
                    }
                )

        return result

    def get_best_performers(self, top_n: int = 5) -> list[dict[str, Any]]:
        stocks = self.list_stocks()
        stocks.sort(key=lambda x: x.get("profit_rate", 0), reverse=True)
        return stocks[:top_n]

    def get_worst_performers(self, top_n: int = 5) -> list[dict[str, Any]]:
        stocks = self.list_stocks()
        stocks.sort(key=lambda x: x.get("profit_rate", 0))
        return stocks[:top_n]


stock_pool = StockPool()
