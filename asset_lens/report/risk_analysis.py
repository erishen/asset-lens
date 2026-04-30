"""
Risk Analysis - 风险分析模块
"""

from decimal import Decimal
from typing import Any

from ..data.models import Portfolio, RiskLevel


class RiskAnalyzer:
    """风险分析器"""

    def get_type_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取投资类型分布

        Args:
            portfolio: 投资组合对象

        Returns:
            类型分布数据
        """
        type_amounts: dict[str, Decimal] = {}
        for product in portfolio.products:
            type_name = product.investment_type.value
            amount = product.current_amount or Decimal("0")
            type_amounts[type_name] = type_amounts.get(type_name, Decimal("0")) + amount

        total = sum(type_amounts.values())
        distribution = {
            type_name: {
                "amount": str(amount),
                "percentage": f"{(amount / total * 100):.2f}%" if total > 0 else "0%",
            }
            for type_name, amount in type_amounts.items()
        }

        return {
            "total_amount": str(total),
            "distribution": distribution,
        }

    def get_risk_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取风险等级分布

        Args:
            portfolio: 投资组合对象

        Returns:
            风险分布数据
        """
        risk_amounts: dict[str, Decimal] = {}
        for product in portfolio.products:
            risk_level = product.risk_level.value if product.risk_level else "未知"
            amount = product.current_amount or Decimal("0")
            risk_amounts[risk_level] = risk_amounts.get(risk_level, Decimal("0")) + amount

        total = sum(risk_amounts.values())
        distribution = {
            risk_level: {
                "amount": str(amount),
                "percentage": f"{(amount / total * 100):.2f}%" if total > 0 else "0%",
            }
            for risk_level, amount in risk_amounts.items()
        }

        return {
            "total_amount": str(total),
            "distribution": distribution,
        }

    def generate_risk_warnings(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成风险预警

        Args:
            portfolio: 投资组合对象

        Returns:
            风险预警列表
        """
        warnings = []

        high_risk_amount = Decimal("0")
        total_amount = Decimal("0")

        for product in portfolio.products:
            amount = product.current_amount or Decimal("0")
            total_amount += amount

            if product.risk_level == RiskLevel.HIGH:
                high_risk_amount += amount

            if product.maturity_date:
                from datetime import date

                days_to_maturity = (product.maturity_date - date.today()).days
                if 0 < days_to_maturity <= 30:
                    warnings.append(
                        {
                            "type": "maturity",
                            "level": "info",
                            "product": product.name,
                            "message": f"即将到期（{days_to_maturity}天后）",
                            "amount": str(amount),
                        }
                    )

        if total_amount > 0:
            high_risk_ratio = high_risk_amount / total_amount
            if high_risk_ratio > Decimal("0.5"):
                warnings.append(
                    {
                        "type": "concentration",
                        "level": "warning",
                        "message": f"高风险产品占比过高（{high_risk_ratio * 100:.1f}%）",
                        "suggestion": "建议降低高风险产品比例",
                    }
                )

        return warnings


risk_analyzer = RiskAnalyzer()
