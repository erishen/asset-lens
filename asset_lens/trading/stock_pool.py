"""
Stock pool management for asset-lens.
股票池管理模块 - 管理观察股票、策略选股、模拟投资

功能:
1. 股票池管理 - 添加/删除/更新观察股票
2. 策略选股 - 根据策略自动选股
3. 模拟投资 - 模拟买卖操作
4. 绩效追踪 - 追踪股票池表现
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..config import config


@dataclass
class StockPosition:
    """股票持仓"""

    code: str
    name: str
    buy_price: float
    buy_date: str
    shares: int = 100
    current_price: float = 0.0
    sell_price: float | None = None
    sell_date: str | None = None
    status: str = "watching"  # watching, holding, sold
    notes: str = ""
    first_selected_date: str = ""  # 首次入选日期
    selected_count: int = 1  # 累计入选次数
    selected_history: list[dict[str, Any]] = field(default_factory=list)  # 入选历史
    max_profit_rate: float = 0.0  # 历史最高收益率
    min_profit_rate: float = 0.0  # 历史最低收益率


@dataclass
class StockPoolConfig:
    """股票池配置"""

    max_pool_size: int = 50
    auto_update: bool = True
    update_interval_days: int = 1
    min_score: float = 60.0
    strategy_name: str = "default"


class StockPool:
    """股票池管理器"""

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
        """加载股票池"""
        if self.pool_file.exists():
            try:
                with open(self.pool_file, encoding="utf-8") as f:
                    data = json.load(f)

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

            except Exception as e:
                print(f"加载股票池失败: {e}")

    def _save_pool(self) -> None:
        """保存股票池"""
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

        with open(self.pool_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_stock(
        self,
        code: str,
        name: str,
        price: float,
        status: str = "watching",
        notes: str = "",
        strategy_score: float = 0,
    ) -> tuple[bool, str]:
        """
        添加股票到股票池（支持累积）

        Args:
            code: 股票代码
            name: 股票名称
            price: 当前价格
            status: 状态 (watching/holding)
            notes: 备注
            strategy_score: 策略得分

        Returns:
            (是否添加成功, 消息)
        """
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
        self._add_history(
            "add", code, name, {"price": price, "status": status, "score": strategy_score}
        )
        self._save_pool()

        return True, f"已添加 {name}({code}) 到股票池，状态: {status}"

    def remove_stock(self, code: str, reason: str = "") -> bool:
        """
        从股票池移除股票

        Args:
            code: 股票代码
            reason: 移除原因

        Returns:
            是否移除成功
        """
        if code not in self.positions:
            print(f"股票 {code} 不在股票池中")
            return False

        pos = self.positions[code]
        self._add_history("remove", code, pos.name, {"reason": reason})
        del self.positions[code]
        self._save_pool()

        print(f"✅ 已从股票池移除 {pos.name}({code})")
        return True

    def clear_pool(self) -> int:
        """
        清空股票池

        Returns:
            清空的股票数量
        """
        count = len(self.positions)

        for code in list(self.positions.keys()):
            pos = self.positions[code]
            self._add_history("remove", code, pos.name, {"reason": "清空股票池"})

        self.positions.clear()
        self._save_pool()

        print(f"✅ 已清空股票池，共移除 {count} 只股票")
        return count

    def buy_stock(self, code: str, price: float, shares: int = 100, notes: str = "") -> tuple[bool, str]:
        """
        买入股票（模拟）

        Args:
            code: 股票代码
            price: 买入价格
            shares: 股数
            notes: 备注

        Returns:
            (是否买入成功, 消息)
        """
        if code not in self.positions:
            return False, f"股票 {code} 不在股票池中，请先添加"

        pos = self.positions[code]
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查今日是否已买入
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
        """
        卖出股票（模拟）

        Args:
            code: 股票代码
            price: 卖出价格
            notes: 备注

        Returns:
            (是否卖出成功, 消息)
        """
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

        return True, f"模拟卖出 {pos.name}({code}), 买入价: {pos.buy_price:.2f}, 卖出价: {price:.2f}, 盈亏: {profit:+.2f} ({profit_rate:+.2f}%)"

    def update_prices(self, prices: dict[str, float]) -> None:
        """
        更新股票价格

        Args:
            prices: 股票代码到价格的映射
        """
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].current_price = price

        self._save_pool()

    def get_performance(self) -> dict[str, Any]:
        """
        获取股票池绩效

        Returns:
            绩效统计
        """
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

        win_rate = (
            (win_count / (win_count + lose_count) * 100) if (win_count + lose_count) > 0 else 0
        )
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
        """添加历史记录"""
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
        """
        列出股票池中的股票

        Args:
            status: 筛选状态 (watching/holding/sold)

        Returns:
            股票列表
        """
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
        """
        获取表现最好的股票

        Args:
            top_n: 返回数量

        Returns:
            股票列表
        """
        stocks = self.list_stocks()
        stocks.sort(key=lambda x: x.get("profit_rate", 0), reverse=True)
        return stocks[:top_n]

    def get_worst_performers(self, top_n: int = 5) -> list[dict[str, Any]]:
        """
        获取表现最差的股票

        Args:
            top_n: 返回数量

        Returns:
            股票列表
        """
        stocks = self.list_stocks()
        stocks.sort(key=lambda x: x.get("profit_rate", 0))
        return stocks[:top_n]

    def add_stocks_by_strategy(
        self,
        strategy_name: str,
        stocks: list[dict[str, Any]],
        min_score: float = 60.0,
        max_stocks: int = 10,
        auto_remove_low_score: bool = False,
    ) -> dict[str, Any]:
        """
        根据策略筛选股票并添加到股票池

        Args:
            strategy_name: 策略名称
            stocks: 待筛选的股票列表
            min_score: 最低策略得分
            max_stocks: 最大添加数量
            auto_remove_low_score: 是否自动移除低分股票

        Returns:
            添加结果
        """
        from ..strategy.engine import strategy_engine

        # 使用策略筛选股票
        screened_stocks = strategy_engine.screen_stocks(
            stocks=stocks,
            strategy_name=strategy_name,
            min_score=min_score,
        )

        # 限制添加数量
        stocks_to_add = screened_stocks[:max_stocks]

        added_count = 0
        updated_count = 0
        skipped_count = 0

        for stock in stocks_to_add:
            code = stock.get("code", "")
            name = stock.get("name", "")
            score = stock.get("strategy_score", 0)

            if code in self.positions:
                # 更新现有股票的策略评分
                existing = self.positions[code]
                existing.selected_count += 1
                existing.selected_history.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "strategy": strategy_name,
                    "score": score,
                })
                updated_count += 1
            else:
                # 添加新股票（使用策略评分作为价格占位）
                self.add_stock(
                    code=code,
                    name=name,
                    price=0.0,  # 价格稍后更新
                    status="watching",
                    notes=f"策略 {strategy_name} 选入，评分: {score:.1f}",
                )
                # 设置首次入选信息
                self.positions[code].first_selected_date = datetime.now().strftime("%Y-%m-%d")
                self.positions[code].selected_count = 1
                self.positions[code].selected_history = [{
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "strategy": strategy_name,
                    "score": score,
                }]
                added_count += 1

        # 自动移除低分股票
        removed_count = 0
        if auto_remove_low_score:
            for code, position in list(self.positions.items()):
                if position.status == "watching":
                    # 检查是否在本次筛选中得分过低
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
                {"code": s.get("code"), "name": s.get("name"), "score": s.get("strategy_score")}
                for s in stocks_to_add
            ],
        }

    def get_strategy_top_stocks(self, strategy_name: str, top_n: int = 10) -> list[dict[str, Any]]:
        """
        获取股票池中某策略评分最高的股票

        Args:
            strategy_name: 策略名称
            top_n: 返回数量

        Returns:
            股票列表
        """
        stocks = self.list_stocks()

        # 筛选包含该策略历史的股票
        strategy_stocks = []
        for stock in stocks:
            history = stock.get("selected_history", [])
            for entry in history:
                if entry.get("strategy") == strategy_name:
                    strategy_stocks.append({
                        **stock,
                        "strategy_score": entry.get("score", 0),
                    })
                    break

        # 按策略评分排序
        strategy_stocks.sort(key=lambda x: x.get("strategy_score", 0), reverse=True)
        return strategy_stocks[:top_n]

    def clear_strategy_stocks(self, strategy_name: str) -> dict[str, Any]:
        """
        清除股票池中某策略选入的股票

        Args:
            strategy_name: 策略名称

        Returns:
            清除结果
        """
        removed_codes = []

        for code, position in list(self.positions.items()):
            if position.status == "watching":
                # 检查是否由该策略选入
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


stock_pool = StockPool()
