import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    max_single_position: float = 0.2
    max_total_position: float = 0.8
    stop_loss_default: float = -0.08
    take_profit_default: float = 0.15
    risk_tolerance: str = "medium"


@dataclass
class PositionAdvice:
    code: str
    name: str
    current_position: float
    suggested_position: float
    action: str
    reason: str


@dataclass
class RiskWarning:
    warning_type: str
    level: str
    message: str
    code: str | None = None
    timestamp: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class RiskPositionMixin:
    def get_position_advice(self, holdings: list[dict[str, Any]]) -> list[PositionAdvice]:
        advices = []

        total_value = sum(h.get("market_value", h.get("amount", 0)) for h in holdings)

        if total_value <= 0:
            return advices

        for holding in holdings:
            code = holding.get("code", "")
            name = holding.get("name", "")
            market_value = holding.get("market_value", holding.get("amount", 0))
            current_position = market_value / total_value

            suggested_position = current_position
            action = "hold"
            reason = ""

            if current_position > self.config.max_single_position:
                suggested_position = self.config.max_single_position
                action = "decrease"
                reason = f"仓位 {current_position:.1%} 超过单只上限 {self.config.max_single_position:.1%}"

            profit_rate = holding.get("profit_rate", 0)
            if profit_rate < -10:
                suggested_position = min(suggested_position, 0.1)
                action = "decrease"
                reason = f"亏损 {profit_rate:.1f}%，建议减仓止损"

            if current_position < 0.05 and profit_rate > 5:
                suggested_position = min(current_position * 1.5, self.config.max_single_position)
                action = "increase"
                reason = f"仓位偏低且盈利 {profit_rate:.1f}%，可适当加仓"

            advices.append(
                PositionAdvice(
                    code=code,
                    name=name,
                    current_position=current_position,
                    suggested_position=suggested_position,
                    action=action,
                    reason=reason,
                )
            )

        return advices

    def check_position_concentration(self, holdings: list[dict[str, Any]]) -> list[RiskWarning]:
        warnings = []

        total_value = sum(h.get("market_value", h.get("amount", 0)) for h in holdings)

        if total_value <= 0:
            return warnings

        industry_positions: dict[str, float] = {}
        for holding in holdings:
            industry = holding.get("industry", "未知")
            market_value = holding.get("market_value", holding.get("amount", 0))
            industry_positions[industry] = industry_positions.get(industry, 0) + market_value

        for industry, value in industry_positions.items():
            ratio = value / total_value
            if ratio > 0.4:
                warnings.append(
                    RiskWarning(
                        warning_type="concentration",
                        level="high",
                        message=f"行业 {industry} 集中度 {ratio:.1%} 过高",
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        details={"industry": industry, "ratio": ratio},
                    )
                )
            elif ratio > 0.3:
                warnings.append(
                    RiskWarning(
                        warning_type="concentration",
                        level="medium",
                        message=f"行业 {industry} 集中度 {ratio:.1%} 偏高",
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        details={"industry": industry, "ratio": ratio},
                    )
                )

        for holding in holdings:
            market_value = holding.get("market_value", holding.get("amount", 0))
            ratio = market_value / total_value
            if ratio > 0.2:
                warnings.append(
                    RiskWarning(
                        warning_type="single_stock",
                        level="high",
                        message=f"{holding.get('name', '')} 单只仓位 {ratio:.1%} 过高",
                        code=holding.get("code"),
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        details={"name": holding.get("name"), "ratio": ratio},
                    )
                )

        return warnings

    def calculate_stop_loss_take_profit(
        self,
        code: str,
        buy_price: float,
        atr: float | None = None,
        strategy_name: str | None = None,
    ) -> dict[str, Any]:
        from ..strategy.engine import strategy_engine

        result = {
            "code": code,
            "buy_price": buy_price,
            "stop_loss": 0,
            "stop_loss_price": 0,
            "take_profit": 0,
            "take_profit_price": 0,
            "risk_reward_ratio": 0,
            "method": "default",
        }

        stop_loss = self.config.stop_loss_default
        take_profit = self.config.take_profit_default

        if strategy_name:
            strategy = strategy_engine.get_strategy(strategy_name)
            if strategy:
                if strategy.stop_loss:
                    stop_loss = strategy.stop_loss
                if strategy.take_profit:
                    take_profit = strategy.take_profit

        if atr and atr > 0:
            stop_loss_price = buy_price - 2 * atr
            stop_loss_pct = (stop_loss_price - buy_price) / buy_price
            take_profit_price = buy_price + 3 * atr
            take_profit_pct = (take_profit_price - buy_price) / buy_price
            result["method"] = "atr"
        else:
            stop_loss_price = buy_price * (1 + stop_loss)
            stop_loss_pct = stop_loss
            take_profit_price = buy_price * (1 + take_profit)
            take_profit_pct = take_profit
            result["method"] = "percentage"

        result["stop_loss"] = stop_loss_pct
        result["stop_loss_price"] = stop_loss_price
        result["take_profit"] = take_profit_pct
        result["take_profit_price"] = take_profit_price

        if stop_loss_pct != 0:
            result["risk_reward_ratio"] = abs(take_profit_pct / stop_loss_pct)

        return result
