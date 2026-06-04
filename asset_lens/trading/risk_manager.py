import logging
from datetime import datetime
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache, write_json_cache
from .risk_position import PositionAdvice, RiskConfig, RiskPositionMixin, RiskWarning

logger = logging.getLogger(__name__)


class RiskManager(RiskPositionMixin):
    RISK_TOLERANCE_POSITIONS = {
        "low": {"max_single": 0.1, "max_total": 0.5, "stop_loss": -0.05},
        "medium": {"max_single": 0.2, "max_total": 0.7, "stop_loss": -0.08},
        "high": {"max_single": 0.3, "max_total": 0.9, "stop_loss": -0.12},
    }

    def __init__(self):
        self.cache_path = config.cache_path
        self.risk_path = self.cache_path / "risk_management"
        self.risk_path.mkdir(parents=True, exist_ok=True)
        self.warnings_file = self.risk_path / "risk_warnings.json"
        self.config = RiskConfig()
        self.warnings: list[RiskWarning] = []
        self._current_regime = None
        self._regime_thresholds: dict[str, float] = {}
        self._load_warnings()

    def adjust_for_market_regime(
        self,
        index_returns: list[float] | None = None,
        regime=None,
    ) -> dict[str, Any]:
        from ..monitoring.risk_analyzer import MarketRegime, RiskAnalyzer

        analyzer = RiskAnalyzer()

        if regime is None and index_returns is not None:
            regime = analyzer.detect_market_regime(index_returns)
        elif regime is None:
            regime = MarketRegime.SIDEWAYS

        self._current_regime = regime
        self._regime_thresholds = analyzer.get_regime_thresholds(regime)

        if "stop_loss" in self._regime_thresholds:
            self.config.stop_loss_default = self._regime_thresholds["stop_loss"]

        if "position_limit" in self._regime_thresholds:
            self.config.max_total_position = self._regime_thresholds["position_limit"]

        return {
            "regime": regime.value if isinstance(regime, MarketRegime) else regime,
            "description": analyzer.get_regime_description(regime),
            "thresholds": self._regime_thresholds,
            "adjusted_config": {
                "stop_loss": self.config.stop_loss_default,
                "max_total_position": self.config.max_total_position,
                "max_single_position": self.config.max_single_position,
            },
        }

    def set_risk_tolerance(self, tolerance: str) -> dict[str, Any]:
        if tolerance not in self.RISK_TOLERANCE_POSITIONS:
            return {"success": False, "message": f"无效的风险偏好: {tolerance}"}

        positions = self.RISK_TOLERANCE_POSITIONS[tolerance]
        self.config.risk_tolerance = tolerance
        self.config.max_single_position = positions["max_single"]
        self.config.max_total_position = positions["max_total"]
        self.config.stop_loss_default = positions["stop_loss"]

        return {
            "success": True,
            "tolerance": tolerance,
            "config": {
                "max_single_position": self.config.max_single_position,
                "max_total_position": self.config.max_total_position,
                "stop_loss_default": self.config.stop_loss_default,
            },
        }

    def check_risks(self, holdings: list[dict[str, Any]]) -> list[RiskWarning]:
        self.warnings = []

        total_value = sum(h.get("market_value", h.get("amount", 0)) for h in holdings)

        if total_value <= 0:
            return self.warnings

        total_position = sum(
            1 for h in holdings if h.get("market_value", h.get("amount", 0)) > 0
        ) / max(len(holdings), 1)

        if total_position > self.config.max_total_position:
            self.warnings.append(
                RiskWarning(
                    warning_type="position",
                    level="high",
                    message=f"总仓位 {total_position:.1%} 超过上限 {self.config.max_total_position:.1%}",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            )

        self.warnings.extend(self.check_position_concentration(holdings))

        for holding in holdings:
            profit_rate = holding.get("profit_rate", 0)
            if profit_rate < -15:
                self.warnings.append(
                    RiskWarning(
                        warning_type="stop_loss",
                        level="critical",
                        message=f"{holding.get('name', '')} 亏损 {profit_rate:.1f}%，建议立即止损",
                        code=holding.get("code"),
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                )
            elif profit_rate < self.config.stop_loss_default * 100:
                self.warnings.append(
                    RiskWarning(
                        warning_type="stop_loss",
                        level="high",
                        message=f"{holding.get('name', '')} 亏损 {profit_rate:.1f}%，接近止损线",
                        code=holding.get("code"),
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                )

        self._save_warnings()
        return self.warnings

    def get_risk_summary(self, pool_name: str = "default") -> dict[str, Any]:
        from ..trading.stock_pool import StockPool

        pool = StockPool(pool_name)
        holdings = pool.list_stocks(status="holding")

        warnings = self.check_risks(holdings)

        critical = [w for w in warnings if w.level == "critical"]
        high = [w for w in warnings if w.level == "high"]
        medium = [w for w in warnings if w.level == "medium"]

        return {
            "total_warnings": len(warnings),
            "critical_count": len(critical),
            "high_count": len(high),
            "medium_count": len(medium),
            "warnings": [
                {"type": w.warning_type, "level": w.level, "message": w.message, "code": w.code}
                for w in warnings
            ],
            "config": {
                "risk_tolerance": self.config.risk_tolerance,
                "max_single_position": self.config.max_single_position,
                "max_total_position": self.config.max_total_position,
                "stop_loss_default": self.config.stop_loss_default,
                "take_profit_default": self.config.take_profit_default,
            },
            "market_regime": self._current_regime.value if self._current_regime else "unknown",
        }

    def _load_warnings(self) -> None:
        data = read_json_cache(self.warnings_file)
        if data:
            self.warnings = [
                RiskWarning(
                    warning_type=w.get("warning_type", ""),
                    level=w.get("level", ""),
                    message=w.get("message", ""),
                    code=w.get("code"),
                    timestamp=w.get("timestamp", ""),
                    details=w.get("details", {}),
                )
                for w in data
            ]
        else:
            self.warnings = []

    def _save_warnings(self) -> None:
        data = [
            {
                "warning_type": w.warning_type,
                "level": w.level,
                "message": w.message,
                "code": w.code,
                "timestamp": w.timestamp,
                "details": w.details,
            }
            for w in self.warnings
        ]
        write_json_cache(self.warnings_file, data)


risk_manager = RiskManager()
