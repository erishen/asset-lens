"""
DCA (Dollar Cost Averaging) calculator for asset-lens.
定投计算模块 - 处理定投产品的收益计算
"""

from datetime import datetime
from decimal import Decimal
from typing import Any


class DCACalculator:
    """定投计算器"""

    @staticmethod
    def calculate_annual_return(
        total_investment: Decimal,
        current_amount: Decimal,
        total_days: int,
    ) -> Decimal | None:
        """计算年化收益率"""
        if total_investment <= 0 or total_days <= 0:
            return None

        if current_amount <= 0:
            return Decimal("-100")

        total_return = float(current_amount / total_investment - 1)
        annualized = (1 + total_return) ** (360 / total_days) - 1

        return Decimal(str(round(annualized * 100, 2)))

    @staticmethod
    def calculate_cashflows(
        transactions: list[dict],
        start_date: datetime,
        current_amount: Decimal,
        total_days: int,
    ) -> list[dict]:
        """计算现金流"""
        cashflows = []

        for t in transactions:
            t_date = datetime.strptime(t["date"], "%Y/%m/%d")
            days = (t_date - start_date).days
            cashflows.append(
                {
                    "days": days,
                    "amount": float(t["amount"]),
                }
            )

        cashflows.append(
            {
                "days": total_days,
                "amount": -float(current_amount),
            }
        )

        return cashflows

    @staticmethod
    def calculate_xirr(cashflows: list[dict]) -> Decimal | None:
        """计算 XIRR"""
        try:
            from scipy.optimize import newton

            def xirr_func(rate: float) -> float:
                total = 0.0
                for cf in cashflows:
                    days = cf["days"]
                    amount = cf["amount"]
                    total += amount / ((1 + rate) ** (days / 365))
                return total

            rate = newton(xirr_func, 0.1)
            return Decimal(str(round(rate * 100, 2)))
        except Exception:
            return None

    @staticmethod
    def is_dca_product(product: Any) -> bool:
        """判断是否为定投产品"""
        if hasattr(product, "investment_type") and product.investment_type and product.investment_type.value == "定投基金":
            return True

        if hasattr(product, "transaction_records") and product.transaction_records:
            records = product.transaction_records.strip()
            if "-now:" in records:
                buy_count: int = records.count(":buy:")
                sell_count: int = records.count(":sell:")
                return buy_count >= 1 and sell_count == 0

        return False
