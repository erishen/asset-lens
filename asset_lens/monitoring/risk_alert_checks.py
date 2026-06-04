import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RiskAlertChecksMixin:
    def check_max_drawdown(self, current_drawdown: float, portfolio_name: str = "default") -> Any | None:
        from .risk_alert import RiskAlertType

        if abs(current_drawdown) >= self.config.max_drawdown_threshold:  # type: ignore[attr-defined]
            level = AlertLevel.CRITICAL if abs(current_drawdown) >= self.config.max_drawdown_threshold * 1.5 else AlertLevel.WARNING  # type: ignore[attr-defined]

            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.MAX_DRAWDOWN,
                level=level,
                title=f"最大回撤预警: {abs(current_drawdown):.1%}",
                message=f"组合 {portfolio_name} 当前回撤 {abs(current_drawdown):.1%}，超过阈值 {self.config.max_drawdown_threshold:.1%}",  # type: ignore[attr-defined]
                data={"drawdown": current_drawdown, "threshold": self.config.max_drawdown_threshold, "portfolio": portfolio_name},  # type: ignore[attr-defined]
            )
        return None

    def check_volatility(self, current_volatility: float, portfolio_name: str = "default") -> Any | None:
        from .risk_alert import RiskAlertType

        if current_volatility >= self.config.volatility_threshold:  # type: ignore[attr-defined]
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.VOLATILITY,
                level=AlertLevel.WARNING,
                title=f"高波动率预警: {current_volatility:.1%}",
                message=f"组合 {portfolio_name} 当前波动率 {current_volatility:.1%}，超过阈值 {self.config.volatility_threshold:.1%}",  # type: ignore[attr-defined]
                data={"volatility": current_volatility, "threshold": self.config.volatility_threshold, "portfolio": portfolio_name},  # type: ignore[attr-defined]
            )
        return None

    def check_concentration(self, holdings: dict[str, float]) -> Any | None:
        from .risk_alert import RiskAlertType

        if not holdings:
            return None

        total = sum(holdings.values())
        if total <= 0:
            return None

        max_holding = max(holdings.values())
        max_ratio = max_holding / total

        if max_ratio >= self.config.concentration_threshold:  # type: ignore[attr-defined]
            max_name = max(holdings, key=holdings.get)  # type: ignore[arg-type]
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.CONCENTRATION,
                level=AlertLevel.WARNING,
                title=f"持仓集中度预警: {max_name}",
                message=f"单一持仓 {max_name} 占比 {max_ratio:.1%}，超过阈值 {self.config.concentration_threshold:.1%}",  # type: ignore[attr-defined]
                data={"max_holding": max_name, "max_ratio": max_ratio, "threshold": self.config.concentration_threshold},  # type: ignore[attr-defined]
            )
        return None

    def check_stop_loss(
        self,
        current_price: float,
        cost_price: float,
        stock_name: str = "",
        stock_code: str = "",
    ) -> Any | None:
        from .risk_alert import RiskAlertType

        if cost_price <= 0:
            return None

        loss_pct = (current_price - cost_price) / cost_price

        if loss_pct <= self.config.stop_loss_threshold:  # type: ignore[attr-defined]
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.STOP_LOSS,
                level=AlertLevel.CRITICAL,
                title=f"止损预警: {stock_name or stock_code}",
                message=f"{stock_name or stock_code} 当前亏损 {abs(loss_pct):.1%}，触发止损线 {abs(self.config.stop_loss_threshold):.1%}",  # type: ignore[attr-defined]
                data={"stock_code": stock_code, "stock_name": stock_name, "loss_pct": loss_pct, "current_price": current_price, "cost_price": cost_price},
            )
        return None

    def check_take_profit(
        self,
        current_price: float,
        cost_price: float,
        stock_name: str = "",
        stock_code: str = "",
    ) -> Any | None:
        from .risk_alert import RiskAlertType

        if cost_price <= 0:
            return None

        profit_pct = (current_price - cost_price) / cost_price

        if profit_pct >= self.config.take_profit_threshold:  # type: ignore[attr-defined]
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.TAKE_PROFIT,
                level=AlertLevel.INFO,
                title=f"止盈提醒: {stock_name or stock_code}",
                message=f"{stock_name or stock_code} 当前盈利 {profit_pct:.1%}，达到止盈线 {self.config.take_profit_threshold:.1%}",  # type: ignore[attr-defined]
                data={"stock_code": stock_code, "stock_name": stock_name, "profit_pct": profit_pct, "current_price": current_price, "cost_price": cost_price},
            )
        return None

    def check_position_limit(self, current_position: float) -> Any | None:
        from .risk_alert import RiskAlertType

        if current_position >= self.config.position_limit:  # type: ignore[attr-defined]
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.POSITION_LIMIT,
                level=AlertLevel.WARNING,
                title=f"仓位上限预警: {current_position:.1%}",
                message=f"当前仓位 {current_position:.1%}，超过上限 {self.config.position_limit:.1%}",  # type: ignore[attr-defined]
                data={"current_position": current_position, "limit": self.config.position_limit},  # type: ignore[attr-defined]
            )
        return None

    def check_price_change(
        self,
        stock_name: str,
        stock_code: str,
        change_percent: float,
    ) -> Any | None:
        from .risk_alert import RiskAlertType

        if abs(change_percent) >= self.config.price_change_threshold:  # type: ignore[attr-defined]
            direction = "上涨" if change_percent > 0 else "下跌"
            level = AlertLevel.CRITICAL if abs(change_percent) >= self.config.price_change_threshold * 2 else AlertLevel.WARNING  # type: ignore[attr-defined]

            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.PRICE_CHANGE,
                level=level,
                title=f"价格剧烈波动: {stock_name}",
                message=f"{stock_name}({stock_code}) {direction} {abs(change_percent):.1%}",
                data={"stock_code": stock_code, "stock_name": stock_name, "change_percent": change_percent},
            )
        return None

    def check_market_regime(self, regime: str, description: str = "") -> Any | None:
        from .risk_alert import RiskAlertType

        if regime in ["crash", "extreme_volatility"]:
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.MARKET_REGIME,
                level=AlertLevel.CRITICAL,
                title=f"市场状态预警: {regime}",
                message=f"当前市场状态: {regime}。{description}",
                data={"regime": regime, "description": description},
            )
        elif regime in ["high_volatility", "bear"]:
            return self._create_alert(  # type: ignore[attr-defined]
                alert_type=RiskAlertType.MARKET_REGIME,
                level=AlertLevel.WARNING,
                title=f"市场状态提醒: {regime}",
                message=f"当前市场状态: {regime}。{description}",
                data={"regime": regime, "description": description},
            )
        return None

    def run_all_checks(
        self,
        portfolio_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> list[Any]:
        from .risk_alert import RiskAlertItem

        alerts: list[RiskAlertItem] = []

        drawdown = portfolio_data.get("max_drawdown")
        if drawdown is not None:
            alert = self.check_max_drawdown(drawdown, portfolio_data.get("name", "default"))
            if alert:
                alerts.append(alert)

        volatility = portfolio_data.get("volatility")
        if volatility is not None:
            alert = self.check_volatility(volatility, portfolio_data.get("name", "default"))
            if alert:
                alerts.append(alert)

        holdings = portfolio_data.get("holdings")
        if holdings:
            alert = self.check_concentration(holdings)
            if alert:
                alerts.append(alert)

        position = portfolio_data.get("total_position")
        if position is not None:
            alert = self.check_position_limit(position)
            if alert:
                alerts.append(alert)

        if market_data:
            regime = market_data.get("regime")
            if regime:
                alert = self.check_market_regime(regime, market_data.get("description", ""))
                if alert:
                    alerts.append(alert)

            for stock_data in market_data.get("stocks", []):
                change = stock_data.get("change_percent")
                if change is not None and abs(change) >= self.config.price_change_threshold:  # type: ignore[attr-defined]
                    alert = self.check_price_change(
                        stock_data.get("name", ""),
                        stock_data.get("code", ""),
                        change,
                    )
                    if alert:
                        alerts.append(alert)

        return alerts


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
