import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..core.exceptions import DataLoadError, DataParseError
from ..data.models import InvestmentProduct, InvestmentType
from .parsers.investment_calculator import days360

logger = logging.getLogger(__name__)


class CSVIrrMixin:
    @classmethod
    def _calculate_irr_for_products(
        cls,
        products: list[InvestmentProduct],
        reference_date: datetime | None = None,
        usd_rate: float = 7.1242,
        hkd_rate: float = 0.9157,
    ) -> list[InvestmentProduct]:
        from ..core.dca_parser import DCAParser
        from ..core.irr_calculator import IRRCalculator

        irr_calculator = IRRCalculator()
        DCAParser()

        for product in products:
            inv_type_value = product.investment_type.value if product.investment_type else ""
            is_usd_investment = "美元" in inv_type_value
            is_hkd_investment = "港元" in inv_type_value

            product_usd_rate = float(product.usd_rate) if product.usd_rate else usd_rate
            product_hkd_rate = float(product.hkd_rate) if product.hkd_rate else hkd_rate

            transactions = []
            if product.transaction_records:
                is_dca = cls._is_dca_product(product)
                if is_dca:
                    transactions = cls._parse_dca_transactions(
                        product.transaction_records,
                        product.investment_type,
                        reference_date,
                        product.name,
                    )
                else:
                    transactions = cls._parse_transaction_records(product.transaction_records)

            if is_usd_investment or is_hkd_investment:
                rate = product_usd_rate if is_usd_investment else product_hkd_rate
                transactions = [
                    {"date": t["date"], "type": t["type"], "amount": round(t["amount"] * rate)} for t in transactions
                ]

            total_buy = sum(t["amount"] for t in transactions if t["type"] == "buy") if transactions else 0
            total_sell = sum(t["amount"] for t in transactions if t["type"] == "sell") if transactions else 0

            is_dca_product = cls._is_dca_product(product)

            current_amount_cny = float(product.current_amount or 0)
            initial_amount_cny = float(product.initial_amount or 0)
            profit_amount_cny = float(product.profit_amount or 0)
            interest_payment_cny = float(product.interest_payment or 0)

            if is_usd_investment:
                rate = product_usd_rate
                current_amount_cny = round(current_amount_cny * rate)
                initial_amount_cny = round(initial_amount_cny * rate)
                profit_amount_cny = round(profit_amount_cny * rate)
                interest_payment_cny = round(interest_payment_cny * rate)
            elif is_hkd_investment:
                rate = product_hkd_rate
                current_amount_cny = round(current_amount_cny * rate)
                initial_amount_cny = round(initial_amount_cny * rate)
                profit_amount_cny = round(profit_amount_cny * rate)
                interest_payment_cny = round(interest_payment_cny * rate)

            if initial_amount_cny > 0 and total_buy > 0:
                net_invest = total_buy - total_sell
                if abs(net_invest - initial_amount_cny) > 1:
                    diff = net_invest - initial_amount_cny
                    diff_days = abs(diff) / 100 if abs(diff) >= 100 else abs(diff) / 50
                    logger.debug(
                        f"产品数据不一致: {product.name}",
                        extra={
                            "product_name": product.name,
                            "csv_amount": float(product.initial_amount or 0),
                            "transaction_amount": net_invest,
                            "difference": diff,
                            "diff_days": diff_days,
                        },
                    )

            if total_buy > 0:
                current_value = current_amount_cny
                if profit_amount_cny != 0 and initial_amount_cny > 0:
                    simple_return = profit_amount_cny / initial_amount_cny
                else:
                    net_gain = current_value + total_sell - total_buy
                    simple_return = net_gain / total_buy
                product.return_rate = Decimal(str(round(simple_return * 100, 2)))
            elif initial_amount_cny > 0:
                initial_value = initial_amount_cny
                if profit_amount_cny != 0:
                    simple_return = profit_amount_cny / initial_value
                else:
                    current_value = current_amount_cny
                    simple_return = (current_value - initial_value) / initial_value
                product.return_rate = Decimal(str(round(simple_return * 100, 2)))

            total_days = product.investment_days or 0
            if total_days > 0:
                is_bond_product = (product.investment_type.value and "债" in product.investment_type.value) or (
                    product.name and "分红" in product.name
                )

                if is_bond_product:
                    if initial_amount_cny > 0:
                        current_value = current_amount_cny
                        interest = interest_payment_cny
                        initial_value = initial_amount_cny
                        net_gain = current_value + interest - initial_value
                        simple_return = net_gain / initial_value
                        product.return_rate = Decimal(str(round(simple_return * 100, 2)))
                        simple_annualized = (1 + simple_return) ** (360 / total_days) - 1
                        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif is_dca_product and initial_amount_cny > 0:
                    if product.start_date and current_amount_cny > 0:
                        cashflows = cls._calculate_cashflows_with_days_for_dca(
                            transactions,
                            product.start_date,
                            Decimal(str(current_amount_cny)),
                            total_days,
                            Decimal(str(initial_amount_cny)),
                            Decimal(str(interest_payment_cny)) if interest_payment_cny else None,
                        )
                    else:
                        cashflows = []

                    if cashflows and len(cashflows) > 1:
                        irr = irr_calculator.calculate_irr_with_days(cashflows)
                        if irr is not None and -1 < irr < 10:
                            product.annual_return = Decimal(str(round(irr * 100, 2)))
                        else:
                            if product.return_rate is not None:
                                simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                                product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                    else:
                        if product.return_rate is not None:
                            simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                            product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif total_days < 180:
                    if product.return_rate is not None:
                        simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif transactions and len(transactions) > 1 and total_buy > 0:
                    cashflows = cls._calculate_cashflows_with_days(
                        transactions,
                        product.start_date,
                        Decimal(str(current_amount_cny)),
                        total_days,
                        Decimal(str(interest_payment_cny)) if interest_payment_cny else None,
                    )

                    if cashflows and len(cashflows) > 1:
                        irr = irr_calculator.calculate_irr_with_days(cashflows)
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
                        else:
                            if product.return_rate is not None:
                                simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                                product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))
                elif product.return_rate is not None:
                    simple_annualized = (1 + float(product.return_rate) / 100) ** (360 / total_days) - 1
                    product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

                if total_buy > 0:
                    total_value = total_sell + current_amount_cny + interest_payment_cny
                    actual_return = (total_value - total_buy) / total_buy
                    product.return_rate = Decimal(str(round(actual_return * 100, 2)))

        return products

    @classmethod
    def _is_dca_product(cls, product: InvestmentProduct) -> bool:
        if product.investment_type and product.investment_type.value == "定投基金":
            return True
        if product.transaction_records:
            records = product.transaction_records.strip()
            if "-now:" in records or "-" in records.split(":")[0] if ":" in records else False:
                buy_count = records.count(":buy:")
                sell_count = records.count(":sell:")
                return buy_count >= 1 and sell_count == 0
        return False

    @classmethod
    def _parse_dca_transactions(
        cls,
        records_str: str,
        investment_type: InvestmentType | None,
        reference_date: datetime | None = None,
        product_name: str | None = None,
    ) -> list[dict]:
        from datetime import datetime

        from ..core.dca_parser import DCAParser

        dca_parser = DCAParser()
        transactions = dca_parser.parse_transaction_record(
            records_str,
            reference_date=reference_date or datetime.now(),
            investment_type=investment_type,
            product_name=product_name,
        )

        result = [
            {
                "date": t.transaction_date.strftime("%Y/%m/%d"),
                "type": t.action,
                "amount": float(t.amount),
            }
            for t in transactions
        ]

        return result

    @classmethod
    def _calculate_cashflows_with_days(
        cls, transactions: list[dict], start_date: date | None, current_amount: Decimal, total_days: int, interest_payment: Decimal | None = None
    ) -> list[dict]:
        from datetime import date

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

        final_amount = float(current_amount or 0)
        if interest_payment:
            final_amount += float(interest_payment)
        if final_amount:
            cashflows.append({"amount": final_amount, "days": total_days})

        return cashflows

    @classmethod
    def _calculate_cashflows_with_days_for_dca(
        cls,
        transactions: list[dict],
        start_date: date,
        current_amount: Decimal,
        total_days: int,
        initial_amount: Decimal,
        interest_payment: Decimal | None = None,
    ) -> list[dict]:
        cashflows: list[dict] = []

        if not start_date:
            return cashflows

        cashflows.append({"amount": -float(initial_amount), "days": 0})

        final_amount = float(current_amount or 0)
        if interest_payment:
            final_amount += float(interest_payment)
        if final_amount:
            cashflows.append({"amount": final_amount, "days": total_days})

        return cashflows

    @classmethod
    def _parse_transaction_records(cls, records_str: str) -> list[dict]:
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

    @classmethod
    def _calculate_cashflows(cls, transactions: list[dict], current_amount: Decimal) -> list[float]:
        cashflows = []

        for trans in transactions:
            if trans["type"] == "buy":
                cashflows.append(-trans["amount"])
            elif trans["type"] == "sell":
                cashflows.append(trans["amount"])

        if current_amount:
            cashflows.append(float(current_amount))

        return cashflows
