"""全产品收益估算模块"""
from decimal import Decimal

from asset_lens.data.models import InvestmentProduct


class DailyEstimateResult:
    """估算结果"""

    def __init__(
        self,
        product_name: str,
        product_type: str,
        current_value: Decimal,
        estimated_daily_return: Decimal,
        estimated_daily_return_rate: Decimal,
        expected_annual_return: Decimal,
        market_sensitivity: Decimal,
        risk_level: str | None = None,
    ):
        self.product_name = product_name
        self.product_type = product_type
        self.current_value = current_value
        self.estimated_daily_return = estimated_daily_return
        self.estimated_daily_return_rate = estimated_daily_return_rate
        self.expected_annual_return = expected_annual_return
        self.market_sensitivity = market_sensitivity
        self.risk_level = risk_level

    def to_dict(self):
        return {
            "product_name": self.product_name,
            "product_type": self.product_type,
            "current_value": float(self.current_value),
            "estimated_daily_return": float(self.estimated_daily_return),
            "estimated_daily_return_rate": float(self.estimated_daily_return_rate),
            "expected_annual_return": float(self.expected_annual_return),
            "market_sensitivity": float(self.market_sensitivity),
            "risk_level": self.risk_level,
        }


def get_expected_annual_return(product_type: str) -> Decimal:
    """获取产品的预期年化收益率"""
    type_lower = product_type.lower()

    if "债券" in product_type or "债" in product_type or "bond" in type_lower:
        return Decimal("0.02")
    elif "黄金" in product_type or "gold" in type_lower:
        return Decimal("0.05")
    elif "货币" in product_type or "currency" in type_lower:
        return Decimal("0.005")
    elif "高端理财" in product_type:
        return Decimal("0.03")
    elif "理财" in product_type or "financial" in type_lower:
        return Decimal("0.02")
    elif "美股" in product_type or "qdii" in type_lower or "us_equity" in type_lower:
        return Decimal("0.05")
    elif "基金" in product_type or "fund" in type_lower:
        return Decimal("0.04")
    elif "股息" in product_type or "dividend" in product_type:
        return Decimal("0.03")
    else:
        return Decimal("0.02")


def get_market_sensitivity(product_type: str) -> Decimal:
    """获取产品与股市的关联度（敏感度系数）"""
    type_lower = product_type.lower()

    if "债券" in product_type or "债" in product_type or "bond" in type_lower:
        return Decimal("-0.3")
    elif "黄金" in product_type or "gold" in type_lower:
        return Decimal("0.5")
    elif "货币" in product_type or "currency" in type_lower:
        return Decimal("0.1")
    elif "高端理财" in product_type:
        return Decimal("0.5")
    elif "理财" in product_type or "financial" in type_lower:
        return Decimal("0.2")
    elif "美股" in product_type or "qdii" in type_lower or "us_equity" in type_lower:
        return Decimal("0.9")
    elif "基金" in product_type or "fund" in type_lower:
        return Decimal("0.8")
    elif "股息" in product_type or "dividend" in product_type:
        return Decimal("0.6")
    else:
        return Decimal("0.3")


def get_adjusted_market_sensitivity(
    product_type: str, product_name: str, risk_level: str | None = None
) -> Decimal:
    """根据产品类型和风险等级获取调整后的市场敏感度"""
    sensitivity = get_market_sensitivity(product_type)

    if "货币" in product_type or "currency" in product_type.lower():
        return Decimal("0")

    if risk_level:
        if "低风险" in risk_level or "稳健" in risk_level or "保守" in risk_level:
            return sensitivity * Decimal("0.1")
        elif "中低风险" in risk_level or "中低" in risk_level:
            return sensitivity * Decimal("0.3")
        elif "中风险" in risk_level or "平衡" in risk_level:
            return sensitivity * Decimal("0.6")
        elif "中高风险" in risk_level or "中高" in risk_level:
            return sensitivity * Decimal("0.8")
        elif "高风险" in risk_level or "进取" in risk_level:
            return sensitivity

    return sensitivity * Decimal("0.5")


def estimate_product_return(
    product: InvestmentProduct, market_change: Decimal = Decimal("0"), is_weekly: bool = False
) -> DailyEstimateResult | None:
    """估算单个产品的收益"""
    if not product.current_amount or product.current_amount <= 0:
        return None

    product_type = product.investment_type.value if product.investment_type else "未知"
    product_name = product.name
    risk_level = product.risk_level.value if product.risk_level else None

    expected_annual_return = get_expected_annual_return(product_type)
    market_sensitivity = get_adjusted_market_sensitivity(product_type, product_name, risk_level)

    trading_days = 50 if is_weekly else 250
    expected_daily_return_rate = expected_annual_return / Decimal(str(trading_days))

    market_impact = market_change * market_sensitivity
    total_daily_return_rate = expected_daily_return_rate + market_impact

    estimated_daily_return = product.current_amount * total_daily_return_rate

    return DailyEstimateResult(
        product_name=product_name,
        product_type=product_type,
        current_value=product.current_amount,
        estimated_daily_return=estimated_daily_return,
        estimated_daily_return_rate=total_daily_return_rate,
        expected_annual_return=expected_annual_return,
        market_sensitivity=market_sensitivity,
        risk_level=risk_level,
    )


def estimate_all_products(
    products: list[InvestmentProduct],
    market_change: Decimal = Decimal("0"),
    is_weekly: bool = False,
) -> list[DailyEstimateResult]:
    """估算所有产品的收益"""
    results = []
    for product in products:
        result = estimate_product_return(product, market_change, is_weekly)
        if result:
            results.append(result)
    return results
