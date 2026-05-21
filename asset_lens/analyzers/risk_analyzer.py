"""
Risk analyzer for asset-lens.
风险分析器 - 包含风险相关分析方法
"""

import warnings
from decimal import Decimal
from typing import Any

from ..config import config
from ..data.models import Portfolio


class LegacyRiskAnalyzer:
    """风险分析器 (已废弃，请使用 asset_lens.monitoring.risk_analyzer.RiskAnalyzer)"""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "LegacyRiskAnalyzer 已废弃，请使用 asset_lens.monitoring.risk_analyzer.RiskAnalyzer",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    def generate_risk_warnings(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成风险警告"""
        warnings = []

        low_returns = self._get_low_return_products(portfolio, threshold=config.min_return_threshold)
        if low_returns:
            warnings.append(
                {
                    "level": "warning",
                    "type": "low_return",
                    "message": f"发现 {len(low_returns)} 个收益率低于 {config.min_return_threshold}% 的产品（低于银行定期）",
                    "products": low_returns[:5],
                }
            )

        loss_products = [p for p in portfolio.products if p.profit_amount and p.profit_amount < Decimal("0")]
        if loss_products:
            loss_products.sort(key=lambda p: p.profit_amount or Decimal("0"))
            warnings.append(
                {
                    "level": "danger",
                    "type": "loss",
                    "message": f"发现 {len(loss_products)} 个严重亏损产品",
                    "products": [
                        {
                            "name": p.name,
                            "loss": str(abs(p.profit_amount)) if p.profit_amount else None,
                            "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                        }
                        for p in loss_products[:5]
                    ],
                }
            )

        risk_dist = portfolio.get_risk_distribution()
        high_risk_stats = risk_dist.get("高", {})
        if high_risk_stats and portfolio.total_value > Decimal("0"):
            high_risk_ratio = high_risk_stats.get("total_value", Decimal("0")) / portfolio.total_value
            if high_risk_ratio > Decimal("0.5"):
                warnings.append(
                    {
                        "level": "warning",
                        "type": "high_risk",
                        "message": f"高风险产品占比过高 ({high_risk_ratio * 100:.1f}%)",
                    }
                )

        long_term_low_return = [
            p
            for p in portfolio.products
            if p.investment_days
            and p.investment_days > 365
            and p.annual_return is not None
            and p.annual_return < Decimal("3")
        ]
        if long_term_low_return:
            warnings.append(
                {
                    "level": "info",
                    "type": "long_term_low_return",
                    "message": f"发现 {len(long_term_low_return)} 个长期投资但收益偏低的产品",
                    "products": [
                        {
                            "name": p.name,
                            "days": p.investment_days,
                            "return": f"{p.annual_return:.2f}%" if p.annual_return is not None else "-",
                        }
                        for p in long_term_low_return[:3]
                    ],
                }
            )

        return warnings

    def _get_low_return_products(self, portfolio: Portfolio, threshold: float = 2.0) -> list[dict[str, Any]]:
        """获取低收益产品列表"""
        low_return_products = [
            p for p in portfolio.products if p.annual_return is not None and p.annual_return < Decimal(str(threshold))
        ]

        low_return_products.sort(key=lambda p: p.annual_return or Decimal("0"))

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "annual_return": f"{p.annual_return:.2f}%",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "status": "收益过低" if p.annual_return and p.annual_return < Decimal("1") else "收益偏低",
            }
            for p in low_return_products
        ]

    def generate_optimization_suggestions(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成优化建议"""
        suggestions = []

        type_dist = portfolio.get_type_distribution()
        total_value = portfolio.total_value

        low_returns = self._get_low_return_products(portfolio, threshold=2.0)
        transferable_amount = sum(
            float(p.get("current_amount", 0)) for p in low_returns if p.get("status") == "收益过低"
        )
        potential_gain = transferable_amount * 0.03

        if total_value > Decimal("0"):
            suggestions.append(
                {
                    "category": "收益优化",
                    "priority": "high",
                    "suggestion": f"考虑将 {transferable_amount:.0f} 元低收益产品转投更高收益产品",
                    "detail": f"预计可增加收益 {potential_gain:.0f} 元/年",
                    "products": [p["name"] for p in low_returns[:3]],
                }
            )

        cash_products = type_dist.get("货币", {})
        if cash_products:
            cash_ratio = cash_products.get("total_value", Decimal("0")) / total_value
            if cash_ratio > Decimal("0.3"):
                suggestions.append(
                    {
                        "category": "资产配置",
                        "priority": "medium",
                        "suggestion": "货币类资产占比较高，可考虑部分转投债券或固收产品",
                        "detail": f"当前货币类占比 {cash_ratio * 100:.1f}%",
                    }
                )

        risk_dist = portfolio.get_risk_distribution()
        high_risk_stats = risk_dist.get("高", {})
        if high_risk_stats:
            high_risk_ratio = high_risk_stats.get("total_value", Decimal("0")) / total_value
            if high_risk_ratio > Decimal("0.4"):
                suggestions.append(
                    {
                        "category": "风险控制",
                        "priority": "high",
                        "suggestion": "高风险产品占比过高，建议适当降低仓位",
                        "detail": f"当前高风险占比 {high_risk_ratio * 100:.1f}%",
                    }
                )

        suggestions.append(
            {
                "category": "定期检查",
                "priority": "low",
                "suggestion": "建议每月检查一次投资组合表现",
                "detail": "及时调整不达预期的产品",
            }
        )

        return suggestions

    def generate_investment_advice(self, portfolio: Portfolio) -> list[str]:
        """生成投资建议"""
        advice = []

        total_return = portfolio.overall_return_rate or Decimal("0")
        if total_return > Decimal("10"):
            advice.append("投资组合整体表现优秀，建议保持当前配置")
        elif total_return > Decimal("5"):
            advice.append("投资组合表现良好，可适当优化低收益产品")
        elif total_return > Decimal("0"):
            advice.append("投资组合表现一般，建议审视资产配置")
        else:
            advice.append("投资组合出现亏损，建议重新评估风险承受能力")

        risk_dist = portfolio.get_risk_distribution()
        high_risk_stats = risk_dist.get("高", {})
        if high_risk_stats and portfolio.total_value > Decimal("0"):
            high_risk_ratio = high_risk_stats.get("total_value", Decimal("0")) / portfolio.total_value
            if high_risk_ratio > Decimal("0.5"):
                advice.append("高风险产品占比过高，建议适当降低风险敞口")

        type_dist = portfolio.get_type_distribution()
        if len(type_dist) < 3:
            advice.append("投资类型较为集中，建议适当分散投资")

        return advice
