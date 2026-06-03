from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asset_lens.monitoring.risk_analyzer import RiskAnalyzer
    from asset_lens.trading.risk_manager import RiskManager


@dataclass
class RiskSummary:
    risk_score: float
    risk_level: str
    total_position: float
    warnings: list[str]
    suggestions: list[str]


class RiskService:
    def __init__(self) -> None:
        self._manager: RiskManager | None = None
        self._analyzer: RiskAnalyzer | None = None

    @property
    def manager(self) -> "RiskManager":
        if self._manager is None:
            from asset_lens.trading.risk_manager import RiskManager

            self._manager = RiskManager()
        return self._manager

    @property
    def analyzer(self) -> "RiskAnalyzer":
        if self._analyzer is None:
            from asset_lens.monitoring.risk_analyzer import RiskAnalyzer

            self._analyzer = RiskAnalyzer()
        return self._analyzer

    def get_risk_summary(self, pool_name: str = "default") -> dict[str, Any]:
        result: dict[str, Any] = self.manager.get_risk_summary(pool_name)
        return result

    def calculate_metrics(
        self,
        returns: list[float],
        values: list[float] | None = None,
    ) -> Any:
        return self.analyzer.calculate_all_metrics(returns, values)

    def calculate_volatility(self, returns: list[float]) -> float:
        result: float = self.analyzer.calculate_volatility(returns)
        return result

    def calculate_max_drawdown(self, values: list[float]) -> float:
        result: float = self.analyzer.calculate_max_drawdown(values)
        return result

    def calculate_sharpe_ratio(
        self,
        returns: list[float],
        risk_free_rate: float = 0.03,
    ) -> float:
        result: float = self.analyzer.calculate_sharpe_ratio(returns, risk_free_rate)
        return result

    def check_risk_thresholds(
        self,
        metrics: Any,
        thresholds: dict[str, float] | None = None,
    ) -> list[Any]:
        result: list[Any] = self.analyzer.check_risk_thresholds(metrics, thresholds)
        return result

    def generate_risk_report(self, metrics: Any, alerts: list[Any]) -> str:
        result: str = self.analyzer.generate_risk_report(metrics, alerts)
        return result

    def detect_market_regime(self, index_returns: list[float]) -> str:
        regime = self.analyzer.detect_market_regime(index_returns)
        return regime.value

    def adjust_for_market_regime(
        self,
        index_returns: list[float] | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = self.manager.adjust_for_market_regime(index_returns)
        return result

    def get_regime_description(self, regime: str) -> str:
        from asset_lens.monitoring.risk_analyzer import MarketRegime

        regime_enum = MarketRegime(regime)
        return self.analyzer.get_regime_description(regime_enum)


risk_service = RiskService()
