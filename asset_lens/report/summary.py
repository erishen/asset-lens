"""
Portfolio Summary - 投资组合摘要分析
"""

from decimal import Decimal
from typing import Any

from ..data.models import Portfolio


class PortfolioSummaryAnalyzer:
    """投资组合摘要分析器"""

    def generate_portfolio_summary(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成投资组合摘要

        Args:
            portfolio: 投资组合对象

        Returns:
            摘要数据字典
        """
        total_amount = sum(
            p.current_amount or Decimal("0") for p in portfolio.products
        )
        total_profit = sum(
            p.profit_amount or Decimal("0") for p in portfolio.products
        )
        total_initial = sum(
            p.initial_amount or Decimal("0") for p in portfolio.products
        )

        return {
            "total_products": len(portfolio.products),
            "total_amount": str(total_amount),
            "total_profit": str(total_profit),
            "total_initial": str(total_initial),
            "positive_avg_return": self._calculate_positive_avg_return(portfolio),
        }

    def _calculate_positive_avg_return(self, portfolio: Portfolio) -> str:
        """计算正收益产品的平均收益率"""
        positive_products = [
            p
            for p in portfolio.products
            if p.annual_return and p.annual_return > Decimal("0")
        ]

        if not positive_products:
            return "N/A"
        avg_return = Decimal(
            str(sum(p.annual_return for p in positive_products if p.annual_return))
        ) / Decimal(str(len(positive_products)))
        return f"{avg_return:.2f}%"

    def get_top_performers(
        self, portfolio: Portfolio, top_n: int = 10
    ) -> list[dict[str, Any]]:
        """获取收益率最高的产品

        Args:
            portfolio: 投资组合对象
            top_n: 返回的产品数量

        Returns:
            按收益率排序的产品列表
        """
        products_with_return = [
            p
            for p in portfolio.products
            if p.annual_return is not None or p.return_rate is not None
        ]

        products_with_return.sort(
            key=lambda p: p.annual_return or p.return_rate or Decimal("0"),
            reverse=True,
        )

        top_products = products_with_return[:top_n]

        return [
            {
                "rank": i + 1,
                "name": p.name,
                "type": p.investment_type.value,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                "annual_return": f"{p.annual_return:.2f}%"
                if p.annual_return
                else "-",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "investment_days": p.investment_days or "-",
            }
            for i, p in enumerate(top_products)
        ]

    def get_low_return_products(
        self, portfolio: Portfolio, threshold: float = 2.0
    ) -> list[dict[str, Any]]:
        """获取低收益产品列表

        Args:
            portfolio: 投资组合对象
            threshold: 收益率阈值

        Returns:
            低收益产品列表
        """
        low_return_products = [
            p
            for p in portfolio.products
            if p.annual_return is not None
            and p.annual_return < Decimal(str(threshold))
        ]

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "annual_return": f"{p.annual_return:.2f}%",
                "current_amount": str(p.current_amount),
                "investment_days": p.investment_days,
            }
            for p in low_return_products
        ]

    def get_short_term_observation_products(
        self, portfolio: Portfolio
    ) -> list[dict[str, Any]]:
        """获取短期观察产品列表

        Args:
            portfolio: 投资组合对象

        Returns:
            短期观察产品列表
        """
        short_term_products = [
            p
            for p in portfolio.products
            if p.investment_days is not None and p.investment_days <= 30
        ]

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "investment_days": p.investment_days,
                "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                "current_amount": str(p.current_amount),
            }
            for p in short_term_products
        ]

    def get_high_return_reference_products(
        self, portfolio: Portfolio
    ) -> list[dict[str, Any]]:
        """获取高收益参考产品列表

        Args:
            portfolio: 投资组合对象

        Returns:
            高收益参考产品列表
        """
        high_return_products = [
            p
            for p in portfolio.products
            if p.annual_return is not None and p.annual_return >= Decimal("10")
        ]

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "annual_return": f"{p.annual_return:.2f}%",
                "investment_days": p.investment_days,
            }
            for p in high_return_products
        ]


portfolio_summary_analyzer = PortfolioSummaryAnalyzer()
