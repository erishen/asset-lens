"""
Report metrics calculation functions.
报告指标计算函数 - 提取公共计算逻辑
"""

from decimal import Decimal
from typing import Any

from ..data.models import Portfolio


def calculate_total_return(portfolio: Portfolio) -> Decimal:
    """计算总收益率"""
    if portfolio.total_initial == 0:
        return Decimal("0")
    return (portfolio.total_value - portfolio.total_initial) / portfolio.total_initial * 100


def calculate_average_return(portfolio: Portfolio) -> Decimal:
    """计算平均收益率"""
    if not portfolio.products:
        return Decimal("0")
    total_return = sum(
        float(p.annualized_return_irr or 0) for p in portfolio.products
    )
    return Decimal(str(total_return / len(portfolio.products)))


def calculate_positive_avg_return(portfolio: Portfolio) -> str:
    """计算正收益产品的平均收益率"""
    positive_returns = [
        float(p.annualized_return_irr or 0)
        for p in portfolio.products
        if (p.annualized_return_irr or 0) > 0
    ]

    if not positive_returns:
        return "0.00%"

    avg_return = sum(positive_returns) / len(positive_returns)
    return f"{avg_return:.2f}%"


def calculate_weighted_return(portfolio: Portfolio) -> Decimal:
    """计算加权收益率"""
    if portfolio.total_initial == 0:
        return Decimal("0")

    weighted_sum = Decimal("0")
    for product in portfolio.products:
        if product.initial_amount and product.annualized_return_irr:
            weight = product.initial_amount / portfolio.total_initial
            weighted_sum += weight * product.annualized_return_irr

    return weighted_sum


def calculate_investment_efficiency(portfolio: Portfolio) -> dict[str, Any]:
    """计算投资效率指标"""
    total_products = len(portfolio.products)
    if total_products == 0:
        return {
            "efficiency_score": 0,
            "profit_rate": 0,
            "avg_holding_days": 0,
        }

    profit_products = sum(
        1 for p in portfolio.products
        if (p.annualized_return_irr or 0) > 0
    )
    total_holding_days = sum(
        p.investment_days or 0 for p in portfolio.products
    )

    return {
        "efficiency_score": (profit_products / total_products * 100) if total_products > 0 else 0,
        "profit_rate": f"{profit_products}/{total_products}",
        "avg_holding_days": total_holding_days / total_products if total_products > 0 else 0,
    }


def get_return_distribution(portfolio: Portfolio) -> dict[str, int]:
    """获取收益率分布"""
    distribution = {
        "high_return": 0,      # > 10%
        "medium_return": 0,    # 0% - 10%
        "low_return": 0,       # -10% - 0%
        "loss": 0,             # < -10%
    }

    for product in portfolio.products:
        return_rate = float(product.annualized_return_irr or 0)
        if return_rate > 10:
            distribution["high_return"] += 1
        elif return_rate > 0:
            distribution["medium_return"] += 1
        elif return_rate > -10:
            distribution["low_return"] += 1
        else:
            distribution["loss"] += 1

    return distribution


def calculate_risk_score(portfolio: Portfolio) -> float:
    """计算风险评分"""
    if not portfolio.products:
        return 0.0

    risk_weights = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    total_score = 0
    for product in portfolio.products:
        risk_level = getattr(product, 'risk_level', 'medium')
        if hasattr(risk_level, 'value'):
            risk_level = risk_level.value
        total_score += risk_weights.get(str(risk_level).lower(), 2)

    return total_score / len(portfolio.products)


def get_type_distribution(portfolio: Portfolio) -> dict[str, Any]:
    """获取投资类型分布"""
    distribution: dict[str, dict[str, Any]] = {}

    for product in portfolio.products:
        ptype = product.investment_type
        if hasattr(ptype, 'value'):
            ptype = getattr(ptype, 'value', ptype)
        type_name = str(ptype) if ptype else "其他"

        if type_name not in distribution:
            distribution[type_name] = {
                "count": 0,
                "total_value": Decimal("0"),
                "total_initial": Decimal("0"),
            }

        distribution[type_name]["count"] += 1
        distribution[type_name]["total_value"] += product.current_amount or Decimal("0")
        distribution[type_name]["total_initial"] += product.initial_amount or Decimal("0")

    return {
        name: {
            "count": data["count"],
            "total_value": str(data["total_value"]),
            "total_initial": str(data["total_initial"]),
            "percentage": f"{data['count'] / len(portfolio.products) * 100:.1f}%",
        }
        for name, data in distribution.items()
    }


def get_risk_distribution(portfolio: Portfolio) -> dict[str, Any]:
    """获取风险等级分布"""
    distribution: dict[str, int] = {}

    for product in portfolio.products:
        risk_level = getattr(product, 'risk_level', 'medium')
        if hasattr(risk_level, 'value'):
            risk_level = risk_level.value
        risk_name = str(risk_level) if risk_level else "中"

        distribution[risk_name] = distribution.get(risk_name, 0) + 1

    return {
        name: {
            "count": count,
            "percentage": f"{count / len(portfolio.products) * 100:.1f}%",
        }
        for name, count in distribution.items()
    }
