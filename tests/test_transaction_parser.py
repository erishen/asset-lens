"""
Tests for transaction_parser.py
"""

from datetime import date
from decimal import Decimal

import pytest

from asset_lens.data.transaction_parser import (
    InvestmentType,
    ParsedTransactions,
    Transaction,
    parse_date,
    parse_stop_periods,
)


class TestInvestmentType:
    """InvestmentType 测试"""

    def test_investment_type_values(self):
        """测试定投类型值"""
        assert InvestmentType.FIXED.value == "fixed"
        assert InvestmentType.SMART.value == "smart"
        assert InvestmentType.FLOATING.value == "floating"
        assert InvestmentType.VALUATION.value == "valuation"


class TestTransaction:
    """Transaction 测试"""

    def test_transaction_creation(self):
        """测试交易记录创建"""
        tx = Transaction(
            date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("1000"),
        )
        assert tx.date == date(2024, 1, 1)
        assert tx.action == "buy"
        assert tx.amount == Decimal("1000")
        assert tx.is_period_investment is False
        assert tx.work_days == 0
        assert tx.daily_amount == Decimal("0")
        assert tx.investment_type == InvestmentType.FIXED

    def test_transaction_with_period_investment(self):
        """测试定投交易记录"""
        tx = Transaction(
            date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("1000"),
            is_period_investment=True,
            work_days=20,
            daily_amount=Decimal("50"),
            investment_type=InvestmentType.SMART,
        )
        assert tx.is_period_investment is True
        assert tx.work_days == 20
        assert tx.daily_amount == Decimal("50")
        assert tx.investment_type == InvestmentType.SMART


class TestParsedTransactions:
    """ParsedTransactions 测试"""

    def test_parsed_transactions_creation(self):
        """测试解析后的交易记录集合创建"""
        transactions = [
            Transaction(date=date(2024, 1, 1), action="buy", amount=Decimal("1000")),
            Transaction(date=date(2024, 1, 15), action="sell", amount=Decimal("500")),
        ]
        parsed = ParsedTransactions(
            transactions=transactions,
            total_buy=Decimal("1000"),
            total_sell=Decimal("500"),
            net_invest=Decimal("500"),
            buy_count=1,
            sell_count=1,
        )
        assert len(parsed.transactions) == 2
        assert parsed.total_buy == Decimal("1000")
        assert parsed.total_sell == Decimal("500")
        assert parsed.net_invest == Decimal("500")
        assert parsed.buy_count == 1
        assert parsed.sell_count == 1


class TestParseDate:
    """parse_date 测试"""

    def test_parse_date_normal(self):
        """测试解析正常日期"""
        result = parse_date("2024/1/15", 20260307)
        assert result == date(2024, 1, 15)

    def test_parse_date_with_dash(self):
        """测试解析带横线的日期"""
        result = parse_date("2024-1-15", 20260307)
        assert result == date(2024, 1, 15)

    def test_parse_date_now(self):
        """测试解析 now 日期"""
        result = parse_date("now", 20260307)
        assert result.year == 2026
        assert result.month == 3
        assert 1 <= result.day <= 31


class TestParseStopPeriods:
    """parse_stop_periods 测试"""

    def test_parse_stop_periods_empty(self):
        """测试解析空暂停期间"""
        result = parse_stop_periods("")
        assert result == []

    def test_parse_stop_periods_single_day(self):
        """测试解析单日暂停"""
        result = parse_stop_periods("2024/1/15:stop")
        assert len(result) == 1
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1] == date(2024, 1, 15)

    def test_parse_stop_periods_range(self):
        """测试解析暂停期间范围"""
        result = parse_stop_periods("2024/1/15-2024/1/20:stop")
        assert len(result) == 1
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1] == date(2024, 1, 20)

    def test_parse_stop_periods_multiple(self):
        """测试解析多个暂停期间"""
        result = parse_stop_periods("2024/1/15:stop;2024/1/20-2024/1/25:stop")
        assert len(result) == 2

    def test_parse_stop_periods_no_stop_keyword(self):
        """测试没有 stop 关键字"""
        result = parse_stop_periods("2024/1/15:buy:100")
        assert result == []
