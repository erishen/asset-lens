"""
Portfolio analyzer for asset-lens.
投资组合分析器 - 包含投资组合相关分析方法
"""

from decimal import Decimal
from typing import Any

from ..data.models import Portfolio


class PortfolioAnalyzer:
    """投资组合分析器"""

    def generate_portfolio_summary(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成投资组合摘要

        Args:
            portfolio: 投资组合对象

        Returns:
            包含投资组合摘要的字典
        """
        total_products = len(portfolio.products)
        total_value = portfolio.total_value
        total_profit = portfolio.total_profit
        total_initial = sum(float(p.initial_amount or 0) for p in portfolio.products)
        total_return_rate = portfolio.overall_return_rate

        positive_products = [p for p in portfolio.products if p.profit_amount and p.profit_amount > Decimal("0")]
        negative_products = [p for p in portfolio.products if p.profit_amount and p.profit_amount < Decimal("0")]

        return {
            "total_products": total_products,
            "total_value": str(total_value),
            "total_initial": str(total_initial),
            "total_profit": str(total_profit),
            "total_return_rate": f"{total_return_rate:.2f}%" if total_return_rate is not None else "0.00%",
            "positive_count": len(positive_products),
            "negative_count": len(negative_products),
            "positive_avg_return": self._calculate_positive_avg_return(portfolio),
        }

    def _calculate_positive_avg_return(self, portfolio: Portfolio) -> str:
        """计算正收益产品的平均收益率"""
        positive_products = [
            p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("0")
        ]

        if not positive_products:
            return "N/A"
        avg_return = Decimal(
            str(sum(p.annual_return for p in positive_products if p.annual_return))
        ) / Decimal(str(len(positive_products)))
        return f"{avg_return:.2f}%"

    def get_top_performers(self, portfolio: Portfolio, top_n: int = 10) -> list[dict[str, Any]]:
        """获取收益率最高的产品"""
        products_with_return = [
            p
            for p in portfolio.products
            if p.annual_return is not None or p.return_rate is not None
        ]

        products_with_return.sort(
            key=lambda p: p.annual_return or p.return_rate or Decimal("0"), reverse=True
        )

        top_products = products_with_return[:top_n]

        return [
            {
                "rank": i + 1,
                "name": p.name,
                "type": p.investment_type.value,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                "annual_return": f"{p.annual_return:.2f}%" if p.annual_return else "-",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "investment_days": p.investment_days or "-",
            }
            for i, p in enumerate(top_products)
        ]

        top_products = products_with_return[:top_n]

        return [
            {
                "rank": i + 1,
                "name": p.name,
                "type": p.investment_type.value,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                "annual_return": f"{p.annual_return:.2f}%" if p.annual_return else "-",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "investment_days": p.investment_days or "-",
            }
            for i, p in enumerate(top_products)
        ]

    def get_low_return_products(
        self, portfolio: Portfolio, threshold: float = 2.0
    ) -> list[dict[str, Any]]:
        """获取低收益产品列表"""
        low_return_products = [
            p
            for p in portfolio.products
            if p.annual_return is not None and p.annual_return < Decimal(str(threshold))
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

    def get_short_term_observation_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """获取短期观察产品"""
        short_term_products = [
            p
            for p in portfolio.products
            if p.investment_days
            and p.investment_days < 90
            and p.annual_return
            and p.annual_return < Decimal("3")
        ]

        return [
            {
                "name": p.name,
                "annual_return": f"{p.annual_return:.2f}%",
                "investment_days": p.investment_days,
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "status": "短期波动(正常现象)"
                if p.profit_amount and p.profit_amount < Decimal("0")
                else "收益偏低(观察)",
            }
            for p in short_term_products
        ]

    def get_high_return_reference_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """获取高收益参考产品"""
        high_return_products = [
            p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("10")
        ]

        high_return_products.sort(key=lambda p: p.annual_return or Decimal("0"), reverse=True)

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "annual_return": f"{p.annual_return:.2f}%",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "investment_days": p.investment_days or "-",
            }
            for p in high_return_products
        ]

    def get_type_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取投资类型分布"""
        type_stats = portfolio.get_type_distribution()

        return {
            type_name: {
                "count": stats["count"],
                "total_value": str(stats["total_value"]),
                "percentage": f"{stats['percentage']:.2f}%",
                "product_names": [p.name for p in stats["products"]],
            }
            for type_name, stats in type_stats.items()
        }

    def get_risk_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取风险分布"""
        risk_stats = portfolio.get_risk_distribution()

        return {
            risk_name: {
                "count": stats["count"],
                "total_value": str(stats["total_value"]),
                "percentage": f"{stats['percentage']:.2f}%",
                "product_names": [p.name for p in stats["products"]],
            }
            for risk_name, stats in risk_stats.items()
        }

    def generate_special_bonds_analysis(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成特别国债分析"""
        special_bonds = []

        for product in portfolio.products:
            if product.investment_type and "国债" in product.investment_type.value:
                special_bonds.append(
                    {
                        "name": product.name,
                        "type": product.investment_type.value,
                        "current_amount": str(product.current_amount)
                        if product.current_amount
                        else "-",
                        "annual_return": f"{product.annual_return:.2f}%"
                        if product.annual_return
                        else "-",
                        "investment_days": product.investment_days or "-",
                    }
                )

        return special_bonds
