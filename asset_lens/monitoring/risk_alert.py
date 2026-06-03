import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..utils.json_cache import read_json_cache, write_json_cache
from .risk_alert_checks import AlertLevel, RiskAlertChecksMixin

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class RiskAlertType(Enum):
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    CONCENTRATION = "concentration"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    POSITION_LIMIT = "position_limit"
    MARKET_REGIME = "market_regime"
    PRICE_CHANGE = "price_change"
    VOLUME_SPIKE = "volume_spike"
    SECTOR_EXPOSURE = "sector_exposure"


@dataclass
class RiskAlertConfig:
    enabled: bool = True
    max_drawdown_threshold: float = 15.0
    volatility_threshold: float = 25.0
    concentration_threshold: float = 30.0
    position_limit: float = 80.0
    stop_loss_percent: float = -8.0
    take_profit_percent: float = 20.0
    price_change_threshold: float = 10.0
    volume_spike_threshold: float = 3.0
    sector_exposure_limit: float = 40.0
    alert_cooldown_minutes: int = 60
    notification_channels: list[str] = field(default_factory=lambda: ["console"])
    stop_loss_threshold: float = -0.08
    take_profit_threshold: float = 0.20


@dataclass
class RiskAlertItem:
    id: str
    level: AlertLevel
    type: RiskAlertType
    title: str
    message: str
    value: float
    threshold: float
    timestamp: str
    suggestion: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level.value,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }


class RiskAlertSystem(RiskAlertChecksMixin):
    def __init__(self, config: RiskAlertConfig | None = None):
        self.config = config or RiskAlertConfig()
        self._alerts: list[RiskAlertItem] = []
        self._handlers: list[Callable[[RiskAlertItem], None]] = []
        self._history_file = Path("cache/risk_alerts_history.json")
        self._alert_history: dict[str, datetime] = {}
        self._load_history()

    def _load_history(self):
        data = read_json_cache(self._history_file)
        if data:
            for key, ts in data.items():
                self._alert_history[key] = datetime.fromisoformat(ts)

    def _save_history(self):
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        data = {key: ts.isoformat() for key, ts in self._alert_history.items()}
        write_json_cache(self._history_file, data)

    def _generate_alert_id(self, alert_type: RiskAlertType, key: str = "") -> str:
        return f"{alert_type.value}_{key}_{datetime.now().strftime('%Y%m%d')}"

    def _should_alert(self, alert_key: str) -> bool:
        if alert_key not in self._alert_history:
            return True

        last_alert = self._alert_history[alert_key]
        cooldown = datetime.now().timestamp() - last_alert.timestamp()
        return cooldown >= self.config.alert_cooldown_minutes * 60

    def _create_alert(
        self,
        alert_type: RiskAlertType,
        level: AlertLevel,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> RiskAlertItem:
        alert_key = f"{alert_type.value}_{data.get('stock_code', '') if data else ''}"
        alert_id = self._generate_alert_id(alert_type, data.get("stock_code", "") if data else "")

        value = 0.0
        threshold = 0.0
        if data:
            value = float(data.get("drawdown", data.get("volatility", data.get("loss_pct", data.get("profit_pct", data.get("change_percent", 0))))))
            threshold = float(data.get("threshold", self.config.max_drawdown_threshold))

        suggestions = {
            RiskAlertType.MAX_DRAWDOWN: "建议降低仓位，检查止损设置",
            RiskAlertType.HIGH_VOLATILITY: "建议减少高风险资产配置",
            RiskAlertType.CONCENTRATION: "建议分散投资，降低单一持仓比例",
            RiskAlertType.STOP_LOSS: "建议立即止损或设置自动止损",
            RiskAlertType.TAKE_PROFIT: "建议考虑部分止盈",
            RiskAlertType.POSITION_LIMIT: "建议降低整体仓位",
            RiskAlertType.MARKET_REGIME: "建议谨慎操作，关注市场动态",
            RiskAlertType.PRICE_CHANGE: "建议关注相关新闻和公告",
        }

        alert = RiskAlertItem(
            id=alert_id,
            level=level,
            type=alert_type,
            title=title,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now().isoformat(),
            suggestion=suggestions.get(alert_type, ""),
            metadata=data or {},
        )

        if self._should_alert(alert_key):
            self._alerts.append(alert)
            self._alert_history[alert_key] = datetime.now()
            self._save_history()

            for handler in self._handlers:
                try:
                    handler(alert)
                except (ValueError, KeyError, TypeError, RuntimeError) as e:
                    logger.error(f"预警处理器执行失败: {e}")

        return alert

    def add_alert_handler(self, handler: Callable[[RiskAlertItem], None]):
        self._handlers.append(handler)

    def get_active_alerts(self, hours: int = 24) -> list[RiskAlertItem]:
        cutoff = datetime.now().timestamp() - hours * 3600
        active = []
        for alert in self._alerts:
            try:
                alert_time = datetime.fromisoformat(alert.timestamp).timestamp()
                if alert_time >= cutoff:
                    active.append(alert)
            except (ValueError, TypeError):
                active.append(alert)
        return active

    def get_alert_summary(self) -> dict[str, Any]:
        active = self.get_active_alerts()
        by_level = {}
        for alert in active:
            level = alert.level.value
            by_level[level] = by_level.get(level, 0) + 1

        return {
            "total_alerts": len(active),
            "by_level": by_level,
            "by_type": {t.value: sum(1 for a in active if a.type == t) for t in RiskAlertType if any(a.type == t for a in active)},
            "last_updated": datetime.now().isoformat(),
        }

    def clear_alerts(self):
        self._alerts.clear()

    def generate_alert_report(self) -> str:
        active = self.get_active_alerts()
        if not active:
            return "✅ 当前没有活跃的风险预警"

        lines = ["⚠️ 风险预警报告", "=" * 40]

        for alert in active:
            level_icon = {"info": "ℹ️", "warning": "⚠️", "danger": "🔴", "critical": "🚨"}.get(alert.level.value, "⚠️")
            lines.append(f"\n{level_icon} [{alert.level.value.upper()}] {alert.title}")
            lines.append(f"   {alert.message}")
            if alert.suggestion:
                lines.append(f"   💡 {alert.suggestion}")

        return "\n".join(lines)


risk_alert_system = RiskAlertSystem()
