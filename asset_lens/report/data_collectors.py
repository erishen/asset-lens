"""
Report Data Collectors - 报告数据收集器

提供统一的数据收集功能，支持渐进式重构。
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CollectedData:
    """收集的数据"""

    timestamp: str
    data: dict[str, Any]
    source: str


class ReportDataCollector:
    """报告数据收集器 - 统一收集报告所需的数据"""

    def __init__(self):
        self.collected: dict[str, CollectedData] = {}

    def collect_portfolio_data(
        self,
        products: list[Any],
    ) -> dict[str, Any]:
        """
        收集投资组合数据

        Args:
            products: 投资产品列表

        Returns:
            投资组合数据
        """
        total_amount = Decimal("0")
        total_cost = Decimal("0")
        by_type: dict[str, dict[str, Decimal]] = {}
        by_platform: dict[str, dict[str, Decimal]] = {}

        for product in products:
            amount = getattr(product, "current_amount", Decimal("0")) or Decimal("0")
            cost = getattr(product, "initial_amount", Decimal("0")) or Decimal("0")

            total_amount += amount
            total_cost += cost

            ptype = str(getattr(product, "investment_type", "其他") or "其他")
            if ptype not in by_type:
                by_type[ptype] = {"amount": Decimal("0"), "cost": Decimal("0")}
            by_type[ptype]["amount"] += amount
            by_type[ptype]["cost"] += cost

            platform = str(getattr(product, "platform", "未知") or "未知")
            if platform not in by_platform:
                by_platform[platform] = {"amount": Decimal("0"), "cost": Decimal("0")}
            by_platform[platform]["amount"] += amount
            by_platform[platform]["cost"] += cost

        profit = total_amount - total_cost
        profit_rate = (profit / total_cost * 100) if total_cost > 0 else Decimal("0")

        data = {
            "total_amount": float(total_amount),
            "total_cost": float(total_cost),
            "total_profit": float(profit),
            "profit_rate": float(profit_rate),
            "by_type": {k: {"amount": float(v["amount"]), "cost": float(v["cost"])} for k, v in by_type.items()},
            "by_platform": {
                k: {"amount": float(v["amount"]), "cost": float(v["cost"])} for k, v in by_platform.items()
            },
            "product_count": len(products),
        }

        self.collected["portfolio"] = CollectedData(
            timestamp=datetime.now().isoformat(),
            data=data,
            source="portfolio",
        )

        return data

    def collect_market_data(
        self,
        indexes: dict[str, Any],
    ) -> dict[str, Any]:
        """
        收集市场数据

        Args:
            indexes: 指数数据

        Returns:
            市场数据
        """
        data = {
            "indexes": indexes,
            "collect_time": datetime.now().isoformat(),
        }

        self.collected["market"] = CollectedData(
            timestamp=datetime.now().isoformat(),
            data=data,
            source="market",
        )

        return data

    def collect_performance_data(
        self,
        performance_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        收集业绩数据

        Args:
            performance_history: 业绩历史

        Returns:
            业绩数据
        """
        if not performance_history:
            return {"history": [], "summary": {}}

        total_profit = sum(item.get("profit", 0) for item in performance_history)
        avg_profit = total_profit / len(performance_history) if performance_history else 0

        data = {
            "history": performance_history,
            "summary": {
                "total_profit": total_profit,
                "avg_profit": avg_profit,
                "record_count": len(performance_history),
            },
        }

        self.collected["performance"] = CollectedData(
            timestamp=datetime.now().isoformat(),
            data=data,
            source="performance",
        )

        return data

    def get_collected_data(self, key: str) -> dict[str, Any] | None:
        """
        获取已收集的数据

        Args:
            key: 数据键

        Returns:
            数据字典
        """
        collected = self.collected.get(key)
        return collected.data if collected else None

    def get_all_collected(self) -> dict[str, dict[str, Any]]:
        """
        获取所有已收集的数据

        Returns:
            所有数据字典
        """
        return {key: item.data for key, item in self.collected.items()}

    def clear(self):
        """清除已收集的数据"""
        self.collected.clear()
