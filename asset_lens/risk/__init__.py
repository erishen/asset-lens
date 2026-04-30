"""
Risk Module - 统一风险入口
提供风险管理与分析的统一接口

此模块整合了两个风险相关模块的功能：
- RiskManager: 仓位管理、止损止盈、风险预警
- RiskAnalyzer: 风险指标计算、波动率、夏普比率等

使用示例:
    from asset_lens.risk import RiskService

    # 获取风险服务
    risk = RiskService()

    # 获取风险摘要（仓位、止损止盈）
    summary = risk.get_risk_summary()

    # 计算风险指标（波动率、夏普比率）
    metrics = risk.calculate_metrics(returns)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from asset_lens.monitoring.risk_analyzer import RiskAnalyzer
    from asset_lens.trading.risk_manager import RiskManager


@dataclass
class RiskSummary:
    """风险摘要"""

    risk_score: float
    risk_level: str
    total_position: float
    warnings: list[str]
    suggestions: list[str]


class RiskService:
    """
    风险服务 - 统一风险入口

    整合 RiskManager 和 RiskAnalyzer 的功能，
    提供一站式的风险管理与分析服务。
    """

    def __init__(self) -> None:
        self._manager: RiskManager | None = None
        self._analyzer: RiskAnalyzer | None = None

    @property
    def manager(self) -> "RiskManager":
        """获取风险管理器（仓位、止损止盈）"""
        if self._manager is None:
            from asset_lens.trading.risk_manager import RiskManager

            self._manager = RiskManager()
        return self._manager

    @property
    def analyzer(self) -> "RiskAnalyzer":
        """获取风险分析器（指标计算）"""
        if self._analyzer is None:
            from asset_lens.monitoring.risk_analyzer import RiskAnalyzer

            self._analyzer = RiskAnalyzer()
        return self._analyzer

    def get_risk_summary(self, pool_name: str = "default") -> dict[str, Any]:
        """
        获取风险摘要

        包含仓位、止损止盈、风险预警等信息

        Args:
            pool_name: 股票池名称

        Returns:
            风险摘要字典
        """
        result: dict[str, Any] = self.manager.get_risk_summary(pool_name)
        return result

    def calculate_metrics(
        self,
        returns: list[float],
        values: list[float] | None = None,
    ) -> Any:
        """
        计算风险指标

        Args:
            returns: 收益率序列
            values: 净值序列（可选）

        Returns:
            RiskMetrics 对象
        """
        return self.analyzer.calculate_all_metrics(returns, values)

    def calculate_volatility(self, returns: list[float]) -> float:
        """
        计算波动率

        Args:
            returns: 收益率序列

        Returns:
            波动率
        """
        result: float = self.analyzer.calculate_volatility(returns)
        return result

    def calculate_max_drawdown(self, values: list[float]) -> float:
        """
        计算最大回撤

        Args:
            values: 净值序列

        Returns:
            最大回撤
        """
        result: float = self.analyzer.calculate_max_drawdown(values)
        return result

    def calculate_sharpe_ratio(
        self,
        returns: list[float],
        risk_free_rate: float = 0.03,
    ) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率

        Returns:
            夏普比率
        """
        result: float = self.analyzer.calculate_sharpe_ratio(returns, risk_free_rate)
        return result

    def check_risk_thresholds(
        self,
        metrics: Any,
        thresholds: dict[str, float] | None = None,
    ) -> list[Any]:
        """
        检查风险阈值

        Args:
            metrics: 风险指标
            thresholds: 阈值字典

        Returns:
            风险预警列表
        """
        result: list[Any] = self.analyzer.check_risk_thresholds(metrics, thresholds)
        return result

    def generate_risk_report(self, metrics: Any, alerts: list[Any]) -> str:
        """
        生成风险报告

        Args:
            metrics: 风险指标
            alerts: 风险预警列表

        Returns:
            风险报告文本
        """
        result: str = self.analyzer.generate_risk_report(metrics, alerts)
        return result

    def detect_market_regime(self, index_returns: list[float]) -> str:
        """
        判断市场环境

        Args:
            index_returns: 指数收益率序列

        Returns:
            市场环境类型 (bull/bear/sideways/crisis)
        """
        regime = self.analyzer.detect_market_regime(index_returns)
        return regime.value

    def adjust_for_market_regime(
        self,
        index_returns: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        根据市场环境调整风险阈值

        Args:
            index_returns: 指数收益率序列

        Returns:
            调整结果字典
        """
        result: dict[str, Any] = self.manager.adjust_for_market_regime(index_returns)
        return result

    def get_regime_description(self, regime: str) -> str:
        """
        获取市场环境描述

        Args:
            regime: 市场环境类型

        Returns:
            市场环境描述
        """
        from asset_lens.monitoring.risk_analyzer import MarketRegime

        regime_enum = MarketRegime(regime)
        return self.analyzer.get_regime_description(regime_enum)


risk_service = RiskService()


__all__ = ["RiskService", "RiskSummary", "risk_service"]
