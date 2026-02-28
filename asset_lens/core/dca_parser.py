"""
DCA (Dollar Cost Average) strategy parser for asset-lens.
定投策略解析和计算模块，支持4种定投模式
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List

from ..config import config
from ..data.models import Currency, Transaction


class DCAInvestmentType(str, Enum):
    """定投类型"""

    FIXED = "fixed"  # 固定金额
    RANGE = "range"  # 智能区间
    FLOAT = "float"  # 浮动金额
    VALUATION = "valuation"  # 估值模式


class DCAParser:
    """定投策略解析器"""

    # 工作日（周一到周五）
    WEEKDAYS = {0, 1, 2, 3, 4}  # 0=周一, 4=周五

    @staticmethod
    def parse_investment_type(
        amount_str: str,
    ) -> tuple[DCAInvestmentType, Decimal, Decimal | None]:
        """
        解析定投类型和金额
        Args:
            amount_str: 金额字符串，如 "100", "50~150", "100±20", "100-300-500"
        Returns:
            (定投类型, 基础金额, 最大金额)
        """
        amount_str = amount_str.strip()

        # 估值模式：100-300-500 (三个数字，两个短横线)
        if "--" not in amount_str and amount_str.count("-") == 2:
            parts = amount_str.split("-")
            if len(parts) == 3:
                try:
                    low = Decimal(parts[0].strip())
                    normal = Decimal(parts[1].strip())
                    high = Decimal(parts[2].strip())
                    # 使用正常估值金额作为基础
                    return DCAInvestmentType.VALUATION, normal, high
                except Exception:
                    pass

        # 智能区间：50~150 (一个波浪号)
        if "~" in amount_str:
            parts = amount_str.split("~")
            if len(parts) == 2:
                try:
                    low = Decimal(parts[0].strip())
                    high = Decimal(parts[1].strip())
                    # 使用平均值
                    avg = (low + high) / Decimal("2")
                    return DCAInvestmentType.RANGE, avg, high
                except Exception:
                    pass

        # 浮动金额：100±20 (包含±符号)
        if "±" in amount_str or "+/-" in amount_str:
            parts = amount_str.replace("+/-", "±").split("±")
            if len(parts) == 2:
                try:
                    base = Decimal(parts[0].strip())
                    delta = Decimal(parts[1].strip())
                    # 使用基础金额
                    return DCAInvestmentType.FLOAT, base, base + delta
                except Exception:
                    pass

        # 固定金额：纯数字
        try:
            amount = Decimal(amount_str)
            return DCAInvestmentType.FIXED, amount, amount
        except Exception:
            return DCAInvestmentType.FIXED, Decimal("0"), Decimal("0")

    @staticmethod
    def parse_date_range(
        date_range_str: str, reference_date: datetime | None = None
    ) -> tuple[datetime | None, datetime | None]:
        """
        解析日期范围
        Args:
            date_range_str: 日期范围字符串，如 "2024/1/15-2024/10/1", "2024/1/15-now"
            reference_date: 参考日期，用于替换 "now"
        Returns:
            (开始日期, 结束日期)
        """
        if "-" not in date_range_str:
            return None, None

        parts = date_range_str.split("-")
        if len(parts) < 2:
            return None, None

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        # 解析开始日期
        start_date = DCAParser.parse_date(start_str)
        if start_date is None:
            return None, None

        # 解析结束日期
        if end_str.lower() == "now":
            end_date = reference_date or datetime.now()
        else:
            end_date = DCAParser.parse_date(end_str)

        return start_date, end_date

    @staticmethod
    def parse_date(date_str: str) -> datetime | None:
        """解析日期字符串"""
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
    ) -> List[Transaction]:
        """
        解析交易记录字符串
        Args:
            record_str: 交易记录字符串，如 "2024/1/15-now:buy:100"
            reference_date: 参考日期，用于替换 "now"
            currency: 货币类型
        Returns:
            交易记录列表
        """
        transactions = []

        if not record_str or not record_str.strip():
            return transactions

        # 分割多个交易记录（使用分号分隔）
        record_parts = record_str.split(";")

        for part in record_parts:
            part = part.strip()
            if not part:
                continue

            # 解析：日期范围:操作:金额
            if ":" not in part:
                continue

            parts = part.split(":")
            if len(parts) < 3:
                continue

            date_range_str = parts[0].strip()
            action = parts[1].strip()
            amount_str = ":".join(parts[2:]).strip()  # 处理金额中可能包含的冒号

            # 解析日期范围
            start_date, end_date = cls.parse_date_range(date_range_str, reference_date)
            if start_date is None or end_date is None:
                continue

            # 如果开始日期晚于结束日期，跳过
            if start_date > end_date:
                continue

            # 解析定投类型和金额
            investment_type, base_amount, max_amount = cls.parse_investment_type(
                amount_str
            )

            # 生成定投交易
            dca_transactions = cls.generate_dca_transactions(
                start_date=start_date,
                end_date=end_date,
                action=action,
                amount=base_amount,
                currency=currency,
                investment_type=investment_type,
            )

            transactions.extend(dca_transactions)

        return transactions

    @classmethod
    def generate_dca_transactions(
        cls,
        start_date: datetime,
        end_date: datetime,
        action: str,
        amount: Decimal,
        currency: Currency,
        investment_type: DCAInvestmentType = DCAInvestmentType.FIXED,
    ) -> List[Transaction]:
        """
        生成定投交易记录
        Args:
            start_date: 开始日期
            end_date: 结束日期
            action: 操作类型（buy/sell）
            amount: 金额
            currency: 货币类型
            investment_type: 定投类型
        Returns:
            交易记录列表
        """
        transactions = []

        # 计算总天数
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return transactions

        # 按工作日计算（占比70%）
        workday_ratio = config.workday_ratio
        workday_count = int(total_days * workday_ratio)

        # 每期投入金额
        if workday_count > 0:
            period_amount = amount / Decimal(workday_count)
        else:
            period_amount = Decimal("0")

        # 生成交易记录（每个工作日）
        current_date = start_date
        transaction_count = 0

        while current_date <= end_date and transaction_count < workday_count:
            # 只在工作日生成交易
            if current_date.weekday() in cls.WEEKDAYS:
                transaction = Transaction(
                    transaction_date=current_date.date(),
                    action=action,
                    amount=period_amount,
                    currency=currency,
                )
                transactions.append(transaction)
                transaction_count += 1

            # 移动到下一天
            current_date += timedelta(days=1)

        return transactions

    @staticmethod
    def calculate_total_investment(
        transactions: List[Transaction], action: str = "buy"
    ) -> Decimal:
        """
        计算总投入
        Args:
            transactions: 交易记录列表
            action: 操作类型（buy/sell）
        Returns:
            总金额
        """
        total = Decimal("0")
        for t in transactions:
            if t.action.lower() == action.lower():
                total += t.amount
        return total

    @staticmethod
    def calculate_net_investment(transactions: List[Transaction]) -> Decimal:
        """
        计算净投入（买入 - 卖出）
        Args:
            transactions: 交易记录列表
        Returns:
            净投入金额
        """
        buy_total = DCAParser.calculate_total_investment(transactions, "buy")
        sell_total = DCAParser.calculate_total_investment(transactions, "sell")
        return buy_total - sell_total


# 全局定投解析器实例
dca_parser = DCAParser()
