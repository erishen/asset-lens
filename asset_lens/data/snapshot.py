"""
Portfolio Snapshot - 投资组合快照
用于存储历史数据，支持差异对比
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .providers.cache import UnifiedCache


@dataclass
class PortfolioSnapshot:
    """投资组合快照"""

    snapshot_id: str
    timestamp: str
    total_assets: float
    total_profit: float
    return_rate: float
    position_count: int
    positions: list[dict[str, Any]] = field(default_factory=list)
    risk_metrics: dict[str, float] = field(default_factory=dict)
    market_regime: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class SnapshotManager:

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path.home() / ".asset_lens" / "snapshots"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache = UnifiedCache(cache_dir=self.storage_path)

    def _get_snapshot_filename(self, date_str: str) -> str:
        return f"snapshot_{date_str}.json"

    def create_snapshot(
        self,
        total_assets: float,
        total_profit: float,
        return_rate: float,
        position_count: int,
        positions: list[dict[str, Any]] | None = None,
        risk_metrics: dict[str, float] | None = None,
        market_regime: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> PortfolioSnapshot:
        """
        创建快照

        Args:
            total_assets: 总资产
            total_profit: 总收益
            return_rate: 收益率
            position_count: 持仓数量
            positions: 持仓列表
            risk_metrics: 风险指标
            market_regime: 市场环境
            metadata: 元数据

        Returns:
            快照对象
        """
        now = datetime.now()
        snapshot_id = now.strftime("%Y%m%d_%H%M%S")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        snapshot = PortfolioSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            total_assets=total_assets,
            total_profit=total_profit,
            return_rate=return_rate,
            position_count=position_count,
            positions=positions or [],
            risk_metrics=risk_metrics or {},
            market_regime=market_regime,
            metadata=metadata or {},
        )

        self._save_snapshot(snapshot)
        return snapshot

    def _save_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        date_str = snapshot.timestamp[:10]
        filename = self._get_snapshot_filename(date_str)

        existing = self._cache.load_file(filename)
        snapshots = existing.get("items", []) if existing else []

        snapshots.append(snapshot.to_dict())

        self._cache.save_file(filename, {"items": snapshots}, ttl=0)

    def get_snapshot(self, date_str: str) -> PortfolioSnapshot | None:
        filename = self._get_snapshot_filename(date_str)

        data = self._cache.load_file(filename)
        if data is None:
            return None

        try:
            snapshots = data.get("items", [])
            if not snapshots:
                return None

            latest = snapshots[-1]
            return PortfolioSnapshot(**latest)
        except (ValueError, KeyError, TypeError):
            return None

    def get_snapshots_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[PortfolioSnapshot]:
        """
        获取日期范围内的快照

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            快照列表
        """
        snapshots: list[PortfolioSnapshot] = []

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return snapshots

        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            snapshot = self.get_snapshot(date_str)
            if snapshot:
                snapshots.append(snapshot)
            current += timedelta(days=1)

        return snapshots

    def get_latest_snapshots(self, count: int = 7) -> list[PortfolioSnapshot]:
        """
        获取最近的快照

        Args:
            count: 数量

        Returns:
            快照列表
        """
        snapshots: list[PortfolioSnapshot] = []
        today = datetime.now()

        for i in range(count * 2):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            snapshot = self.get_snapshot(date_str)
            if snapshot:
                snapshots.append(snapshot)
                if len(snapshots) >= count:
                    break

        return snapshots


snapshot_manager = SnapshotManager()


__all__ = [
    "PortfolioSnapshot",
    "SnapshotManager",
    "snapshot_manager",
]
