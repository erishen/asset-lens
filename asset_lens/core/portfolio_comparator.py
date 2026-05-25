"""
Portfolio Comparator - 投资组合快照对比模块
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any


class PortfolioComparator:
    """投资组合对比器 - 提供快照对比功能"""

    def __init__(self):
        self._snapshots: list[dict[str, Any]] = []

    def compare_weekly(self) -> dict[str, Any] | None:
        """周度对比"""
        if len(self._snapshots) < 2:
            return None

        sorted_snapshots = sorted(self._snapshots, key=lambda x: x.get("timestamp", ""), reverse=True)
        latest = sorted_snapshots[0] if sorted_snapshots else {}
        previous = sorted_snapshots[1] if len(sorted_snapshots) > 1 else {}

        if not latest or not previous:
            return None

        total_assets_before = previous.get("total_assets", 0)
        total_assets_after = latest.get("total_assets", 0)
        change = Decimal(str(total_assets_after)) - Decimal(str(total_assets_before))
        return_rate = (change / Decimal(str(total_assets_before)) * 100) if total_assets_before > 0 else 0

        return {
            "before": previous,
            "after": latest,
            "change": str(change),
            "return_rate": str(return_rate),
        }

    def compare_periods(self, date1: str, date2: str) -> dict[str, Any] | None:
        """对比指定日期"""
        snapshots = [
            s
            for s in self._snapshots
            if s.get("timestamp", "").startswith(date1) or s.get("timestamp", "").startswith(date2)
        ]

        if len(snapshots) < 2:
            return None

        sorted_snapshots = sorted(snapshots, key=lambda x: x.get("timestamp", ""))
        return {
            "period1": sorted_snapshots[0],
            "period2": sorted_snapshots[-1],
        }

    def get_trend_analysis(self, days: int = 30) -> dict[str, Any]:
        """获取趋势分析"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_snapshots = [
            s
            for s in self._snapshots
            if datetime.strptime(s.get("timestamp", "2000-01-01"), "%Y-%m-%d %H:%M:%S") >= cutoff_date
        ]

        if not recent_snapshots:
            return {"trend": "unknown", "days": 0}

        sorted_snapshots = sorted(recent_snapshots, key=lambda x: x.get("timestamp", ""))
        first = sorted_snapshots[0]
        last = sorted_snapshots[-1]

        first_assets = Decimal(str(first.get("total_assets", 0)))
        last_assets = Decimal(str(last.get("total_assets", 0)))
        change = last_assets - first_assets
        trend = "up" if change > 0 else "down" if change < 0 else "stable"

        return {
            "trend": trend,
            "days": len(sorted_snapshots),
            "change": str(change),
            "start_assets": str(first_assets),
            "end_assets": str(last_assets),
        }

    def add_snapshot(self, snapshot: dict[str, Any]) -> None:
        """添加快照"""
        self._snapshots.append(snapshot)


portfolio_comparator = PortfolioComparator()


__all__ = ["PortfolioComparator", "portfolio_comparator"]
