"""
Portfolio Rebalancing Module.
调仓建议模块 - 持仓优化建议

功能:
1. 持仓健康度评估
2. 调仓建议生成
3. 行业配置优化
4. 风险敞口分析
5. 资金效率优化
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config


class RebalanceAction(Enum):
    """调仓动作"""

    REDUCE = "reduce"  # 减仓
    INCREASE = "increase"  # 加仓
    SELL = "sell"  # 清仓
    HOLD = "hold"  # 持有
    SWAP = "swap"  # 换股


class RebalanceReason(Enum):
    """调仓原因"""

    STOP_LOSS = "stop_loss"  # 止损
    TAKE_PROFIT = "take_profit"  # 止盈
    HIGH_VALUATION = "high_valuation"  # 估值过高
    LOW_PERFORMANCE = "low_performance"  # 表现不佳
    INDUSTRY_ROTATION = "industry_rotation"  # 行业轮动
    RISK_CONTROL = "risk_control"  # 风险控制
    OPPORTUNITY_COST = "opportunity_cost"  # 机会成本
    CONCENTRATION = "concentration"  # 集中度调整


@dataclass
class RebalanceSuggestion:
    """调仓建议"""

    code: str
    name: str
    action: RebalanceAction
    reason: RebalanceReason
    current_value: float
    target_value: float
    confidence: float
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "action": self.action.value,
            "reason": self.reason.value,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "confidence": self.confidence,
            "description": self.description,
            "timestamp": self.timestamp,
        }


@dataclass
class PortfolioHealth:
    """持仓健康度"""

    overall_score: float
    diversification_score: float
    risk_score: float
    performance_score: float
    efficiency_score: float
    issues: list[str]
    suggestions: list[str]


@dataclass
class RebalanceReport:
    """调仓报告"""

    portfolio_health: PortfolioHealth
    rebalance_suggestions: list[RebalanceSuggestion]
    industry_allocation: dict[str, float]
    risk_exposure: dict[str, float]
    expected_improvement: float
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class PortfolioRebalancer:
    """持仓调仓器"""

    MAX_SINGLE_POSITION = 0.20
    MAX_INDUSTRY_POSITION = 0.40
    MIN_CASH_RATIO = 0.10
    STOP_LOSS_THRESHOLD = -0.08
    TAKE_PROFIT_THRESHOLD = 0.15
    LOW_PERFORMANCE_THRESHOLD = -0.05

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.history_file = self.cache_path / "rebalance_history.json"

    def analyze_portfolio(self, holdings: list[dict[str, Any]]) -> PortfolioHealth:
        """分析持仓健康度"""
        issues: list[str] = []
        suggestions: list[str] = []

        if not holdings:
            return PortfolioHealth(
                overall_score=0,
                diversification_score=0,
                risk_score=0,
                performance_score=0,
                efficiency_score=0,
                issues=["无持仓"],
                suggestions=["建议先建立基础仓位"],
            )

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)

        diversification_score = self._calculate_diversification(holdings, total_value)
        risk_score = self._calculate_risk_score(holdings, total_value)
        performance_score = self._calculate_performance_score(holdings)
        efficiency_score = self._calculate_efficiency_score(holdings)

        if diversification_score < 60:
            issues.append("持仓分散度不足")
            suggestions.append("建议增加持仓股票数量，分散风险")

        if risk_score < 60:
            issues.append("风险敞口过大")
            suggestions.append("建议降低单一股票/行业仓位")

        if performance_score < 50:
            issues.append("整体表现不佳")
            suggestions.append("建议检查持仓，考虑调仓")

        if efficiency_score < 60:
            issues.append("资金效率较低")
            suggestions.append("建议优化持仓结构，提高资金利用率")

        overall_score = (diversification_score + risk_score + performance_score + efficiency_score) / 4

        return PortfolioHealth(
            overall_score=overall_score,
            diversification_score=diversification_score,
            risk_score=risk_score,
            performance_score=performance_score,
            efficiency_score=efficiency_score,
            issues=issues,
            suggestions=suggestions,
        )

    def generate_suggestions(
        self,
        holdings: list[dict[str, Any]],
        market_data: dict[str, Any] | None = None,
        stock_scores: dict[str, float] | None = None,
    ) -> list[RebalanceSuggestion]:
        """生成调仓建议"""
        suggestions: list[RebalanceSuggestion] = []

        if not holdings:
            return suggestions

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)

        for holding in holdings:
            code = holding["code"]
            name = holding.get("name", code)
            current_value = holding.get("current_value", holding.get("amount", 0))
            profit_rate = holding.get("profit_rate", 0)
            position_ratio = current_value / total_value if total_value > 0 else 0

            stock_score = stock_scores.get(code, 50) if stock_scores else 50

            if profit_rate < self.STOP_LOSS_THRESHOLD:
                suggestions.append(
                    RebalanceSuggestion(
                        code=code,
                        name=name,
                        action=RebalanceAction.SELL,
                        reason=RebalanceReason.STOP_LOSS,
                        current_value=current_value,
                        target_value=0,
                        confidence=0.9,
                        description=f"触发止损线，亏损 {abs(profit_rate):.1%}，建议立即卖出",
                    )
                )

            elif profit_rate > self.TAKE_PROFIT_THRESHOLD:
                suggestions.append(
                    RebalanceSuggestion(
                        code=code,
                        name=name,
                        action=RebalanceAction.REDUCE,
                        reason=RebalanceReason.TAKE_PROFIT,
                        current_value=current_value,
                        target_value=current_value * 0.5,
                        confidence=0.8,
                        description=f"触发止盈线，盈利 {profit_rate:.1%}，建议减仓锁定收益",
                    )
                )

            elif position_ratio > self.MAX_SINGLE_POSITION:
                target_value = total_value * self.MAX_SINGLE_POSITION * 0.9
                suggestions.append(
                    RebalanceSuggestion(
                        code=code,
                        name=name,
                        action=RebalanceAction.REDUCE,
                        reason=RebalanceReason.RISK_CONTROL,
                        current_value=current_value,
                        target_value=target_value,
                        confidence=0.85,
                        description=f"仓位过重 ({position_ratio:.1%})，建议减仓至 {self.MAX_SINGLE_POSITION:.0%} 以下",
                    )
                )

            elif profit_rate < self.LOW_PERFORMANCE_THRESHOLD and stock_score < 40:
                suggestions.append(
                    RebalanceSuggestion(
                        code=code,
                        name=name,
                        action=RebalanceAction.SELL,
                        reason=RebalanceReason.LOW_PERFORMANCE,
                        current_value=current_value,
                        target_value=0,
                        confidence=0.7,
                        description=f"表现不佳 (亏损 {abs(profit_rate):.1%}，评分 {stock_score:.0f})，建议清仓",
                    )
                )

            elif stock_score > 80 and profit_rate < 5:
                suggestions.append(
                    RebalanceSuggestion(
                        code=code,
                        name=name,
                        action=RebalanceAction.INCREASE,
                        reason=RebalanceReason.OPPORTUNITY_COST,
                        current_value=current_value,
                        target_value=current_value * 1.5,
                        confidence=0.75,
                        description=f"优质股票 (评分 {stock_score:.0f})，建议加仓",
                    )
                )

        return suggestions

    def optimize_industry_allocation(
        self,
        holdings: list[dict[str, Any]],
        industry_views: dict[str, str] | None = None,
    ) -> dict[str, RebalanceSuggestion]:
        """优化行业配置"""
        suggestions: dict[str, RebalanceSuggestion] = {}

        industry_positions: dict[str, float] = {}
        total_value = 0

        for holding in holdings:
            industry = holding.get("industry", "未知")
            value = holding.get("current_value", holding.get("amount", 0))
            industry_positions[industry] = industry_positions.get(industry, 0) + value
            total_value += value

        if total_value <= 0:
            return suggestions

        for industry, value in industry_positions.items():
            ratio = value / total_value
            if ratio > self.MAX_INDUSTRY_POSITION:
                target_ratio = self.MAX_INDUSTRY_POSITION * 0.9
                suggestions[industry] = RebalanceSuggestion(
                    code="INDUSTRY",
                    name=industry,
                    action=RebalanceAction.REDUCE,
                    reason=RebalanceReason.CONCENTRATION,
                    current_value=value,
                    target_value=total_value * target_ratio,
                    confidence=0.8,
                    description=f"行业 {industry} 仓位过重 ({ratio:.1%})，建议分散配置",
                )

        return suggestions

    def calculate_risk_exposure(self, holdings: list[dict[str, Any]]) -> dict[str, float]:
        """计算风险敞口"""
        exposure: dict[str, float] = {
            "market_risk": 0,
            "industry_risk": 0,
            "concentration_risk": 0,
            "performance_risk": 0,
        }

        if not holdings:
            return exposure

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)

        losing_positions = [h for h in holdings if h.get("profit_rate", 0) < 0]
        losing_value = sum(h.get("current_value", h.get("amount", 0)) for h in losing_positions)

        industry_positions: dict[str, float] = {}
        for holding in holdings:
            industry = holding.get("industry", "未知")
            value = holding.get("current_value", holding.get("amount", 0))
            industry_positions[industry] = industry_positions.get(industry, 0) + value

        max_industry_ratio = (
            max(industry_positions.values()) / total_value if industry_positions and total_value > 0 else 0
        )
        max_position_ratio = (
            max(h.get("current_value", h.get("amount", 0)) for h in holdings) / total_value
            if holdings and total_value > 0
            else 0
        )

        exposure["market_risk"] = min(1.0, total_value / 100000)
        exposure["industry_risk"] = min(1.0, max_industry_ratio / self.MAX_INDUSTRY_POSITION)
        exposure["concentration_risk"] = min(1.0, max_position_ratio / self.MAX_SINGLE_POSITION)
        exposure["performance_risk"] = losing_value / total_value if total_value > 0 else 0

        return exposure

    def generate_report(
        self,
        holdings: list[dict[str, Any]],
        market_data: dict[str, Any] | None = None,
        stock_scores: dict[str, float] | None = None,
    ) -> RebalanceReport:
        """生成调仓报告"""
        health = self.analyze_portfolio(holdings)
        suggestions = self.generate_suggestions(holdings, market_data, stock_scores)
        self.optimize_industry_allocation(holdings)
        risk_exposure = self.calculate_risk_exposure(holdings)

        industry_allocation: dict[str, float] = {}
        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)
        for holding in holdings:
            industry = holding.get("industry", "未知")
            value = holding.get("current_value", holding.get("amount", 0))
            industry_allocation[industry] = (
                industry_allocation.get(industry, 0) + value / total_value if total_value > 0 else 0
            )

        expected_improvement = self._estimate_improvement(health, suggestions)

        return RebalanceReport(
            portfolio_health=health,
            rebalance_suggestions=suggestions,
            industry_allocation=industry_allocation,
            risk_exposure=risk_exposure,
            expected_improvement=expected_improvement,
        )

    def _calculate_diversification(self, holdings: list[dict[str, Any]], total_value: float) -> float:
        """计算分散度评分"""
        if total_value <= 0 or not holdings:
            return 0.0

        num_stocks = len(holdings)
        industries = {h.get("industry", "未知") for h in holdings}

        stock_score: float = float(min(100, num_stocks * 10))
        industry_score: float = float(min(100, len(industries) * 20))

        max_position = max(h.get("current_value", h.get("amount", 0)) for h in holdings)
        concentration_score: float = float(100 - (max_position / total_value * 100)) if total_value > 0 else 0.0

        return (stock_score + industry_score + concentration_score) / 3

    def _calculate_risk_score(self, holdings: list[dict[str, Any]], total_value: float) -> float:
        """计算风险评分"""
        if total_value <= 0 or not holdings:
            return 100.0

        max_position_ratio = max(h.get("current_value", h.get("amount", 0)) for h in holdings) / total_value

        industry_positions: dict[str, float] = {}
        for holding in holdings:
            industry = holding.get("industry", "未知")
            value = holding.get("current_value", holding.get("amount", 0))
            industry_positions[industry] = industry_positions.get(industry, 0) + value

        max_industry_ratio = max(industry_positions.values()) / total_value if industry_positions else 0

        position_risk: float = float(max(0, 100 - max_position_ratio * 100 / self.MAX_SINGLE_POSITION))
        industry_risk: float = float(max(0, 100 - max_industry_ratio * 100 / self.MAX_INDUSTRY_POSITION))

        return (position_risk + industry_risk) / 2

    def _calculate_performance_score(self, holdings: list[dict[str, Any]]) -> float:
        """计算表现评分"""
        if not holdings:
            return 0.0

        profit_rates = [h.get("profit_rate", 0) for h in holdings]
        avg_profit = sum(profit_rates) / len(profit_rates) if profit_rates else 0

        winning = sum(1 for r in profit_rates if r > 0)
        win_rate = winning / len(profit_rates) if profit_rates else 0

        profit_score: float = float(min(100, max(0, 50 + avg_profit * 10)))
        win_rate_score: float = float(win_rate * 100)

        return (profit_score + win_rate_score) / 2

    def _calculate_efficiency_score(self, holdings: list[dict[str, Any]]) -> float:
        """计算效率评分"""
        if not holdings:
            return 0.0

        active_positions = [h for h in holdings if h.get("current_value", h.get("amount", 0)) > 0]
        if not active_positions:
            return 0.0

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)
        avg_value = total_value / len(active_positions)

        efficiency: float = float(min(100, avg_value / 100))
        return efficiency

    def _estimate_improvement(self, health: PortfolioHealth, suggestions: list[RebalanceSuggestion]) -> float:
        """预估改善幅度"""
        if not suggestions:
            return 0

        improvement = 0
        for suggestion in suggestions:
            if suggestion.action == RebalanceAction.SELL:
                if suggestion.reason == RebalanceReason.STOP_LOSS:
                    improvement += 10
                elif suggestion.reason == RebalanceReason.LOW_PERFORMANCE:
                    improvement += 5
            elif suggestion.action == RebalanceAction.REDUCE:
                improvement += 3
            elif suggestion.action == RebalanceAction.INCREASE:
                improvement += 2

        return min(30, improvement)

    def format_report(self, report: RebalanceReport) -> str:
        """格式化报告"""
        health = report.portfolio_health

        lines = [
            "\n📊 持仓调仓建议报告",
            "=" * 60,
            f"整体健康度: {health.overall_score:.1f}/100",
            f"  分散度: {health.diversification_score:.1f}",
            f"  风险控制: {health.risk_score:.1f}",
            f"  表现评分: {health.performance_score:.1f}",
            f"  资金效率: {health.efficiency_score:.1f}",
            "",
        ]

        if health.issues:
            lines.append("⚠️ 问题:")
            for issue in health.issues:
                lines.append(f"  - {issue}")
            lines.append("")

        if report.rebalance_suggestions:
            lines.append("📋 调仓建议:")
            for sug in report.rebalance_suggestions:
                action_emoji = {
                    RebalanceAction.SELL: "🔴",
                    RebalanceAction.REDUCE: "🟡",
                    RebalanceAction.INCREASE: "🟢",
                    RebalanceAction.HOLD: "⚪",
                    RebalanceAction.SWAP: "🔄",
                }
                emoji = action_emoji.get(sug.action, "📊")
                lines.append(f"  {emoji} {sug.code} - {sug.name}")
                lines.append(f"     动作: {sug.action.value} | 原因: {sug.reason.value}")
                lines.append(f"     {sug.description}")
                lines.append(f"     置信度: {sug.confidence:.0%}")
            lines.append("")

        if report.industry_allocation:
            lines.append("📊 行业配置:")
            for industry, ratio in report.industry_allocation.items():
                status = "⚠️" if ratio > self.MAX_INDUSTRY_POSITION else "✅"
                lines.append(f"  {status} {industry}: {ratio:.1%}")
            lines.append("")

        if report.risk_exposure:
            lines.append("⚠️ 风险敞口:")
            for risk_type, value in report.risk_exposure.items():
                level = "高" if value > 0.7 else ("中" if value > 0.4 else "低")
                lines.append(f"  - {risk_type}: {value:.2f} ({level})")
            lines.append("")

        lines.append(f"📈 预估改善: +{report.expected_improvement:.1f} 分")

        return "\n".join(lines)


portfolio_rebalancer = PortfolioRebalancer()
