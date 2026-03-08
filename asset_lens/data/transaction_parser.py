"""
交易记录解析模块
支持多种交易记录格式：单日交易、定投期间、智能定投等
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Tuple

from ..core.holidays import (
    calculate_fund_trading_days,
    calculate_working_days,
    get_last_fund_trading_day,
    is_fund_trading_day,
)


class InvestmentType(Enum):
    """定投类型"""

    FIXED = "fixed"
    SMART = "smart"
    FLOATING = "floating"
    VALUATION = "valuation"


@dataclass
class Transaction:
    """交易记录"""

    date: date
    action: str
    amount: Decimal
    is_period_investment: bool = False
    work_days: int = 0
    daily_amount: Decimal = Decimal("0")
    investment_type: InvestmentType = InvestmentType.FIXED
    original_record: str = ""


@dataclass
class ParsedTransactions:
    """解析后的交易记录集合"""

    transactions: List[Transaction]
    total_buy: Decimal
    total_sell: Decimal
    net_invest: Decimal
    buy_count: int
    sell_count: int


def parse_date(date_str: str, suffix: int) -> date:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串，如 "2025/9/17" 或 "now"
        suffix: 数据目录后缀，如 20260307

    Returns:
        解析后的日期
    """
    date_str = date_str.strip()

    if date_str.lower() == "now":
        y = suffix // 10000
        m = (suffix % 10000) // 100
        d = suffix % 100
        current = date(y, m, d)
        return get_last_fund_trading_day(current)

    parts = date_str.replace("-", "/").split("/")
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))

    raise ValueError(f"无法解析日期: {date_str}")


def parse_stop_periods(transaction_string: str) -> List[Tuple[date, date]]:
    """
    解析暂停期间

    支持格式:
    - 日期范围格式：2025/10/13-2025/10/15:stop
    - 单日格式：2025/10/29:stop
    """
    stop_periods: List[Tuple[date, date]] = []

    for tx in transaction_string.split(";"):
        s = tx.strip()
        if ":stop" not in s:
            continue

        date_range = s.split(":")[0]

        if "-" in date_range:
            parts = date_range.split("-")
            if len(parts) == 2:
                start_str, end_str = parts
                try:
                    start = parse_date(start_str.strip(), 20260307)
                    end = parse_date(end_str.strip(), 20260307)
                    stop_periods.append((start, end))
                except:
                    pass
        else:
            try:
                d = parse_date(date_range.strip(), 20260307)
                stop_periods.append((d, d))
            except:
                pass

    return stop_periods


def parse_period_record(
    period_record: str,
    suffix: int,
    is_qdii: bool = False,
    stop_periods: Optional[List[Tuple[date, date]]] = None,
) -> List[Transaction]:
    """
    解析定投期间记录

    支持格式:
    - 固定金额定投：2025/9/19-now:buy:100
    - 智能定投：2025/9/19-now:buy:50~150
    - 浮动定投：2025/9/19-now:buy:100±20
    - 估值模式定投：2025/9/19-now:buy:100-300-500
    """
    transactions: List[Transaction] = []

    parts = period_record.split(":")
    if len(parts) < 3:
        return transactions

    date_range = parts[0].strip()
    action = parts[1].strip().lower()
    amount_str = parts[2].strip()

    if "-" not in date_range:
        return transactions

    date_parts = date_range.split("-")
    if len(date_parts) != 2:
        return transactions

    start_date_str = date_parts[0].strip()
    end_date_str = date_parts[1].strip()

    try:
        start_date = parse_date(start_date_str, suffix)
        end_date = parse_date(end_date_str, suffix)
    except:
        return transactions

    current_date = date(suffix // 10000, (suffix % 10000) // 100, suffix % 100)
    if start_date > current_date:
        return transactions

    if stop_periods is None:
        stop_periods = []

    if is_qdii:
        work_days = calculate_fund_trading_days(start_date, end_date, stop_periods)
    else:
        work_days = calculate_working_days(start_date, end_date, stop_periods)

    dash_count = amount_str.count("-")

    if dash_count == 2:
        amounts = amount_str.split("-")
        if len(amounts) == 3:
            try:
                normal_valuation = Decimal(amounts[1])
                daily_amount = normal_valuation
                total_amount = normal_valuation * work_days
                investment_type = InvestmentType.VALUATION
            except:
                return transactions
        else:
            return transactions
    elif "~" in amount_str:
        amount_parts = amount_str.split("~")
        if len(amount_parts) == 2:
            try:
                min_amount = Decimal(amount_parts[0])
                max_amount = Decimal(amount_parts[1])
                daily_amount = (min_amount + max_amount) / 2
                total_amount = Decimal("0")
                investment_type = InvestmentType.SMART
            except:
                return transactions
        else:
            return transactions
    elif "±" in amount_str:
        base_str = amount_str.split("±")[0]
        try:
            base_amount = Decimal(base_str)
            daily_amount = base_amount
            total_amount = base_amount * work_days
            investment_type = InvestmentType.FLOATING
        except:
            return transactions
    else:
        try:
            daily_amount = Decimal(amount_str)
            total_amount = daily_amount * work_days
            investment_type = InvestmentType.FIXED
        except:
            return transactions

    transactions.append(
        Transaction(
            date=start_date,
            action=action,
            amount=total_amount,
            is_period_investment=True,
            work_days=work_days,
            daily_amount=daily_amount,
            investment_type=investment_type,
            original_record=period_record,
        )
    )

    return transactions


def parse_transactions(
    transaction_string: str, suffix: int, is_qdii: bool = False
) -> ParsedTransactions:
    """
    解析交易记录字符串

    Args:
        transaction_string: 交易记录字符串
        suffix: 数据目录后缀，如 20260307
        is_qdii: 是否为 QDII 基金

    Returns:
        解析后的交易记录集合
    """
    if not transaction_string or not transaction_string.strip():
        return ParsedTransactions(
            transactions=[],
            total_buy=Decimal("0"),
            total_sell=Decimal("0"),
            net_invest=Decimal("0"),
            buy_count=0,
            sell_count=0,
        )

    cleaned = transaction_string.strip().rstrip(";")
    transactions: List[Transaction] = []

    stop_periods = parse_stop_periods(cleaned)

    for tx in cleaned.split(";"):
        s = tx.strip()
        if not s:
            continue

        if ":stop" in s:
            continue

        if "-" in s and ":buy:" in s:
            period_txs = parse_period_record(s, suffix, is_qdii, stop_periods)
            transactions.extend(period_txs)
            continue

        parts = s.split(":")
        if len(parts) >= 3:
            try:
                tx_date = parse_date(parts[0].strip(), suffix)
                action = parts[1].strip().lower()
                amount = Decimal(parts[2].strip())

                transactions.append(
                    Transaction(
                        date=tx_date,
                        action=action,
                        amount=amount,
                    )
                )
            except:
                pass

    total_buy = sum(tx.amount for tx in transactions if tx.action == "buy")
    total_sell = sum(tx.amount for tx in transactions if tx.action == "sell")
    net_invest = total_buy - total_sell
    buy_count = sum(1 for tx in transactions if tx.action == "buy")
    sell_count = sum(1 for tx in transactions if tx.action == "sell")

    return ParsedTransactions(
        transactions=transactions,
        total_buy=Decimal(str(total_buy)),
        total_sell=Decimal(str(total_sell)),
        net_invest=Decimal(str(net_invest)),
        buy_count=buy_count,
        sell_count=sell_count,
    )


def calculate_net_invest_from_transactions(
    transaction_string: str,
    suffix: int,
    is_qdii: bool = False,
    initial_amount: Optional[Decimal] = None,
) -> Decimal:
    """
    从交易记录计算净投入

    Args:
        transaction_string: 交易记录字符串
        suffix: 数据目录后缀
        is_qdii: 是否为 QDII 基金
        initial_amount: CSV 中的初始金额（作为备用）

    Returns:
        净投入金额
    """
    if not transaction_string or not transaction_string.strip():
        return initial_amount or Decimal("0")

    parsed = parse_transactions(transaction_string, suffix, is_qdii)

    # 检查是否有智能定投（totalAmount = 0 的情况）
    has_smart_investment = any(
        tx.investment_type == InvestmentType.SMART for tx in parsed.transactions
    )

    # 智能定投使用 CSV 初始金额
    if has_smart_investment and initial_amount:
        return initial_amount

    if parsed.net_invest > 0:
        return parsed.net_invest

    return initial_amount or Decimal("0")
