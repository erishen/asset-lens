"""
Tests for IRR calculator.
"""

from datetime import date, datetime
from decimal import Decimal

from asset_lens.core.irr_calculator import IRRCalculator, irr_calculator
from asset_lens.data.models import Transaction


class TestIRRCalculator:
    """Test IRRCalculator class"""

    def setup_method(self):
        self.calculator = IRRCalculator()

    def test_calculate_irr_simple_case(self):
        cashflows = [-100, 110]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is not None
        assert 9 < irr < 11

    def test_calculate_irr_multiple_periods(self):
        cashflows = [-100, 0, 0, 121]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is not None
        assert 6 < irr < 7

    def test_calculate_irr_no_profit(self):
        cashflows = [-100, 100]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is not None
        assert abs(irr) < 1

    def test_calculate_irr_loss(self):
        cashflows = [-100, 90]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is not None
        assert irr < 0

    def test_calculate_irr_insufficient_cashflows(self):
        cashflows = [-100]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is None

    def test_calculate_irr_empty_cashflows(self):
        cashflows = []
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is None

    def test_calculate_irr_all_positive(self):
        cashflows = [100, 100, 100]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is None

    def test_calculate_irr_all_negative(self):
        cashflows = [-100, -100, -100]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is None

    def test_calculate_irr_complex_case(self):
        cashflows = [-1000, 300, 300, 300, 300, 300]
        irr = self.calculator.calculate_irr(cashflows)
        assert irr is not None
        assert 14 < irr < 16

    def test_calculate_irr_newton_simple(self):
        cashflows = [-100, 110]
        irr = self.calculator.calculate_irr_newton(cashflows)
        assert irr is not None
        assert 9 < irr < 11

    def test_calculate_irr_newton_complex(self):
        cashflows = [-1000, 300, 300, 300, 300, 300]
        irr = self.calculator.calculate_irr_newton(cashflows)
        assert irr is not None
        assert 14 < irr < 16

    def test_calculate_simple_annual_return(self):
        result = self.calculator.calculate_simple_annual_return(Decimal("1000"), Decimal("1200"), 365)
        assert result is not None
        assert 19 < result < 21

    def test_calculate_simple_annual_return_half_year(self):
        result = self.calculator.calculate_simple_annual_return(Decimal("1000"), Decimal("1100"), 182)
        assert result is not None
        assert 18 < result < 22

    def test_calculate_simple_annual_return_zero_days(self):
        result = self.calculator.calculate_simple_annual_return(Decimal("1000"), Decimal("1200"), 0)
        assert result == Decimal("20")

    def test_calculate_simple_annual_return_zero_initial(self):
        result = self.calculator.calculate_simple_annual_return(Decimal("0"), Decimal("1200"), 365)
        assert result is None

    def test_calculate_simple_annual_return_negative_initial(self):
        result = self.calculator.calculate_simple_annual_return(Decimal("-1000"), Decimal("1200"), 365)
        assert result is None

    def test_calculate_compound_return(self):
        result = self.calculator.calculate_compound_return(Decimal("1000"), Decimal("1200"), 365)
        assert result is not None
        assert 19 < result < 21

    def test_calculate_annualized_irr_basic(self):
        transactions = [
            Transaction(
                transaction_date=date(2024, 1, 1),
                action="buy",
                amount=Decimal("1000"),
            ),
            Transaction(
                transaction_date=date(2024, 6, 1),
                action="buy",
                amount=Decimal("500"),
            ),
        ]
        result = self.calculator.calculate_annualized_irr(
            transactions,
            Decimal("1800"),
            datetime(2024, 12, 31),
        )
        assert result is not None

    def test_calculate_annualized_irr_empty_transactions(self):
        result = self.calculator.calculate_annualized_irr(
            [],
            Decimal("1100"),
            datetime(2024, 12, 31),
        )
        assert result is None

    def test_calculate_annualized_irr_multiple_transactions(self):
        transactions = [
            Transaction(
                transaction_date=date(2024, 1, 1),
                action="buy",
                amount=Decimal("500"),
            ),
            Transaction(
                transaction_date=date(2024, 6, 1),
                action="buy",
                amount=Decimal("500"),
            ),
        ]
        result = self.calculator.calculate_annualized_irr(
            transactions,
            Decimal("1200"),
            datetime(2024, 12, 31),
        )
        assert result is not None

    def test_calculate_annualized_irr_with_sell(self):
        transactions = [
            Transaction(
                transaction_date=date(2024, 1, 1),
                action="buy",
                amount=Decimal("1000"),
            ),
            Transaction(
                transaction_date=date(2024, 3, 1),
                action="buy",
                amount=Decimal("500"),
            ),
            Transaction(
                transaction_date=date(2024, 6, 1),
                action="sell",
                amount=Decimal("200"),
            ),
        ]
        result = self.calculator.calculate_annualized_irr(
            transactions,
            Decimal("1400"),
            datetime(2024, 12, 31),
        )
        assert result is not None


class TestIRRGlobalInstance:
    """Test global IRR calculator instance"""

    def test_global_instance_exists(self):
        assert irr_calculator is not None
        assert isinstance(irr_calculator, IRRCalculator)

    def test_global_instance_works(self):
        cashflows = [-100, 110]
        irr = irr_calculator.calculate_irr(cashflows)
        assert irr is not None
