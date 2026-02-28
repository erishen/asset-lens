"""
Tests for DCA parser module.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from asset_lens.core.dca_parser import DCAParser, DCAInvestmentType
from asset_lens.data.models import Currency


class TestDCAInvestmentType:
    """Test DCAInvestmentType enum"""

    def test_enum_values(self):
        """Test enum values"""
        assert DCAInvestmentType.FIXED == "fixed"
        assert DCAInvestmentType.RANGE == "range"
        assert DCAInvestmentType.FLOAT == "float"
        assert DCAInvestmentType.VALUATION == "valuation"


class TestDCAParserParseInvestmentType:
    """Test DCAParser.parse_investment_type method"""

    def test_fixed_amount(self):
        """Test parsing fixed amount"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("100")
        assert invest_type == DCAInvestmentType.FIXED
        assert base == Decimal("100")
        assert max_amt == Decimal("100")

    def test_fixed_amount_with_spaces(self):
        """Test parsing fixed amount with spaces"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("  200  ")
        assert invest_type == DCAInvestmentType.FIXED
        assert base == Decimal("200")

    def test_range_amount(self):
        """Test parsing range amount (智能区间)"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("50~150")
        assert invest_type == DCAInvestmentType.RANGE
        assert base == Decimal("100")  # Average
        assert max_amt == Decimal("150")

    def test_float_amount(self):
        """Test parsing float amount (浮动金额)"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("100±20")
        assert invest_type == DCAInvestmentType.FLOAT
        assert base == Decimal("100")
        assert max_amt == Decimal("120")

    def test_float_amount_with_slash(self):
        """Test parsing float amount with +/-"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("100+/-20")
        assert invest_type == DCAInvestmentType.FLOAT
        assert base == Decimal("100")
        assert max_amt == Decimal("120")

    def test_valuation_amount(self):
        """Test parsing valuation amount (估值模式)"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("80-200-400")
        assert invest_type == DCAInvestmentType.VALUATION
        assert base == Decimal("200")  # Normal amount
        assert max_amt == Decimal("400")

    def test_invalid_amount(self):
        """Test parsing invalid amount"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("invalid")
        assert invest_type == DCAInvestmentType.FIXED
        assert base == Decimal("0")
        assert max_amt == Decimal("0")

    def test_invalid_range(self):
        """Test parsing invalid range"""
        invest_type, base, max_amt = DCAParser.parse_investment_type("abc~def")
        # Should fall back to fixed (which will fail and return 0)
        assert invest_type == DCAInvestmentType.FIXED
        assert base == Decimal("0")


class TestDCAParserParseDate:
    """Test DCAParser.parse_date method"""

    def test_parse_date_slash(self):
        """Test parsing date with slash"""
        result = DCAParser.parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_dash(self):
        """Test parsing date with dash"""
        result = DCAParser.parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_time(self):
        """Test parsing date with time"""
        result = DCAParser.parse_date("2024/01/15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_date_invalid(self):
        """Test parsing invalid date"""
        result = DCAParser.parse_date("invalid")
        assert result is None

    def test_parse_date_empty(self):
        """Test parsing empty date"""
        result = DCAParser.parse_date("")
        assert result is None


class TestDCAParserParseDateRange:
    """Test DCAParser.parse_date_range method"""

    def test_parse_date_range(self):
        """Test parsing date range"""
        start, end = DCAParser.parse_date_range("2024/01/15-2024/06/30")
        assert start == datetime(2024, 1, 15)
        assert end == datetime(2024, 6, 30)

    def test_parse_date_range_with_now(self):
        """Test parsing date range with 'now'"""
        ref_date = datetime(2024, 12, 31)
        start, end = DCAParser.parse_date_range("2024/01/15-now", ref_date)
        assert start == datetime(2024, 1, 15)
        assert end == ref_date

    def test_parse_date_range_no_dash(self):
        """Test parsing date range without dash"""
        start, end = DCAParser.parse_date_range("2024/01/15")
        assert start is None
        assert end is None

    def test_parse_date_range_invalid(self):
        """Test parsing invalid date range"""
        start, end = DCAParser.parse_date_range("invalid-invalid")
        assert start is None
        assert end is None


class TestDCAParserParseTransactionRecord:
    """Test DCAParser.parse_transaction_record method"""

    def test_parse_simple_record(self):
        """Test parsing simple transaction record"""
        ref_date = datetime(2024, 6, 30)
        transactions = DCAParser.parse_transaction_record(
            "2024/01/01-2024/01/31:buy:100",
            reference_date=ref_date
        )
        assert len(transactions) > 0

    def test_parse_multiple_records(self):
        """Test parsing multiple transaction records"""
        ref_date = datetime(2024, 12, 31)
        transactions = DCAParser.parse_transaction_record(
            "2024/01/01-2024/01/31:buy:100;2024/02/01-2024/02/28:buy:200",
            reference_date=ref_date
        )
        assert len(transactions) > 0

    def test_parse_empty_record(self):
        """Test parsing empty record"""
        transactions = DCAParser.parse_transaction_record("")
        assert len(transactions) == 0

    def test_parse_record_with_now(self):
        """Test parsing record with 'now'"""
        ref_date = datetime(2024, 12, 31)
        transactions = DCAParser.parse_transaction_record(
            "2024/01/01-now:buy:100",
            reference_date=ref_date
        )
        assert len(transactions) > 0

    def test_parse_record_invalid_format(self):
        """Test parsing record with invalid format"""
        transactions = DCAParser.parse_transaction_record("invalid")
        assert len(transactions) == 0

    def test_parse_record_no_colon(self):
        """Test parsing record without colon"""
        transactions = DCAParser.parse_transaction_record("2024/01/01-2024/01/31")
        assert len(transactions) == 0


class TestDCAParserGenerateTransactions:
    """Test DCAParser.generate_dca_transactions method"""

    def test_generate_transactions(self):
        """Test generating transactions"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        transactions = DCAParser.generate_dca_transactions(
            start_date=start_date,
            end_date=end_date,
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.CNY,
        )
        
        assert len(transactions) > 0
        # All transactions should be buy
        for t in transactions:
            assert t.action == "buy"

    def test_generate_transactions_zero_days(self):
        """Test generating transactions with zero days"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1)  # Same day
        
        transactions = DCAParser.generate_dca_transactions(
            start_date=start_date,
            end_date=end_date,
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.CNY,
        )
        
        assert len(transactions) == 0

    def test_generate_transactions_end_before_start(self):
        """Test generating transactions with end before start"""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)
        
        transactions = DCAParser.generate_dca_transactions(
            start_date=start_date,
            end_date=end_date,
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.CNY,
        )
        
        assert len(transactions) == 0


class TestDCAParserCalculateTotalInvestment:
    """Test DCAParser.calculate_total_investment method"""

    def test_calculate_total_empty(self):
        """Test calculating total with empty list"""
        total = DCAParser.calculate_total_investment([])
        assert total == Decimal("0")
