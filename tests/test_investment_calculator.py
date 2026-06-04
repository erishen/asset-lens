from datetime import date
from decimal import Decimal

from asset_lens.data.parsers.investment_calculator import (
    InvestmentCalculator,
    days360,
)


class TestDays360:
    def test_same_month(self):
        result = days360(date(2024, 1, 1), date(2024, 1, 31))
        assert result == 30

    def test_one_month(self):
        result = days360(date(2024, 1, 1), date(2024, 2, 1))
        assert result == 30

    def test_one_year(self):
        result = days360(date(2024, 1, 1), date(2025, 1, 1))
        assert result == 360

    def test_european_mode(self):
        result = days360(date(2024, 1, 31), date(2024, 2, 28), european=True)
        assert result == 28

    def test_day_31_adjustment(self):
        result = days360(date(2024, 1, 31), date(2024, 2, 1))
        assert result == 1


class TestParseTransactionRecords:
    def test_basic(self):
        records = "2024/01/15:buy:10000; 2024/06/15:sell:5000"
        result = InvestmentCalculator.parse_transaction_records(records)
        assert len(result) == 2
        assert result[0]["type"] == "buy"
        assert result[0]["amount"] == 10000.0
        assert result[1]["type"] == "sell"

    def test_chinese_semicolon(self):
        records = "2024/01/15:buy:10000；2024/06/15:sell:5000"
        result = InvestmentCalculator.parse_transaction_records(records)
        assert len(result) == 2

    def test_empty(self):
        assert InvestmentCalculator.parse_transaction_records("") == []

    def test_none(self):
        assert InvestmentCalculator.parse_transaction_records(None) == []

    def test_invalid_record(self):
        records = "invalid;2024/01/15:buy:1000"
        result = InvestmentCalculator.parse_transaction_records(records)
        assert len(result) == 1


class TestCalculateCashflows:
    def test_basic(self):
        transactions = [
            {"type": "buy", "amount": 10000},
            {"type": "sell", "amount": 5000},
        ]
        result = InvestmentCalculator.calculate_cashflows(transactions, Decimal("8000"))
        assert result == [-10000.0, 5000.0, 8000.0]

    def test_no_current_amount(self):
        transactions = [{"type": "buy", "amount": 10000}]
        result = InvestmentCalculator.calculate_cashflows(transactions, Decimal("0"))
        assert result == [-10000.0]

    def test_empty_transactions(self):
        result = InvestmentCalculator.calculate_cashflows([], Decimal("5000"))
        assert result == [5000.0]


class TestCalculateCashflowsWithDays:
    def test_basic(self):
        transactions = [
            {"date": "2024/01/15", "type": "buy", "amount": 10000},
            {"date": "2024/06/15", "type": "sell", "amount": 5000},
        ]
        start_date = date(2024, 1, 1)
        result = InvestmentCalculator.calculate_cashflows_with_days(
            transactions, start_date, Decimal("8000"), 360
        )
        assert len(result) == 3
        assert result[0]["amount"] == -10000
        assert result[1]["amount"] == 5000
        assert result[2]["amount"] == 8000.0

    def test_no_start_date(self):
        result = InvestmentCalculator.calculate_cashflows_with_days(
            [], None, Decimal("1000"), 360
        )
        assert result == []

    def test_with_interest_payment(self):
        transactions = [
            {"date": "2024/01/15", "type": "buy", "amount": 10000},
        ]
        start_date = date(2024, 1, 1)
        result = InvestmentCalculator.calculate_cashflows_with_days(
            transactions, start_date, Decimal("8000"), 360, Decimal("500")
        )
        assert result[-1]["amount"] == 8500.0


class TestIsDCAProduct:
    def test_dca_fund_type(self):
        from unittest.mock import MagicMock
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "定投基金"
        product.transaction_records = None
        assert InvestmentCalculator.is_dca_product(product) is True

    def test_non_dca(self):
        from unittest.mock import MagicMock
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "股票"
        product.transaction_records = None
        assert InvestmentCalculator.is_dca_product(product) is False
