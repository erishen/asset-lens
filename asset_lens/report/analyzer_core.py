"""
Portfolio Analyzer Core - 投资组合核心分析功能
"""

from typing import Any


class PortfolioCore:
    """投资组合核心分析器"""

    def __init__(self):
        pass

    def get_summary(self, products: list[Any]) -> dict[str, Any]:
        """获取投资组合摘要"""
        total_value = sum(float(p.current_amount or 0) for p in products)
        total_initial = sum(float(p.initial_amount or 0) for p in products)
        total_profit = total_value - total_initial

        return_rate = (total_profit / total_initial * 100) if total_initial > 0 else 0

        return {
            "total_value": total_value,
            "total_initial": total_initial,
            "total_profit": total_profit,
            "return_rate": f"{return_rate:.2f}%",
            "position_count": len(products),
            "positive_count": sum(1 for p in products if p.profit_amount and p.profit_amount > 0),
            "negative_count": sum(1 for p in products if p.profit_amount and p.profit_amount < 0),
        }

    def get_risk_summary(self, products: list[Any]) -> dict[str, Any]:
        """获取风险摘要"""
        risk_levels: dict[str, int] = {}
        for p in products:
            risk = p.risk_level.value if p.risk_level else "unknown"
            risk_levels[risk] = risk_levels.get(risk, 0) + 1

        return {
            "risk_distribution": dict(sorted(risk_levels.items(), key=lambda x: x[1], reverse=True)),
        }

    def get_type_distribution(self, products: list[Any]) -> dict[str, Any]:
        """获取类型分布"""
        type_dist: dict[str, int] = {}
        for p in products:
            type_name = p.investment_type.value
            type_dist[type_name] = type_dist.get(type_name, 0) + 1

        return {
            "type_distribution": dict(sorted(type_dist.items(), key=lambda x: x[1], reverse=True)),
        }

    def get_top_performers(self, products: list[Any], top_n: int = 5) -> list[dict[str, Any]]:
        """获取表现最佳的产品"""
        sorted_products = sorted(
            products,
            key=lambda p: float(p.annual_return or 0) if p.annual_return else 0,
            reverse=True,
        )
        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "return_rate": f"{p.annual_return:.2f}%" if p.annual_return else "N/A",
                "current_amount": float(p.current_amount or 0),
            }
            for p in sorted_products[:top_n]
        ]

    def get_bottom_performers(self, products: list[Any], bottom_n: int = 5) -> list[dict[str, Any]]:
        """获取表现最差的产品"""
        sorted_products = sorted(
            products,
            key=lambda p: float(p.annual_return or 0) if p.annual_return else 0,
        )
        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "return_rate": f"{p.annual_return:.2f}%" if p.annual_return else "N/A",
                "current_amount": float(p.current_amount or 0),
            }
            for p in sorted_products[:bottom_n]
        ]
