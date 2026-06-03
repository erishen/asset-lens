from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from asset_lens.data.parsers.dca_calculator import DCACalculator


class TestCalculateAnnualReturn:
    def test_positive_return(self):
        result = DCACalculator.calculate_annual_return(
            Decimal("10000"), Decimal("12000"), 360
        )
        assert result is not None
        assert float(result) > 0

    def test_zero_investment(self):
        result = DCACalculator.calculate_annual_return(Decimal("0"), Decimal("1000"), 360)
        assert result is None

    def test_zero_days(self):
        result = DCACalculator.calculate_annual_return(Decimal("10000"), Decimal("12000"), 0)
        assert result is None

    def test_loss(self):
        result = DCACalculator.calculate_annual_return(
            Decimal("10000"), Decimal("5000"), 360
        )
        assert result is not None
        assert float(result) < 0

    def test_total_loss(self):
        result = DCACalculator.calculate_annual_return(
            Decimal("10000"), Decimal("0"), 360
        )
        assert result == Decimal("-100")

    def test_short_period(self):
        result = DCACalculator.calculate_annual_return(
            Decimal("10000"), Decimal("10100"), 30
        )
        assert result is not None
        assert float(result) > 0


class TestCalculateCashflows:
    def test_basic(self):
        transactions = [
            {"date": "2024/01/15", "amount": 5000},
            {"date": "2024/07/15", "amount": 5000},
        ]
        start_date = datetime(2024, 1, 1)
        current_amount = Decimal("12000")
        cashflows = DCACalculator.calculate_cashflows(transactions, start_date, current_amount, 360)
        assert len(cashflows) == 3
        assert cashflows[0]["days"] == 14
        assert cashflows[2]["amount"] == -12000.0

    def test_empty_transactions(self):
        cashflows = DCACalculator.calculate_cashflows(
            [], datetime(2024, 1, 1), Decimal("10000"), 360
        )
        assert len(cashflows) == 1
        assert cashflows[0]["amount"] == -10000.0


class TestIsDCAProduct:
    def test_dca_fund_type(self):
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "定投基金"
        assert DCACalculator.is_dca_product(product) is True

    def test_non_dca_type(self):
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "股票"
        product.transaction_records = None
        assert DCACalculator.is_dca_product(product) is False

    def test_with_transaction_records_dca(self):
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "基金"
        product.transaction_records = "2024/01/01-now:buy:1000"
        assert DCACalculator.is_dca_product(product) is True

    def test_with_sell_records(self):
        product = MagicMock()
        product.investment_type = MagicMock()
        product.investment_type.value = "基金"
        product.transaction_records = "2024/01/01-2024/06/01:buy:1000:sell:500"
        assert DCACalculator.is_dca_product(product) is False

    def test_no_relevant_attributes(self):
        product = MagicMock(spec=[])
        assert DCACalculator.is_dca_product(product) is False
