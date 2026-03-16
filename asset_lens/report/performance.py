"""
Performance Analysis - 绩效分析模块
"""

from decimal import Decimal
from typing import Any, Dict, List

from ..data.models import InvestmentProduct, InvestmentType, Portfolio, RiskLevel


class PerformanceAnalyzer:
    """绩效分析器"""

    def generate_investment_efficiency(self, portfolio: Portfolio) -> Dict[str, Any]:
        """生成投资效率分析

        Args:
            portfolio: 投资组合对象

        Returns:
            投资效率数据
        """
        total_amount = Decimal("0")
        total_profit = Decimal("0")
        total_days = 0
        product_count = 0

        for product in portfolio.products:
            if product.current_amount:
                total_amount += product.current_amount
            if product.profit_amount:
                total_profit += product.profit_amount
            if product.investment_days:
                total_days += product.investment_days
            product_count += 1

        avg_days = total_days / product_count if product_count > 0 else 0
        overall_return = (
            (total_profit / total_amount * 100) if total_amount > 0 else Decimal("0")
        )
        annualized_return = (
            overall_return * Decimal("365") / Decimal(str(avg_days)) if avg_days > 0 else Decimal("0")
        )

        return {
            "total_amount": str(total_amount),
            "total_profit": str(total_profit),
            "overall_return": f"{overall_return:.2f}%",
            "annualized_return": f"{annualized_return:.2f}%",
            "avg_investment_days": avg_days,
            "product_count": product_count,
        }

    def generate_optimization_suggestions(
        self, portfolio: Portfolio
    ) -> List[Dict[str, Any]]:
        """生成优化建议

        Args:
            portfolio: 投资组合对象

        Returns:
            优化建议列表
        """
        suggestions = []

        type_distribution: Dict[str, Decimal] = {}
        for product in portfolio.products:
            type_name = product.investment_type.value
            amount = product.current_amount or Decimal("0")
            type_distribution[type_name] = (
                type_distribution.get(type_name, Decimal("0")) + amount
            )

        total_amount = sum(type_distribution.values())

        for type_name, amount in type_distribution.items():
            if total_amount > 0:
                ratio = amount / total_amount
                if ratio > Decimal("0.5"):
                    suggestions.append(
                        {
                            "type": "diversification",
                            "level": "warning",
                            "message": f"{type_name}占比过高（{ratio * 100:.1f}%）",
                            "suggestion": "建议分散投资，降低单一类型占比",
                        }
                    )

        low_return_products = [
            p
            for p in portfolio.products
            if p.annual_return is not None and p.annual_return < Decimal("2")
        ]

        if low_return_products:
            suggestions.append(
                {
                    "type": "performance",
                    "level": "info",
                    "message": f"发现 {len(low_return_products)} 个低收益产品",
                    "suggestion": "考虑调整或替换低收益产品",
                }
            )

        return suggestions

    def generate_investment_advice(self, portfolio: Portfolio) -> List[str]:
        """生成投资建议

        Args:
            portfolio: 投资组合对象

        Returns:
            投资建议列表
        """
        advice = []

        total_amount = sum(
            p.current_amount or Decimal("0") for p in portfolio.products
        )
        total_profit = sum(
            p.profit_amount or Decimal("0") for p in portfolio.products
        )

        if total_amount > 0:
            return_rate = total_profit / total_amount * 100

            if return_rate > Decimal("10"):
                advice.append("投资组合表现优秀，建议保持当前配置")
            elif return_rate > Decimal("5"):
                advice.append("投资组合表现良好，可适当优化配置")
            elif return_rate > Decimal("0"):
                advice.append("投资组合表现一般，建议优化产品结构")
            else:
                advice.append("投资组合表现不佳，建议重新评估投资策略")

        risk_count = sum(
            1
            for p in portfolio.products
            if p.risk_level == RiskLevel.HIGH
        )
        if risk_count > len(portfolio.products) * 0.5:
            advice.append("高风险产品占比较高，建议适当降低风险敞口")

        return advice


performance_analyzer = PerformanceAnalyzer()
