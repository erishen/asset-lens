"""
Portfolio Comparison - 投资组合对比模块
支持周度对比、策略表现对比等
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .snapshot import PortfolioSnapshot, SnapshotManager


@dataclass
class ComparisonResult:
    """对比结果"""
    period1: str
    period2: str
    total_assets_change: float
    total_assets_change_percent: float
    total_profit_change: float
    return_rate_change: float
    position_count_change: int
    position_changes: List[Dict[str, Any]]
    risk_metrics_change: Dict[str, float]
    market_regime_change: Optional[str]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "period1": self.period1,
            "period2": self.period2,
            "total_assets_change": self.total_assets_change,
            "total_assets_change_percent": self.total_assets_change_percent,
            "total_profit_change": self.total_profit_change,
            "return_rate_change": self.return_rate_change,
            "position_count_change": self.position_count_change,
            "position_changes": self.position_changes,
            "risk_metrics_change": self.risk_metrics_change,
            "market_regime_change": self.market_regime_change,
            "summary": self.summary,
        }


class PortfolioComparator:
    """投资组合对比器"""
    
    def __init__(self, snapshot_manager: Optional[SnapshotManager] = None):
        self.snapshot_manager = snapshot_manager or SnapshotManager()
    
    def compare_snapshots(
        self,
        snapshot1: PortfolioSnapshot,
        snapshot2: PortfolioSnapshot,
    ) -> ComparisonResult:
        """
        对比两个快照
        
        Args:
            snapshot1: 较早的快照
            snapshot2: 较新的快照
            
        Returns:
            对比结果
        """
        total_assets_change = snapshot2.total_assets - snapshot1.total_assets
        total_assets_change_percent = (
            (total_assets_change / snapshot1.total_assets * 100)
            if snapshot1.total_assets > 0
            else 0
        )
        
        total_profit_change = snapshot2.total_profit - snapshot1.total_profit
        return_rate_change = snapshot2.return_rate - snapshot1.return_rate
        position_count_change = snapshot2.position_count - snapshot1.position_count
        
        position_changes = self._compare_positions(
            snapshot1.positions,
            snapshot2.positions,
        )
        
        risk_metrics_change = {}
        for key in set(snapshot1.risk_metrics.keys()) | set(snapshot2.risk_metrics.keys()):
            val1 = snapshot1.risk_metrics.get(key, 0)
            val2 = snapshot2.risk_metrics.get(key, 0)
            risk_metrics_change[key] = val2 - val1
        
        market_regime_change = None
        if snapshot1.market_regime != snapshot2.market_regime:
            market_regime_change = f"{snapshot1.market_regime} → {snapshot2.market_regime}"
        
        summary = self._generate_summary(
            total_assets_change_percent,
            return_rate_change,
            position_count_change,
            market_regime_change,
        )
        
        return ComparisonResult(
            period1=snapshot1.timestamp,
            period2=snapshot2.timestamp,
            total_assets_change=total_assets_change,
            total_assets_change_percent=total_assets_change_percent,
            total_profit_change=total_profit_change,
            return_rate_change=return_rate_change,
            position_count_change=position_count_change,
            position_changes=position_changes,
            risk_metrics_change=risk_metrics_change,
            market_regime_change=market_regime_change,
            summary=summary,
        )
    
    def _compare_positions(
        self,
        positions1: List[Dict[str, Any]],
        positions2: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """对比持仓变化"""
        changes: List[Dict[str, Any]] = []
        
        pos1_map = {p.get("code", ""): p for p in positions1}
        pos2_map = {p.get("code", ""): p for p in positions2}
        
        all_codes = set(pos1_map.keys()) | set(pos2_map.keys())
        
        for code in all_codes:
            p1 = pos1_map.get(code)
            p2 = pos2_map.get(code)
            
            if p1 is None and p2 is not None:
                changes.append({
                    "code": code,
                    "name": p2.get("name", ""),
                    "change_type": "new",
                    "message": f"新增持仓: {p2.get('name', '')}",
                })
            elif p1 is not None and p2 is None:
                changes.append({
                    "code": code,
                    "name": p1.get("name", ""),
                    "change_type": "removed",
                    "message": f"移除持仓: {p1.get('name', '')}",
                })
            elif p1 is not None and p2 is not None:
                amount1 = p1.get("amount", 0)
                amount2 = p2.get("amount", 0)
                if abs(amount2 - amount1) > 0.01:
                    change_percent = (
                        ((amount2 - amount1) / amount1 * 100)
                        if amount1 > 0
                        else 0
                    )
                    changes.append({
                        "code": code,
                        "name": p1.get("name", ""),
                        "change_type": "modified",
                        "amount_change": amount2 - amount1,
                        "change_percent": change_percent,
                        "message": f"{p1.get('name', '')} 仓位变化: {change_percent:.1f}%",
                    })
        
        return changes
    
    def _generate_summary(
        self,
        assets_change_percent: float,
        return_change: float,
        position_change: int,
        regime_change: Optional[str],
    ) -> str:
        """生成对比摘要"""
        parts: List[str] = []
        
        if assets_change_percent > 0:
            parts.append(f"资产增长 {assets_change_percent:.2f}%")
        elif assets_change_percent < 0:
            parts.append(f"资产减少 {abs(assets_change_percent):.2f}%")
        else:
            parts.append("资产持平")
        
        if return_change > 0.01:
            parts.append(f"收益率提升 {return_change:.2f}%")
        elif return_change < -0.01:
            parts.append(f"收益率下降 {abs(return_change):.2f}%")
        
        if position_change > 0:
            parts.append(f"新增 {position_change} 只持仓")
        elif position_change < 0:
            parts.append(f"减少 {abs(position_change)} 只持仓")
        
        if regime_change:
            parts.append(f"市场环境变化: {regime_change}")
        
        return "，".join(parts)
    
    def compare_weekly(self) -> Optional[ComparisonResult]:
        """
        周度对比
        
        Returns:
            对比结果
        """
        today = datetime.now()
        
        this_week_start = today - timedelta(days=today.weekday())
        this_week_str = this_week_start.strftime("%Y-%m-%d")
        
        last_week_start = this_week_start - timedelta(days=7)
        last_week_str = last_week_start.strftime("%Y-%m-%d")
        
        snapshot1 = self.snapshot_manager.get_snapshot(last_week_str)
        snapshot2 = self.snapshot_manager.get_snapshot(this_week_str)
        
        if snapshot1 is None or snapshot2 is None:
            return None
        
        return self.compare_snapshots(snapshot1, snapshot2)
    
    def compare_periods(
        self,
        date1: str,
        date2: str,
    ) -> Optional[ComparisonResult]:
        """
        对比指定日期
        
        Args:
            date1: 日期1 (较早)
            date2: 日期2 (较晚)
            
        Returns:
            对比结果
        """
        snapshot1 = self.snapshot_manager.get_snapshot(date1)
        snapshot2 = self.snapshot_manager.get_snapshot(date2)
        
        if snapshot1 is None or snapshot2 is None:
            return None
        
        return self.compare_snapshots(snapshot1, snapshot2)
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        获取趋势分析
        
        Args:
            days: 分析天数
            
        Returns:
            趋势分析结果
        """
        snapshots = self.snapshot_manager.get_latest_snapshots(days)
        
        if len(snapshots) < 2:
            return {
                "trend": "insufficient_data",
                "message": "数据不足，无法分析趋势",
            }
        
        snapshots.sort(key=lambda x: x.timestamp)
        
        assets_values = [s.total_assets for s in snapshots]
        return_values = [s.return_rate for s in snapshots]
        
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        
        total_change = last_snapshot.total_assets - first_snapshot.total_assets
        total_change_percent = (
            (total_change / first_snapshot.total_assets * 100)
            if first_snapshot.total_assets > 0
            else 0
        )
        
        if total_change_percent > 5:
            trend = "upward"
            trend_message = "上升趋势"
        elif total_change_percent < -5:
            trend = "downward"
            trend_message = "下降趋势"
        else:
            trend = "stable"
            trend_message = "横盘整理"
        
        max_assets = max(assets_values)
        min_assets = min(assets_values)
        avg_assets = sum(assets_values) / len(assets_values)
        
        return {
            "trend": trend,
            "trend_message": trend_message,
            "total_change_percent": round(total_change_percent, 2),
            "max_assets": max_assets,
            "min_assets": min_assets,
            "avg_assets": avg_assets,
            "data_points": len(snapshots),
            "start_date": first_snapshot.timestamp,
            "end_date": last_snapshot.timestamp,
        }


portfolio_comparator = PortfolioComparator()


__all__ = [
    "ComparisonResult",
    "PortfolioComparator",
    "portfolio_comparator",
]
