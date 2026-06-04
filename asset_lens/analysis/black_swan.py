"""
Black Swan Alert Module.
黑天鹅预警模块 - 系统性风险预警

功能:
1. 市场系统性风险监控
2. 行业风险预警
3. 个股风险预警
4. 外部风险监控
5. 风险等级评估
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache_list, write_json_cache


class BlackSwanRiskLevel(Enum):
    """黑天鹅风险等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""

    MARKET_CRASH = "market_crash"  # 市场暴跌
    POLICY_CHANGE = "policy_change"  # 政策变化
    INDUSTRY_RISK = "industry_risk"  # 行业风险
    COMPANY_RISK = "company_risk"  # 公司风险
    LIQUIDITY_RISK = "liquidity_risk"  # 流动性风险
    EXTERNAL_SHOCK = "external_shock"  # 外部冲击
    SYSTEMIC_RISK = "systemic_risk"  # 系统性风险


@dataclass
class BlackSwanRiskAlert:
    """风险预警"""

    risk_type: RiskType
    risk_level: BlackSwanRiskLevel
    title: str
    description: str
    impact_stocks: list[str]
    suggested_action: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_type": self.risk_type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "impact_stocks": self.impact_stocks,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp,
        }


@dataclass
class MarketRiskAssessment:
    """市场风险评估"""

    overall_risk_level: BlackSwanRiskLevel
    market_trend: str
    volatility_level: float
    sentiment_score: float
    risk_alerts: list[BlackSwanRiskAlert]
    recommendations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class BlackSwanMonitor:
    """黑天鹅监控器"""

    MARKET_CRASH_THRESHOLD = -3.0
    HIGH_VOLATILITY_THRESHOLD = 3.0
    PANIC_SELLING_THRESHOLD = -5.0

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.cache_path / "risk_alerts.json"
        self.history_file = self.cache_path / "risk_history.json"

    def check_market_risk(self, market_data: dict[str, Any] | None = None) -> MarketRiskAssessment:
        """检查市场风险"""
        alerts: list[BlackSwanRiskAlert] = []
        recommendations: list[str] = []

        if market_data:
            index_change = market_data.get("index_change", 0)
            volatility = market_data.get("volatility", 0)
            market_data.get("sentiment", "中性")

            if index_change < self.PANIC_SELLING_THRESHOLD:
                alerts.append(
                    BlackSwanRiskAlert(
                        risk_type=RiskType.MARKET_CRASH,
                        risk_level=BlackSwanRiskLevel.CRITICAL,
                        title="市场恐慌性下跌",
                        description=f"大盘跌幅 {index_change:.2f}%，可能触发恐慌性抛售",
                        impact_stocks=["ALL"],
                        suggested_action="立即降低仓位，持有现金观望",
                    )
                )
                recommendations.append("🚨 建议立即减仓 50% 以上")
                recommendations.append("🚨 设置更严格的止损线")

            elif index_change < self.MARKET_CRASH_THRESHOLD:
                alerts.append(
                    BlackSwanRiskAlert(
                        risk_type=RiskType.MARKET_CRASH,
                        risk_level=BlackSwanRiskLevel.HIGH,
                        title="市场大幅下跌",
                        description=f"大盘跌幅 {index_change:.2f}%，市场风险上升",
                        impact_stocks=["ALL"],
                        suggested_action="谨慎操作，控制仓位",
                    )
                )
                recommendations.append("⚠️ 建议降低仓位至 30% 以下")
                recommendations.append("⚠️ 避免追高买入")

            if volatility > self.HIGH_VOLATILITY_THRESHOLD:
                alerts.append(
                    BlackSwanRiskAlert(
                        risk_type=RiskType.SYSTEMIC_RISK,
                        risk_level=BlackSwanRiskLevel.HIGH,
                        title="市场波动剧烈",
                        description=f"市场波动率 {volatility:.2f}%，不确定性增加",
                        impact_stocks=["ALL"],
                        suggested_action="减少交易频率，等待市场稳定",
                    )
                )
                recommendations.append("⚠️ 建议减少交易频率")

        if not alerts:
            alerts.append(
                BlackSwanRiskAlert(
                    risk_type=RiskType.SYSTEMIC_RISK,
                    risk_level=BlackSwanRiskLevel.LOW,
                    title="市场风险较低",
                    description="当前市场环境相对稳定",
                    impact_stocks=[],
                    suggested_action="正常执行交易策略",
                )
            )
            recommendations.append("✅ 可正常执行交易策略")

        overall_level = self._calculate_overall_risk(alerts)

        return MarketRiskAssessment(
            overall_risk_level=overall_level,
            market_trend=market_data.get("trend", "未知") if market_data else "未知",
            volatility_level=market_data.get("volatility", 0) if market_data else 0,
            sentiment_score=market_data.get("sentiment_score", 0.5) if market_data else 0.5,
            risk_alerts=alerts,
            recommendations=recommendations,
        )

    def check_portfolio_risk(
        self,
        holdings: list[dict[str, Any]],
        market_data: dict[str, Any] | None = None,
    ) -> list[BlackSwanRiskAlert]:
        """检查持仓风险"""
        alerts: list[BlackSwanRiskAlert] = []

        if not holdings:
            return alerts

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in holdings)
        losing_positions = [h for h in holdings if h.get("profit_rate", 0) < -5]
        high_concentration = self._check_concentration(holdings, total_value)

        if len(losing_positions) > len(holdings) * 0.5:
            alerts.append(
                BlackSwanRiskAlert(
                    risk_type=RiskType.COMPANY_RISK,
                    risk_level=BlackSwanRiskLevel.HIGH,
                    title="持仓大面积亏损",
                    description=f"{len(losing_positions)} 只股票亏损超过 5%",
                    impact_stocks=[h["code"] for h in losing_positions],
                    suggested_action="检查持仓，考虑止损",
                )
            )

        if high_concentration:
            alerts.append(
                BlackSwanRiskAlert(
                    risk_type=RiskType.SYSTEMIC_RISK,
                    risk_level=BlackSwanRiskLevel.MEDIUM,
                    title="持仓集中度过高",
                    description="单一行业/股票占比过高",
                    impact_stocks=high_concentration,
                    suggested_action="分散持仓，降低集中度",
                )
            )

        for holding in holdings:
            profit_rate = holding.get("profit_rate", 0)
            if profit_rate < -15:
                alerts.append(
                    BlackSwanRiskAlert(
                        risk_type=RiskType.COMPANY_RISK,
                        risk_level=BlackSwanRiskLevel.CRITICAL,
                        title=f"{holding.get('name', holding['code'])} 严重亏损",
                        description=f"亏损 {abs(profit_rate):.2f}%",
                        impact_stocks=[holding["code"]],
                        suggested_action="立即止损",
                    )
                )

        return alerts

    def check_industry_risk(
        self,
        industry_data: dict[str, Any],
        holdings: list[dict[str, Any]],
    ) -> list[BlackSwanRiskAlert]:
        """检查行业风险"""
        alerts: list[BlackSwanRiskAlert] = []

        for industry, data in industry_data.items():
            industry_change = data.get("change", 0)
            if industry_change < -5:
                industry_stocks = [h["code"] for h in holdings if h.get("industry") == industry]
                if industry_stocks:
                    alerts.append(
                        BlackSwanRiskAlert(
                            risk_type=RiskType.INDUSTRY_RISK,
                            risk_level=BlackSwanRiskLevel.HIGH,
                            title=f"{industry} 行业风险",
                            description=f"行业跌幅 {industry_change:.2f}%",
                            impact_stocks=industry_stocks,
                            suggested_action=f"考虑减持 {industry} 相关股票",
                        )
                    )

        return alerts

    def check_external_risk(self, external_events: list[dict[str, Any]]) -> list[BlackSwanRiskAlert]:
        """检查外部风险"""
        alerts: list[BlackSwanRiskAlert] = []

        for event in external_events:
            severity = event.get("severity", "low")
            risk_level = BlackSwanRiskLevel.HIGH if severity == "high" else BlackSwanRiskLevel.MEDIUM

            alerts.append(
                BlackSwanRiskAlert(
                    risk_type=RiskType.EXTERNAL_SHOCK,
                    risk_level=risk_level,
                    title=event.get("title", "外部风险事件"),
                    description=event.get("description", ""),
                    impact_stocks=event.get("impact_stocks", []),
                    suggested_action=event.get("suggested_action", "密切关注事态发展"),
                )
            )

        return alerts

    def _calculate_overall_risk(self, alerts: list[BlackSwanRiskAlert]) -> BlackSwanRiskLevel:
        """计算整体风险等级"""
        if not alerts:
            return BlackSwanRiskLevel.LOW

        critical_count = sum(1 for a in alerts if a.risk_level == BlackSwanRiskLevel.CRITICAL)
        high_count = sum(1 for a in alerts if a.risk_level == BlackSwanRiskLevel.HIGH)

        if critical_count > 0:
            return BlackSwanRiskLevel.CRITICAL
        elif high_count >= 2:
            return BlackSwanRiskLevel.HIGH
        elif high_count > 0:
            return BlackSwanRiskLevel.MEDIUM
        else:
            return BlackSwanRiskLevel.LOW

    def _check_concentration(self, holdings: list[dict[str, Any]], total_value: float) -> list[str]:
        """检查持仓集中度"""
        if total_value <= 0:
            return []

        concentrated_stocks: list[str] = []
        for holding in holdings:
            value = holding.get("current_value", holding.get("amount", 0))
            if value / total_value > 0.3:
                concentrated_stocks.append(holding["code"])

        return concentrated_stocks

    def save_alerts(self, alerts: list[BlackSwanRiskAlert]) -> None:
        """保存预警记录"""
        history: list[dict[str, Any]] = read_json_cache_list(self.history_file) or []

        for alert in alerts:
            history.append(alert.to_dict())

        write_json_cache(self.history_file, history[-100:])

    def get_recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近预警"""
        history = read_json_cache_list(self.history_file)
        if history:
            return history[-limit:]
        return []

    def format_assessment(self, assessment: MarketRiskAssessment) -> str:
        """格式化风险评估报告"""
        level_emoji = {
            BlackSwanRiskLevel.LOW: "🟢",
            BlackSwanRiskLevel.MEDIUM: "🟡",
            BlackSwanRiskLevel.HIGH: "🟠",
            BlackSwanRiskLevel.CRITICAL: "🔴",
        }

        lines = [
            "\n🦢 黑天鹅风险评估报告",
            "=" * 60,
            f"整体风险等级: {level_emoji[assessment.overall_risk_level]} {assessment.overall_risk_level.value.upper()}",
            f"市场趋势: {assessment.market_trend}",
            f"波动率: {assessment.volatility_level:.2f}%",
            f"情绪评分: {assessment.sentiment_score:.2f}",
            "",
            "⚠️ 风险预警:",
        ]

        for alert in assessment.risk_alerts:
            emoji = level_emoji[alert.risk_level]
            lines.append(f"  {emoji} [{alert.risk_type.value}] {alert.title}")
            lines.append(f"     {alert.description}")
            if alert.impact_stocks and alert.impact_stocks != ["ALL"]:
                lines.append(f"     影响股票: {', '.join(alert.impact_stocks[:5])}")
            lines.append(f"     建议操作: {alert.suggested_action}")

        lines.append("")
        lines.append("💡 操作建议:")
        lines.extend(f"  {rec}" for rec in assessment.recommendations)

        return "\n".join(lines)


black_swan_monitor = BlackSwanMonitor()
