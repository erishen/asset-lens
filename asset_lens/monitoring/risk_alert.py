"""
Risk Alert System for asset-lens.
风险预警系统 - 实时监控、多维度预警、通知推送
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class AlertType(Enum):
    """预警类型"""
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
    """风险预警配置"""
    enabled: bool = True

    max_drawdown_threshold: float = 15.0
    volatility_threshold: float = 25.0
    concentration_threshold: float = 30.0
    position_limit: float = 80.0

    stop_loss_percent: float = -8.0
    take_profit_percent: float = 20.0

    price_change_threshold: float = 5.0
    volume_spike_threshold: float = 3.0

    sector_exposure_limit: float = 40.0

    alert_cooldown_minutes: int = 60

    notification_channels: list[str] = field(default_factory=lambda: ["console"])


@dataclass
class RiskAlertItem:
    """风险预警项"""
    id: str
    level: AlertLevel
    type: AlertType
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


class RiskAlertSystem:
    """风险预警系统"""

    def __init__(self, config: RiskAlertConfig | None = None):
        self.config = config or RiskAlertConfig()
        self._cache_path = Path("cache")
        self._cache_path.mkdir(parents=True, exist_ok=True)

        self._alerts: list[RiskAlertItem] = []
        self._alert_history: list[dict[str, Any]] = []
        self._last_alert_times: dict[str, str] = {}
        self._alert_handlers: list[Callable[[RiskAlertItem], None]] = []

        self._load_history()

    def _load_history(self):
        """加载历史预警"""
        history_file = self._cache_path / "risk_alerts_history.json"
        if history_file.exists():
            try:
                with open(history_file, encoding="utf-8") as f:
                    self._alert_history = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"加载预警历史失败: {e}")
                self._alert_history = []

    def _save_history(self):
        """保存预警历史"""
        history_file = self._cache_path / "risk_alerts_history.json"
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self._alert_history[-1000:], f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"保存预警历史失败: {e}")

    def _generate_alert_id(self, alert_type: AlertType, key: str = "") -> str:
        """生成预警ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{alert_type.value}_{key}_{timestamp}" if key else f"{alert_type.value}_{timestamp}"

    def _should_alert(self, alert_key: str) -> bool:
        """检查是否应该发送预警（冷却时间检查）"""
        if not self.config.alert_cooldown_minutes:
            return True

        last_time = self._last_alert_times.get(alert_key)
        if not last_time:
            return True

        try:
            last_dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            elapsed = (datetime.now() - last_dt).total_seconds() / 60
            return elapsed >= self.config.alert_cooldown_minutes
        except ValueError:
            return True

    def _create_alert(
        self,
        level: AlertLevel,
        alert_type: AlertType,
        title: str,
        message: str,
        value: float,
        threshold: float,
        suggestion: str,
        metadata: dict[str, Any] | None = None,
    ) -> RiskAlertItem:
        """创建预警项"""
        alert = RiskAlertItem(
            id=self._generate_alert_id(alert_type, metadata.get("key", "") if metadata else ""),
            level=level,
            type=alert_type,
            title=title,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            suggestion=suggestion,
            metadata=metadata or {},
        )

        alert_key = f"{alert_type.value}_{metadata.get('key', '')}" if metadata else alert_type.value
        self._last_alert_times[alert_key] = alert.timestamp

        self._alerts.append(alert)
        self._alert_history.append(alert.to_dict())
        self._save_history()

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"预警处理器执行失败: {e}")

        return alert

    def add_alert_handler(self, handler: Callable[[RiskAlertItem], None]):
        """添加预警处理器"""
        self._alert_handlers.append(handler)

    def check_max_drawdown(self, current_drawdown: float, portfolio_name: str = "default") -> RiskAlertItem | None:
        """
        检查最大回撤

        Args:
            current_drawdown: 当前最大回撤百分比
            portfolio_name: 投资组合名称

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"max_drawdown_{portfolio_name}"
        if not self._should_alert(alert_key):
            return None

        if current_drawdown >= self.config.max_drawdown_threshold:
            level = AlertLevel.DANGER if current_drawdown >= self.config.max_drawdown_threshold * 1.5 else AlertLevel.WARNING

            return self._create_alert(
                level=level,
                alert_type=AlertType.MAX_DRAWDOWN,
                title=f"最大回撤预警 - {portfolio_name}",
                message=f"当前最大回撤 {current_drawdown:.2f}% 超过阈值 {self.config.max_drawdown_threshold:.2f}%",
                value=current_drawdown,
                threshold=self.config.max_drawdown_threshold,
                suggestion="建议检查持仓，考虑减仓或止损",
                metadata={"portfolio": portfolio_name, "key": portfolio_name},
            )

        return None

    def check_volatility(self, current_volatility: float, portfolio_name: str = "default") -> RiskAlertItem | None:
        """
        检查波动率

        Args:
            current_volatility: 当前波动率百分比
            portfolio_name: 投资组合名称

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"volatility_{portfolio_name}"
        if not self._should_alert(alert_key):
            return None

        if current_volatility >= self.config.volatility_threshold:
            level = AlertLevel.WARNING if current_volatility < self.config.volatility_threshold * 1.5 else AlertLevel.DANGER

            return self._create_alert(
                level=level,
                alert_type=AlertType.VOLATILITY,
                title=f"波动率预警 - {portfolio_name}",
                message=f"当前波动率 {current_volatility:.2f}% 超过阈值 {self.config.volatility_threshold:.2f}%",
                value=current_volatility,
                threshold=self.config.volatility_threshold,
                suggestion="市场波动较大，建议降低仓位或增加对冲",
                metadata={"portfolio": portfolio_name, "key": portfolio_name},
            )

        return None

    def check_concentration(self, holdings: dict[str, float]) -> RiskAlertItem | None:
        """
        检查持仓集中度

        Args:
            holdings: 持仓字典 {股票代码: 市值}

        Returns:
            预警项或None
        """
        if not self.config.enabled or not holdings:
            return None

        alert_key = "concentration"
        if not self._should_alert(alert_key):
            return None

        total_value = sum(holdings.values())
        if total_value == 0:
            return None

        weights = {code: value / total_value for code, value in holdings.items()}
        max_weight = max(weights.values())
        top_code = max(weights, key=lambda k: weights[k])

        if max_weight * 100 >= self.config.concentration_threshold:
            return self._create_alert(
                level=AlertLevel.WARNING,
                alert_type=AlertType.CONCENTRATION,
                title="持仓集中度预警",
                message=f"单一持仓 {top_code} 占比 {max_weight*100:.2f}% 超过阈值 {self.config.concentration_threshold:.2f}%",
                value=max_weight * 100,
                threshold=self.config.concentration_threshold,
                suggestion="建议分散投资，降低单一资产权重",
                metadata={"top_holding": top_code, "weight": max_weight, "key": "main"},
            )

        return None

    def check_stop_loss(
        self,
        code: str,
        cost_price: float,
        current_price: float,
    ) -> RiskAlertItem | None:
        """
        检查止损

        Args:
            code: 股票代码
            cost_price: 成本价
            current_price: 当前价格

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"stop_loss_{code}"
        if not self._should_alert(alert_key):
            return None

        if cost_price <= 0:
            return None

        change_percent = (current_price - cost_price) / cost_price * 100

        if change_percent <= self.config.stop_loss_percent:
            return self._create_alert(
                level=AlertLevel.DANGER,
                alert_type=AlertType.STOP_LOSS,
                title=f"止损预警 - {code}",
                message=f"{code} 亏损 {abs(change_percent):.2f}% 触及止损线 {self.config.stop_loss_percent}%",
                value=change_percent,
                threshold=self.config.stop_loss_percent,
                suggestion="建议执行止损操作，控制风险",
                metadata={"code": code, "cost_price": cost_price, "current_price": current_price, "key": code},
            )

        return None

    def check_take_profit(
        self,
        code: str,
        cost_price: float,
        current_price: float,
    ) -> RiskAlertItem | None:
        """
        检查止盈

        Args:
            code: 股票代码
            cost_price: 成本价
            current_price: 当前价格

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"take_profit_{code}"
        if not self._should_alert(alert_key):
            return None

        if cost_price <= 0:
            return None

        change_percent = (current_price - cost_price) / cost_price * 100

        if change_percent >= self.config.take_profit_percent:
            return self._create_alert(
                level=AlertLevel.INFO,
                alert_type=AlertType.TAKE_PROFIT,
                title=f"止盈提醒 - {code}",
                message=f"{code} 盈利 {change_percent:.2f}% 达到止盈目标 {self.config.take_profit_percent}%",
                value=change_percent,
                threshold=self.config.take_profit_percent,
                suggestion="建议考虑止盈锁定收益",
                metadata={"code": code, "cost_price": cost_price, "current_price": current_price, "key": code},
            )

        return None

    def check_position_limit(self, current_position: float) -> RiskAlertItem | None:
        """
        检查仓位限制

        Args:
            current_position: 当前仓位百分比

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = "position_limit"
        if not self._should_alert(alert_key):
            return None

        if current_position >= self.config.position_limit:
            level = AlertLevel.WARNING if current_position < 95 else AlertLevel.DANGER

            return self._create_alert(
                level=level,
                alert_type=AlertType.POSITION_LIMIT,
                title="仓位预警",
                message=f"当前仓位 {current_position:.2f}% 超过限制 {self.config.position_limit:.2f}%",
                value=current_position,
                threshold=self.config.position_limit,
                suggestion="建议降低仓位，保留一定现金应对风险",
                metadata={"key": "main"},
            )

        return None

    def check_price_change(
        self,
        code: str,
        change_percent: float,
    ) -> RiskAlertItem | None:
        """
        检查价格变动

        Args:
            code: 股票代码
            change_percent: 涨跌幅百分比

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"price_change_{code}"
        if not self._should_alert(alert_key):
            return None

        abs_change = abs(change_percent)
        if abs_change >= self.config.price_change_threshold:
            direction = "上涨" if change_percent > 0 else "下跌"
            level = AlertLevel.WARNING if abs_change < self.config.price_change_threshold * 2 else AlertLevel.DANGER

            return self._create_alert(
                level=level,
                alert_type=AlertType.PRICE_CHANGE,
                title=f"价格异动 - {code}",
                message=f"{code} {direction} {abs_change:.2f}% 超过阈值 {self.config.price_change_threshold:.2f}%",
                value=change_percent,
                threshold=self.config.price_change_threshold,
                suggestion="关注市场动态，评估是否需要调整持仓",
                metadata={"code": code, "direction": direction, "key": code},
            )

        return None

    def check_market_regime(self, regime: str, description: str = "") -> RiskAlertItem | None:
        """
        检查市场环境变化

        Args:
            regime: 市场环境 (bull/bear/sideways/crisis)
            description: 环境描述

        Returns:
            预警项或None
        """
        if not self.config.enabled:
            return None

        alert_key = f"market_regime_{regime}"
        if not self._should_alert(alert_key):
            return None

        if regime in ["bear", "crisis"]:
            level = AlertLevel.WARNING if regime == "bear" else AlertLevel.DANGER

            suggestions = {
                "bear": "熊市环境，建议降低仓位，控制风险",
                "crisis": "危机环境，建议大幅降低仓位，保持谨慎",
            }

            return self._create_alert(
                level=level,
                alert_type=AlertType.MARKET_REGIME,
                title=f"市场环境预警 - {regime.upper()}",
                message=f"当前市场环境: {description or regime}",
                value=0,
                threshold=0,
                suggestion=suggestions.get(regime, "建议谨慎操作"),
                metadata={"regime": regime, "key": regime},
            )

        return None

    def run_all_checks(
        self,
        portfolio_data: dict[str, Any],
    ) -> list[RiskAlertItem]:
        """
        运行所有风险检查

        Args:
            portfolio_data: 投资组合数据
                {
                    "max_drawdown": float,
                    "volatility": float,
                    "position": float,
                    "holdings": {code: value},
                    "stocks": [{code, cost_price, current_price, change_percent}],
                    "market_regime": str,
                }

        Returns:
            预警列表
        """
        alerts = []

        if "max_drawdown" in portfolio_data:
            alert = self.check_max_drawdown(portfolio_data["max_drawdown"])
            if alert:
                alerts.append(alert)

        if "volatility" in portfolio_data:
            alert = self.check_volatility(portfolio_data["volatility"])
            if alert:
                alerts.append(alert)

        if "position" in portfolio_data:
            alert = self.check_position_limit(portfolio_data["position"])
            if alert:
                alerts.append(alert)

        if "holdings" in portfolio_data:
            alert = self.check_concentration(portfolio_data["holdings"])
            if alert:
                alerts.append(alert)

        if "stocks" in portfolio_data:
            for stock in portfolio_data["stocks"]:
                if "cost_price" in stock and "current_price" in stock:
                    alert = self.check_stop_loss(
                        stock["code"],
                        stock["cost_price"],
                        stock["current_price"],
                    )
                    if alert:
                        alerts.append(alert)

                    alert = self.check_take_profit(
                        stock["code"],
                        stock["cost_price"],
                        stock["current_price"],
                    )
                    if alert:
                        alerts.append(alert)

                if "change_percent" in stock:
                    alert = self.check_price_change(stock["code"], stock["change_percent"])
                    if alert:
                        alerts.append(alert)

        if "market_regime" in portfolio_data:
            alert = self.check_market_regime(
                portfolio_data["market_regime"],
                portfolio_data.get("market_description", ""),
            )
            if alert:
                alerts.append(alert)

        return alerts

    def get_active_alerts(self, hours: int = 24) -> list[RiskAlertItem]:
        """
        获取活跃预警

        Args:
            hours: 最近N小时内的预警

        Returns:
            预警列表
        """
        cutoff = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cutoff_dt = datetime.strptime(cutoff, "%Y-%m-%d %H:%M:%S")

        active_alerts = []
        for alert in self._alerts:
            try:
                alert_dt = datetime.strptime(alert.timestamp, "%Y-%m-%d %H:%M:%S")
                if (cutoff_dt - alert_dt).total_seconds() / 3600 <= hours:
                    active_alerts.append(alert)
            except ValueError:
                pass

        return active_alerts

    def get_alert_summary(self) -> dict[str, Any]:
        """
        获取预警摘要

        Returns:
            预警摘要
        """
        active_alerts = self.get_active_alerts(24)

        by_level: dict[str, int] = {}
        for alert in active_alerts:
            level = alert.level.value
            by_level[level] = by_level.get(level, 0) + 1

        by_type: dict[str, int] = {}
        for alert in active_alerts:
            type_ = alert.type.value
            by_type[type_] = by_type.get(type_, 0) + 1

        return {
            "total_alerts": len(active_alerts),
            "by_level": by_level,
            "by_type": by_type,
            "last_alert": active_alerts[-1].timestamp if active_alerts else None,
            "config": {
                "enabled": self.config.enabled,
                "max_drawdown_threshold": self.config.max_drawdown_threshold,
                "volatility_threshold": self.config.volatility_threshold,
                "concentration_threshold": self.config.concentration_threshold,
                "stop_loss_percent": self.config.stop_loss_percent,
                "take_profit_percent": self.config.take_profit_percent,
            },
        }

    def clear_alerts(self):
        """清除所有预警"""
        self._alerts.clear()

    def generate_alert_report(self) -> str:
        """
        生成预警报告

        Returns:
            报告文本
        """
        summary = self.get_alert_summary()
        active_alerts = self.get_active_alerts(24)

        lines = []
        lines.append("=" * 60)
        lines.append("🚨 风险预警报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        lines.append("📊 预警统计:")
        lines.append(f"  • 24小时内预警总数: {summary['total_alerts']}")

        if summary["by_level"]:
            lines.append("  • 按级别分布:")
            for level, count in summary["by_level"].items():
                level_emoji = {"critical": "🔴", "danger": "🟠", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
                lines.append(f"    - {level_emoji} {level}: {count}")

        lines.append("")

        if summary["by_type"]:
            lines.append("  • 按类型分布:")
            for type_, count in summary["by_type"].items():
                lines.append(f"    - {type_}: {count}")

        lines.append("")

        if active_alerts:
            lines.append("🚨 最近预警详情:")
            for alert in active_alerts[-10:]:
                level_emoji = {
                    "critical": "🔴",
                    "danger": "🟠",
                    "warning": "🟡",
                    "info": "🔵",
                }.get(alert.level.value, "⚪")
                lines.append(f"  {level_emoji} [{alert.timestamp}] {alert.title}")
                lines.append(f"     {alert.message}")
                lines.append(f"     建议: {alert.suggestion}")
                lines.append("")
        else:
            lines.append("✅ 暂无活跃预警")
            lines.append("")

        lines.append("⚙️ 预警配置:")
        config = summary["config"]
        lines.append(f"  • 最大回撤阈值: {config['max_drawdown_threshold']}%")
        lines.append(f"  • 波动率阈值: {config['volatility_threshold']}%")
        lines.append(f"  • 集中度阈值: {config['concentration_threshold']}%")
        lines.append(f"  • 止损线: {config['stop_loss_percent']}%")
        lines.append(f"  • 止盈线: {config['take_profit_percent']}%")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


risk_alert_system = RiskAlertSystem()
