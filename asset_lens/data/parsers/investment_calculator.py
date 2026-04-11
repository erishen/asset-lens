"""
Investment Calculator - 投资产品计算模块

从 csv_parser.py 中提取的计算逻辑，包括:
- IRR 计算
- DCA 产品识别和解析
- 现金流计算
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ...core.dca_parser import DCAParser
from ...core.irr_calculator import IRRCalculator
from ..models import InvestmentProduct


def days360(start_date: date, end_date: date, european: bool = False) -> int:
    """
    计算360天日历法的天数（金融计算方法）
    Args:
        start_date: 开始日期
        end_date: 结束日期
        european: 是否使用欧洲方法（31日改为30日）
    Returns:
        天数
    """
    start_year = start_date.year
    start_month = start_date.month
    start_day = start_date.day

    end_year = end_date.year
    end_month = end_date.month
    end_day = end_date.day

    if european:
        if start_day == 31:
            start_day = 30
        if end_day == 31:
            end_day = 30
    else:
        if start_day == 31:
            start_day = 30
        if end_day == 31 and start_day == 30:
            end_day = 30

    return (end_year - start_year) * 360 + (end_month - start_month) * 30 + (end_day - start_day)


class InvestmentCalculator:
    """投资产品计算器"""

    @staticmethod
    def is_dca_product(product: InvestmentProduct) -> bool:
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

    @staticmethod
    def parse_dca_transactions(
        records_str: str,
        investment_type,
        reference_date: datetime | None = None,
        product_name: str | None = None,
    ) -> list[dict]:
        """解析定投交易记录"""
        dca_parser = DCAParser()
        transactions = dca_parser.parse_transaction_record(
            records_str,
            reference_date=reference_date or datetime.now(),
            investment_type=investment_type,
            product_name=product_name,
        )

        result = []
        for t in transactions:
            result.append(
                {
                    "date": t.transaction_date.strftime("%Y/%m/%d"),
                    "type": t.action,
                    "amount": float(t.amount),
                }
            )

        return result

    @staticmethod
    def calculate_cashflows_with_days(
        transactions: list[dict], start_date, current_amount, total_days: int
    ) -> list[dict]:
        """
        计算现金流（使用 days360 计算天数，与 ts-demo 一致）
        Args:
            transactions: 交易记录列表
            start_date: 开始日期
            current_amount: 当前金额
            total_days: 总投资天数
        Returns:
            现金流列表，格式为 [{"amount": float, "days": int}, ...]
        """
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
                continue

            trans_days = days360(start_date, trans_date)

            if trans["type"] == "buy":
                cashflows.append({"amount": -trans["amount"], "days": trans_days})
            elif trans["type"] == "sell":
                cashflows.append({"amount": trans["amount"], "days": trans_days})

        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows

    @staticmethod
    def calculate_cashflows_with_days_for_dca(
        transactions: list[dict],
        start_date: date,
        current_amount: Decimal,
        total_days: int,
        initial_amount: Decimal,
    ) -> list[dict]:
        """
        计算定投产品的现金流（使用初始金额作为净投入）
        """
        cashflows: list[dict] = []

        if not start_date:
            return cashflows

        cashflows.append({"amount": -float(initial_amount), "days": 0})

        if current_amount:
            cashflows.append({"amount": float(current_amount), "days": total_days})

        return cashflows

    @staticmethod
    def parse_transaction_records(records_str: str) -> list[dict]:
        """
        解析交易记录字符串
        Args:
            records_str: 交易记录字符串，格式如 "2025/8/8:buy:15703; 2025/9/18:sell:11581"
        Returns:
            交易记录列表
        """
        transactions: list[dict[str, Any]] = []
        if not records_str:
            return transactions

        for record in records_str.replace("；", ";").split(";"):
            record = record.strip()
            if not record:
                continue

            parts = record.split(":")
            if len(parts) >= 3:
                try:
                    date_str = parts[0]
                    trans_type = parts[1]
                    amount = float(parts[2])
                    transactions.append({"date": date_str, "type": trans_type, "amount": amount})
                except (ValueError, IndexError):
                    continue

        return transactions

    @staticmethod
    def calculate_cashflows(transactions: list[dict], current_amount: Decimal) -> list[float]:
        """
        计算现金流
        """
        cashflows = []

        for trans in transactions:
            if trans["type"] == "buy":
                cashflows.append(-trans["amount"])
            elif trans["type"] == "sell":
                cashflows.append(trans["amount"])

        if current_amount:
            cashflows.append(float(current_amount))

        return cashflows

    @classmethod
    def calculate_product_returns(
        cls,
        product: InvestmentProduct,
        reference_date: datetime | None = None,
    ) -> InvestmentProduct:
        """
        计算单个产品的收益率
        Args:
            product: 投资产品
            reference_date: 参考日期
        Returns:
            更新后的投资产品
        """
        irr_calculator = IRRCalculator()
        transactions = []

        if product.transaction_records:
            is_dca = cls.is_dca_product(product)
            if is_dca:
                transactions = cls.parse_dca_transactions(
                    product.transaction_records,
                    product.investment_type,
                    reference_date,
                    product.name,
                )
            else:
                transactions = cls.parse_transaction_records(product.transaction_records)

        total_buy = sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0
        total_sell = sum(t["amount"] for t in transactions if t["type"] == "sell") if transactions else 0

        is_dca_product = cls.is_dca_product(product)
        if is_dca_product and product.initial_amount and product.initial_amount > 0:
            net_invest = total_buy - total_sell
            if net_invest > 0 and abs(net_invest - float(product.initial_amount)) > 1:
                pass

            current_value = float(product.current_amount or 0)
            initial_value = float(product.initial_amount)
            simple_return = (current_value - initial_value) / initial_value
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))
        elif total_buy > 0:
            current_value = float(product.current_amount or 0)
            net_gain = current_value + total_sell - total_buy
            simple_return = net_gain / total_buy
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))
        elif product.initial_amount and product.initial_amount > 0:
            current_value = float(product.current_amount or 0)
            initial_value = float(product.initial_amount)
            simple_return = (current_value - initial_value) / initial_value
            product.return_rate = Decimal(str(round(simple_return * 100, 2)))

        total_days = product.investment_days or 0
        if total_days > 0:
            is_bond_product = (
                product.investment_type.value and "债" in product.investment_type.value
            ) or (product.name and "分红" in product.name)

            if is_bond_product:
                if product.initial_amount and product.initial_amount > 0:
                    current_value = float(product.current_amount or 0)
                    interest = float(product.interest_payment or 0)
                    initial_value = float(product.initial_amount)
                    net_gain = current_value + interest - initial_value
                    simple_return = net_gain / initial_value
                    product.return_rate = Decimal(str(round(simple_return * 100, 2)))
                    simple_annualized = (1 + simple_return) ** (360 / total_days) - 1
                    product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
            elif is_dca_product and product.initial_amount and product.initial_amount > 0:
                if product.start_date and product.current_amount:
                    cashflows = cls.calculate_cashflows_with_days_for_dca(
                        transactions,
                        product.start_date,
                        product.current_amount,
                        total_days,
                        product.initial_amount,
                    )

                    if len(cashflows) >= 2:
                        irr = irr_calculator.calculate_irr_with_days(cashflows)
                        if irr is not None:
                            product.annual_return = Decimal(str(round(irr * 100, 2)))

                    if product.return_rate is not None:
                        simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
            else:
                if product.return_rate is not None and total_days > 0:
                    simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                    product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

        return product


investment_calculator = InvestmentCalculator()
