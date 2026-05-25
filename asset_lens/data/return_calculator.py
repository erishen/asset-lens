"""
Return Calculator - 收益率计算器
支持多种投资产品的收益率计算
"""

import logging
from datetime import date, datetime
from decimal import Decimal

from ..core.irr_calculator import IRRCalculator
from ..data.models import InvestmentProduct
from .parsers.investment_calculator import days360

logger = logging.getLogger(__name__)


class ReturnCalculator:
    """收益率计算器"""

    def __init__(self) -> None:
        self.irr_calculator = IRRCalculator()

    def calculate_returns(
        self, product: InvestmentProduct, transactions: list[dict], reference_date: datetime | None = None
    ) -> None:
        """
        计算产品收益率

        Args:
            product: 投资产品
            transactions: 交易记录
            reference_date: 参考日期
        """
        total_days = product.investment_days or 0

        self._calculate_simple_return(product, transactions)

        if total_days > 0:
            self._calculate_annual_return(product, transactions, total_days)

    def _calculate_simple_return(self, product: InvestmentProduct, transactions: list[dict]) -> None:
        """计算简单收益率"""
        total_buy = sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0
        total_sell = sum(t["amount"] for t in transactions if t["type"] == "sell") if transactions else 0

        is_dca_product = self._is_dca_product(product)

        if is_dca_product and product.initial_amount and product.initial_amount > 0:
            self._calculate_dca_simple_return(product, transactions)
        elif total_buy > 0:
            current_value = float(product.current_amount or 0)
            net_gain = current_value + total_sell - total_buy
            simple_return = net_gain / total_buy
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))
        elif product.initial_amount and product.initial_amount > 0:
            initial_value = float(product.initial_amount)
            if product.profit_amount is not None and product.profit_amount != 0:
                simple_return = float(product.profit_amount) / initial_value
            else:
                current_value = float(product.current_amount or 0)
                simple_return = (current_value - initial_value) / initial_value
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))

    def _calculate_dca_simple_return(self, product: InvestmentProduct, transactions: list[dict]) -> None:
        """计算定投产品简单收益率"""
        if not product.initial_amount:
            return

        total_buy = sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0
        total_sell = sum(t["amount"] for t in transactions if t["type"] == "sell") if transactions else 0
        net_invest = total_buy - total_sell
        initial_value = float(product.initial_amount)

        if net_invest > 0 and abs(net_invest - initial_value) > 1:
            diff = net_invest - initial_value
            diff_days = abs(diff) / 100 if abs(diff) >= 100 else abs(diff) / 50
            logger.warning(
                f"定投产品数据不一致: {product.name}",
                extra={
                    "product_name": product.name,
                    "csv_amount": initial_value,
                    "transaction_amount": net_invest,
                    "difference": diff,
                    "diff_days": diff_days,
                },
            )

        current_value = float(product.current_amount or 0)
        if net_invest > 0:
            simple_return = (current_value - net_invest) / net_invest
        else:
            simple_return = (current_value - initial_value) / initial_value if initial_value > 0 else 0
        product.return_rate = Decimal(str(round(simple_return * 100, 2)))

    def _calculate_annual_return(self, product: InvestmentProduct, transactions: list[dict], total_days: int) -> None:
        """计算年化收益率"""
        is_bond = self._is_bond_product(product)
        is_dca = self._is_dca_product(product)

        if is_bond:
            self._calculate_bond_annual_return(product, total_days)
        elif is_dca:
            self._calculate_dca_annual_return(product, transactions, total_days)
        else:
            self._calculate_regular_annual_return(product, transactions, total_days)

    def _calculate_bond_annual_return(self, product: InvestmentProduct, total_days: int) -> None:
        """计算债券类产品年化收益率"""
        if product.initial_amount and product.initial_amount > 0:
            current_value = float(product.current_amount or 0)
            interest = float(product.interest_payment or 0)
            initial_value = float(product.initial_amount)

            net_gain = current_value + interest - initial_value
            simple_return = net_gain / initial_value
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))

            simple_annualized = (1 + simple_return) ** (360 / total_days) - 1
            product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

    def _calculate_dca_annual_return(
        self, product: InvestmentProduct, transactions: list[dict], total_days: int
    ) -> None:
        """计算定投产品年化收益率"""
        if not product.start_date or not product.current_amount:
            self._fallback_simple_annual_return(product, total_days)
            return

        cashflows = self._build_cashflows_for_dca(
            transactions, product.start_date, product.current_amount, total_days, product.initial_amount
        )

        if cashflows and len(cashflows) > 1:
            irr = self.irr_calculator.calculate_irr_with_days(cashflows)
            if irr is not None and -1 < irr < 10:
                product.annual_return = Decimal(str(round(irr * 100, 2)))
                return

        self._fallback_simple_annual_return(product, total_days)

    def _calculate_regular_annual_return(
        self, product: InvestmentProduct, transactions: list[dict], total_days: int
    ) -> None:
        """计算普通产品年化收益率"""
        if total_days < 180:
            self._fallback_simple_annual_return(product, total_days)
            return

        total_buy = sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0

        if transactions and len(transactions) > 1 and total_buy > 0:
            cashflows = self._build_cashflows(transactions, product.start_date, product.current_amount, total_days)

            if cashflows and len(cashflows) > 1:
                irr = self.irr_calculator.calculate_irr_with_days(cashflows)
                if irr is not None and -1 < irr < 10:
                    if product.return_rate is not None:
                        simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                        diff = abs(irr - simple_annualized)
                        if diff > 1:
                            product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                        else:
                            product.annual_return = Decimal(str(round(irr * 100, 2)))
                    else:
                        product.annual_return = Decimal(str(round(irr * 100, 2)))
                    return

        self._fallback_simple_annual_return(product, total_days)

    def _fallback_simple_annual_return(self, product: InvestmentProduct, total_days: int) -> None:
        """降级到简单年化收益率"""
        if product.return_rate is not None:
            simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
            product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

    @staticmethod
    def _is_bond_product(product: InvestmentProduct) -> bool:
        """判断是否为债券类产品"""
        if product.investment_type.value and "债" in product.investment_type.value:
            return True
        return bool(product.name and "分红" in product.name)

    @staticmethod
    def _is_dca_product(product: InvestmentProduct) -> bool:
        """判断是否为定投产品"""
        if product.investment_type and product.investment_type.value == "定投基金":
            return True
        if product.transaction_records:
            records = product.transaction_records.strip()
            if "-now:" in records or "-" in records.split(":")[0] if ":" in records else False:
                buy_count = records.count(":buy:")
                sell_count = records.count(":sell:")
                return buy_count >= 1 and sell_count == 0
        return False

    def _build_cashflows(
        self, transactions: list[dict], start_date: date | None, current_amount: Decimal | None, total_days: int
    ) -> list[dict]:
        """构建现金流"""
        cashflows: list[dict] = []

        if not start_date:
            return cashflows

        for trans in transactions:
            date_str = trans["date"]
            try:
                if "/" in date_str and "-" in date_str:
                    date_parts = date_str.split("-")[0].split("/")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                elif "/" in date_str:
                    date_parts = date_str.split("/")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                elif "-" in date_str and date_str.count("-") == 2:
                    date_parts = date_str.split("-")
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                else:
                    continue
            except (ValueError, IndexError):
                logger.warning(f"日期解析失败: {date_str}", exc_info=True)
                continue

            trans_days = days360(start_date, trans_date)

            if trans["type"] == "buy":
                cashflows.append({"amount": -trans["amount"], "days": trans_days})
            elif trans["type"] == "sell":
                cashflows.append({"amount": trans["amount"], "days": trans_days})

        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows

    def _build_cashflows_for_dca(
        self,
        transactions: list[dict],
        start_date: date | None,
        current_amount: Decimal | None,
        total_days: int,
        initial_amount: Decimal | None,
    ) -> list[dict]:
        """为 DCA 产品构建现金流"""
        cashflows: list[dict] = []

        if not start_date or not initial_amount:
            return cashflows

        cashflows.append({"amount": -float(initial_amount), "days": 0})

        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows
