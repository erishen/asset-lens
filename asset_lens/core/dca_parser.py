"""
DCA (Dollar Cost Average) strategy parser for asset-lens.
定投策略解析和计算模块，支持4种定投模式
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from ..data.models import Currency, InvestmentType, Transaction
from .holidays import (
    calculate_fund_trading_days,
    calculate_working_days,
    get_last_fund_trading_day,
    parse_stop_periods,
)


class DCAInvestmentType(str, Enum):
    """定投类型"""

    FIXED = "fixed"
    RANGE = "range"
    FLOAT = "float"
    VALUATION = "valuation"


class DCAParser:
    """定投策略解析器"""

    @staticmethod
    def parse_investment_type(
        amount_str: str,
    ) -> tuple[DCAInvestmentType, Decimal, Decimal | None]:
        amount_str = amount_str.strip()

        if "--" not in amount_str and amount_str.count("-") == 2:
            parts = amount_str.split("-")
            if len(parts) == 3:
                try:
                    low = Decimal(parts[0].strip())
                    normal = Decimal(parts[1].strip())
                    high = Decimal(parts[2].strip())
                    return DCAInvestmentType.VALUATION, normal, high
                except Exception:
                    pass

        if "~" in amount_str:
            parts = amount_str.split("~")
            if len(parts) == 2:
                try:
                    low = Decimal(parts[0].strip())
                    high = Decimal(parts[1].strip())
                    if low > 0 and high > low and high <= 365 and low <= 100:
                        return DCAInvestmentType.RANGE, Decimal("0"), high
                    avg = (low + high) / Decimal("2")
                    return DCAInvestmentType.RANGE, avg, high
                except Exception:
                    pass

        if "±" in amount_str or "+/-" in amount_str:
            parts = amount_str.replace("+/-", "±").split("±")
            if len(parts) == 2:
                try:
                    base = Decimal(parts[0].strip())
                    delta = Decimal(parts[1].strip())
                    return DCAInvestmentType.FLOAT, base, base + delta
                except Exception:
                    pass

        try:
            amount = Decimal(amount_str)
            return DCAInvestmentType.FIXED, amount, amount
        except Exception:
            return DCAInvestmentType.FIXED, Decimal("0"), Decimal("0")

    @staticmethod
    def parse_date_range(
        date_range_str: str,
        reference_date: datetime | None = None,
    ) -> tuple[datetime | None, datetime | None]:
        if "-" not in date_range_str:
            return None, None

        parts = date_range_str.split("-")
        if len(parts) < 2:
            return None, None

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        start_date = DCAParser.parse_date(start_str)
        if start_date is None:
            return None, None

        if end_str.lower() == "now":
            if reference_date:
                last_trading_day = get_last_fund_trading_day(reference_date.date())
                end_date = datetime.combine(last_trading_day, datetime.min.time())
            else:
                last_trading_day = get_last_fund_trading_day(date.today())
                end_date = datetime.combine(last_trading_day, datetime.min.time())
        else:
            parsed_date = DCAParser.parse_date(end_str)
            if parsed_date is None:
                raise ValueError(f"无法解析日期: {end_str}")
            end_date = parsed_date

        return start_date, end_date

    @staticmethod
    def parse_date(date_str: str) -> datetime | None:
        date_formats = [
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    @classmethod
    def parse_transaction_record(
        cls,
        record_str: str,
        reference_date: datetime | None = None,
        currency: Currency = Currency.CNY,
        investment_type: InvestmentType | None = None,
        product_name: str | None = None,
    ) -> list[Transaction]:
        transactions: list[Transaction] = []

        if not record_str or not record_str.strip():
            return transactions

        stop_periods = parse_stop_periods(record_str)

        record_parts = record_str.replace("；", ";").split(";")

        for part in record_parts:
            part = part.strip()
            if not part:
                continue

            if ":stop" in part:
                continue

            if ":" not in part:
                continue

            parts = part.split(":")
            if len(parts) < 3:
                continue

            date_range_str = parts[0].strip()
            action = parts[1].strip()
            amount_str = ":".join(parts[2:]).strip()

            is_dca = "-" in date_range_str and not cls._is_single_date_transaction(date_range_str)

            if not is_dca:
                single_date = cls.parse_date(date_range_str)
                if single_date:
                    try:
                        amount = Decimal(amount_str)
                        transaction = Transaction(
                            transaction_date=single_date.date(),
                            action=action,
                            amount=amount,
                            currency=currency,
                        )
                        transactions.append(transaction)
                    except Exception:
                        pass
                continue

            start_date, end_date = cls.parse_date_range(date_range_str, reference_date)
            if start_date is None or end_date is None:
                continue

            if start_date > end_date:
                continue

            dca_type, base_amount, max_amount = cls.parse_investment_type(amount_str)

            is_qdii = False
            if product_name and "QDII" in product_name:
                is_qdii = True
            elif investment_type:
                if hasattr(investment_type, "value") and investment_type.value:
                    is_qdii = "QDII" in investment_type.value
                elif hasattr(investment_type, "name"):
                    is_qdii = "QDII" in investment_type.name
                else:
                    is_qdii = investment_type == InvestmentType.QDII

            dca_transactions = cls.generate_dca_transactions(
                start_date=start_date,
                end_date=end_date,
                action=action,
                amount=base_amount,
                currency=currency,
                investment_type=dca_type,
                stop_periods=stop_periods,
                is_qdii=is_qdii,
            )

            transactions.extend(dca_transactions)

        return transactions

    @staticmethod
    def _is_single_date_transaction(date_range_str: str) -> bool:
        """判断是否为单日交易（非定投）"""
        if "-" not in date_range_str:
            return True

        parts = date_range_str.split("-")
        if len(parts) != 2:
            return False

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        if end_str.lower() == "now":
            return False

        return start_str == end_str

    @classmethod
    def generate_dca_transactions(
        cls,
        start_date: datetime,
        end_date: datetime,
        action: str,
        amount: Decimal,
        currency: Currency,
        investment_type: DCAInvestmentType = DCAInvestmentType.FIXED,
        stop_periods: list[tuple[date, date]] | None = None,
        is_qdii: bool = False,
    ) -> list[Transaction]:
        transactions: list[Transaction] = []

        start = start_date.date()
        end = end_date.date()

        if start > end:
            return transactions

        if is_qdii:
            trading_days = calculate_fund_trading_days(start, end, stop_periods)
        else:
            trading_days = calculate_working_days(start, end, stop_periods)

        if trading_days <= 0:
            return transactions

        total_amount = amount * Decimal(trading_days)

        transaction = Transaction(
            transaction_date=start,
            action=action,
            amount=total_amount,
            currency=currency,
        )
        transactions.append(transaction)

        return transactions

    @staticmethod
    def calculate_total_investment(transactions: list[Transaction], action: str = "buy") -> Decimal:
        total = Decimal("0")
        for t in transactions:
            if t.action.lower() == action.lower():
                total += t.amount
        return total

    @staticmethod
    def calculate_net_investment(transactions: list[Transaction]) -> Decimal:
        buy_total = DCAParser.calculate_total_investment(transactions, "buy")
        sell_total = DCAParser.calculate_total_investment(transactions, "sell")
        return buy_total - sell_total


dca_parser = DCAParser()
