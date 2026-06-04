"""
Stock Alert Monitor Module.
异动提醒模块 - 实时监控股票异动

功能:
1. 涨跌幅异动监控 (超过阈值提醒)
2. 成交量异动监控 (放量/缩量)
3. 关键价位提醒 (支撑/阻力位)
4. 大单监控 (主力资金动向)
5. 涨跌停监控
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache, write_json_cache
from .signal_pusher import Priority, Signal, SignalPusher, SignalType


class MarketAlertType(Enum):
    """异动类型"""

    PRICE_UP = "price_up"  # 涨幅异动
    PRICE_DOWN = "price_down"  # 跌幅异动
    VOLUME_SURGE = "volume_surge"  # 放量
    VOLUME_SHRINK = "volume_shrink"  # 缩量
    LIMIT_UP = "limit_up"  # 涨停
    LIMIT_DOWN = "limit_down"  # 跌停
    BIG_BUY = "big_buy"  # 大单买入
    BIG_SELL = "big_sell"  # 大单卖出
    SUPPORT_BREAK = "support_break"  # 跌破支撑
    RESISTANCE_BREAK = "resistance_break"  # 突破阻力


@dataclass
class AlertThreshold:
    """异动阈值配置"""

    price_up_percent: float = 5.0  # 涨幅阈值
    price_down_percent: float = -5.0  # 跌幅阈值
    volume_surge_ratio: float = 2.0  # 放量倍数
    volume_shrink_ratio: float = 0.5  # 缩量比例
    big_order_amount: float = 1000000  # 大单金额 (元)


@dataclass
class StockSnapshot:
    """股票快照"""

    code: str
    name: str
    price: float
    change_percent: float
    volume: float
    turnover: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def is_limit_up(self) -> bool:
        """是否涨停"""
        return self.change_percent >= 9.9

    @property
    def is_limit_down(self) -> bool:
        """是否跌停"""
        return self.change_percent <= -9.9

    @property
    def amplitude(self) -> float:
        """振幅"""
        if self.prev_close > 0:
            return (self.high - self.low) / self.prev_close * 100
        return 0.0


@dataclass
class MarketStockAlert:
    """股票异动"""

    code: str
    name: str
    alert_type: MarketAlertType
    current_price: float
    change_percent: float
    description: str
    severity: Priority
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class AlertMonitor:
    """异动监控器"""

    def __init__(
        self,
        threshold: AlertThreshold | None = None,
        pusher: SignalPusher | None = None,
        cache_path: Path | None = None,
    ):
        self.threshold = threshold or AlertThreshold()
        self.pusher = pusher or SignalPusher()
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.alert_history_file = self.cache_path / "alert_history.json"

        self._prev_snapshots: dict[str, StockSnapshot] = {}
        self._avg_volumes: dict[str, float] = {}

    def check_price_alert(self, snapshot: StockSnapshot) -> MarketStockAlert | None:
        """检查价格异动"""
        if snapshot.change_percent >= self.threshold.price_up_percent:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.PRICE_UP,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description=f"涨幅 {snapshot.change_percent:.2f}% 超过阈值 {self.threshold.price_up_percent}%",
                severity=Priority.HIGH if snapshot.change_percent >= 7 else Priority.MEDIUM,
                details={"threshold": self.threshold.price_up_percent},
            )

        if snapshot.change_percent <= self.threshold.price_down_percent:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.PRICE_DOWN,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description=f"跌幅 {abs(snapshot.change_percent):.2f}% 超过阈值 {abs(self.threshold.price_down_percent)}%",
                severity=Priority.HIGH if snapshot.change_percent <= -7 else Priority.MEDIUM,
                details={"threshold": self.threshold.price_down_percent},
            )

        return None

    def check_volume_alert(self, snapshot: StockSnapshot, avg_volume: float | None = None) -> MarketStockAlert | None:
        """检查成交量异动"""
        if avg_volume is None:
            avg_volume = self._avg_volumes.get(snapshot.code, snapshot.volume)

        if avg_volume > 0:
            volume_ratio = snapshot.volume / avg_volume

            if volume_ratio >= self.threshold.volume_surge_ratio:
                return MarketStockAlert(
                    code=snapshot.code,
                    name=snapshot.name,
                    alert_type=MarketAlertType.VOLUME_SURGE,
                    current_price=snapshot.price,
                    change_percent=snapshot.change_percent,
                    description=f"成交量放大 {volume_ratio:.1f} 倍",
                    severity=Priority.MEDIUM,
                    details={"volume_ratio": volume_ratio, "avg_volume": avg_volume},
                )

            if volume_ratio <= self.threshold.volume_shrink_ratio:
                return MarketStockAlert(
                    code=snapshot.code,
                    name=snapshot.name,
                    alert_type=MarketAlertType.VOLUME_SHRINK,
                    current_price=snapshot.price,
                    change_percent=snapshot.change_percent,
                    description=f"成交量萎缩至 {volume_ratio:.1%}",
                    severity=Priority.LOW,
                    details={"volume_ratio": volume_ratio, "avg_volume": avg_volume},
                )

        return None

    def check_limit_alert(self, snapshot: StockSnapshot) -> MarketStockAlert | None:
        """检查涨跌停"""
        if snapshot.is_limit_up:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.LIMIT_UP,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description="涨停",
                severity=Priority.HIGH,
                details={"amplitude": snapshot.amplitude},
            )

        if snapshot.is_limit_down:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.LIMIT_DOWN,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description="跌停",
                severity=Priority.HIGH,
                details={"amplitude": snapshot.amplitude},
            )

        return None

    def check_price_level_alert(
        self,
        snapshot: StockSnapshot,
        support_level: float | None = None,
        resistance_level: float | None = None,
    ) -> MarketStockAlert | None:
        """检查关键价位"""
        if support_level and snapshot.price < support_level:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.SUPPORT_BREAK,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description=f"跌破支撑位 {support_level:.2f}",
                severity=Priority.HIGH,
                details={"support_level": support_level},
            )

        if resistance_level and snapshot.price > resistance_level:
            return MarketStockAlert(
                code=snapshot.code,
                name=snapshot.name,
                alert_type=MarketAlertType.RESISTANCE_BREAK,
                current_price=snapshot.price,
                change_percent=snapshot.change_percent,
                description=f"突破阻力位 {resistance_level:.2f}",
                severity=Priority.HIGH,
                details={"resistance_level": resistance_level},
            )

        return None

    def monitor(self, snapshot: StockSnapshot, **kwargs) -> list[MarketStockAlert]:
        """监控股票异动"""
        alerts = []

        price_alert = self.check_price_alert(snapshot)
        if price_alert:
            alerts.append(price_alert)

        volume_alert = self.check_volume_alert(
            snapshot,
            avg_volume=kwargs.get("avg_volume"),
        )
        if volume_alert:
            alerts.append(volume_alert)

        limit_alert = self.check_limit_alert(snapshot)
        if limit_alert:
            alerts.append(limit_alert)

        level_alert = self.check_price_level_alert(
            snapshot,
            support_level=kwargs.get("support_level"),
            resistance_level=kwargs.get("resistance_level"),
        )
        if level_alert:
            alerts.append(level_alert)

        self._prev_snapshots[snapshot.code] = snapshot

        for alert in alerts:
            self._save_alert(alert)
            self._push_alert(alert)

        return alerts

    def monitor_batch(
        self,
        snapshots: list[StockSnapshot],
        price_levels: dict[str, dict[str, float]] | None = None,
        avg_volumes: dict[str, float] | None = None,
    ) -> list[MarketStockAlert]:
        """批量监控"""
        all_alerts = []

        for snapshot in snapshots:
            kwargs = {}

            if price_levels and snapshot.code in price_levels:
                kwargs.update(price_levels[snapshot.code])

            if avg_volumes and snapshot.code in avg_volumes:
                kwargs["avg_volume"] = avg_volumes[snapshot.code]

            alerts = self.monitor(snapshot, **kwargs)
            all_alerts.extend(alerts)

        return all_alerts

    def _push_alert(self, alert: MarketStockAlert) -> None:
        """推送异动"""
        signal = Signal(
            code=alert.code,
            name=alert.name,
            signal_type=self._alert_to_signal_type(alert.alert_type),
            price=alert.current_price,
            change_percent=alert.change_percent,
            confidence=1.0,
            reason=alert.description,
            suggestion=self._get_suggestion(alert.alert_type),
            priority=alert.severity,
        )

        self.pusher.push(signal)

    def _alert_to_signal_type(self, alert_type: MarketAlertType) -> SignalType:
        """转换异动类型到信号类型"""
        mapping = {
            MarketAlertType.PRICE_UP: SignalType.PRICE_ALERT,
            MarketAlertType.PRICE_DOWN: SignalType.PRICE_ALERT,
            MarketAlertType.VOLUME_SURGE: SignalType.VOLUME_ALERT,
            MarketAlertType.VOLUME_SHRINK: SignalType.VOLUME_ALERT,
            MarketAlertType.LIMIT_UP: SignalType.PRICE_ALERT,
            MarketAlertType.LIMIT_DOWN: SignalType.PRICE_ALERT,
            MarketAlertType.BIG_BUY: SignalType.PRICE_ALERT,
            MarketAlertType.BIG_SELL: SignalType.PRICE_ALERT,
            MarketAlertType.SUPPORT_BREAK: SignalType.PRICE_ALERT,
            MarketAlertType.RESISTANCE_BREAK: SignalType.PRICE_ALERT,
        }
        return mapping.get(alert_type, SignalType.PRICE_ALERT)

    def _get_suggestion(self, alert_type: MarketAlertType) -> str:
        """获取建议"""
        suggestions = {
            MarketAlertType.PRICE_UP: "关注是否需要止盈",
            MarketAlertType.PRICE_DOWN: "关注是否需要止损",
            MarketAlertType.VOLUME_SURGE: "关注资金动向，可能有大动作",
            MarketAlertType.VOLUME_SHRINK: "成交量萎缩，观望为主",
            MarketAlertType.LIMIT_UP: "涨停，关注封单情况",
            MarketAlertType.LIMIT_DOWN: "跌停，注意风险",
            MarketAlertType.BIG_BUY: "大单买入，关注后续走势",
            MarketAlertType.BIG_SELL: "大单卖出，注意风险",
            MarketAlertType.SUPPORT_BREAK: "跌破支撑，考虑止损",
            MarketAlertType.RESISTANCE_BREAK: "突破阻力，关注确认情况",
        }
        return suggestions.get(alert_type, "关注后续走势")

    def _save_alert(self, alert: MarketStockAlert) -> None:
        """保存异动历史"""
        history = read_json_cache(self.alert_history_file) or []

        history.append(
            {
                "code": alert.code,
                "name": alert.name,
                "type": alert.alert_type.value,
                "price": alert.current_price,
                "change": alert.change_percent,
                "description": alert.description,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp,
            }
        )

        if len(history) > 1000:
            history = history[-1000:]

        write_json_cache(self.alert_history_file, history)

    def get_recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近异动"""
        history = read_json_cache(self.alert_history_file)
        if history:
            return history[-limit:]
        return []


alert_monitor = AlertMonitor()
