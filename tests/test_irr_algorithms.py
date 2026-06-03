from datetime import date

from asset_lens.core.irr_algorithms import IRRAlgorithmsMixin


class TestCalculateIRRWithDays:
    def test_basic(self):
        cashflows = [
            {"amount": -10000, "days": 0},
            {"amount": 5000, "days": 180},
            {"amount": 6000, "days": 360},
        ]
        result = IRRAlgorithmsMixin.calculate_irr_with_days(cashflows)
        assert result is not None
        assert -1 < result < 10

    def test_empty(self):
        assert IRRAlgorithmsMixin.calculate_irr_with_days([]) is None

    def test_single_cashflow(self):
        cashflows = [{"amount": -1000, "days": 0}]
        result = IRRAlgorithmsMixin.calculate_irr_with_days(cashflows)
        assert result is not None

    def test_negative_return(self):
        cashflows = [
            {"amount": -10000, "days": 0},
            {"amount": 5000, "days": 360},
        ]
        result = IRRAlgorithmsMixin.calculate_irr_with_days(cashflows)
        assert result is not None


class TestCalculateIRRNewton:
    def test_basic(self):
        cashflows = [-10000, 3000, 3000, 3000, 3000]
        result = IRRAlgorithmsMixin.calculate_irr_newton(cashflows)
        assert result is not None
        assert 7 < result < 8

    def test_empty(self):
        assert IRRAlgorithmsMixin.calculate_irr_newton([]) is None

    def test_single(self):
        assert IRRAlgorithmsMixin.calculate_irr_newton([100]) is None

    def test_all_positive(self):
        assert IRRAlgorithmsMixin.calculate_irr_newton([100, 200, 300]) is None

    def test_all_negative(self):
        assert IRRAlgorithmsMixin.calculate_irr_newton([-100, -200, -300]) is None

    def test_two_flows(self):
        cashflows = [-1000, 1100]
        result = IRRAlgorithmsMixin.calculate_irr_newton(cashflows)
        assert result is not None
        assert 9 < result < 11


class TestCalculateIRRBisection:
    def test_basic(self):
        cashflows = [-10000, 3000, 3000, 3000, 3000]
        result = IRRAlgorithmsMixin.calculate_irr_bisection(cashflows)
        assert result is not None
        assert 7 < result < 8

    def test_empty(self):
        assert IRRAlgorithmsMixin.calculate_irr_bisection([]) is None

    def test_single(self):
        assert IRRAlgorithmsMixin.calculate_irr_bisection([100]) is None

    def test_all_positive(self):
        assert IRRAlgorithmsMixin.calculate_irr_bisection([100, 200]) is None

    def test_all_negative(self):
        assert IRRAlgorithmsMixin.calculate_irr_bisection([-100, -200]) is None


class TestCalculateXIRR:
    def test_basic(self):
        cashflows = [
            (date(2024, 1, 1), -10000),
            (date(2024, 7, 1), 5000),
            (date(2025, 1, 1), 6000),
        ]
        result = IRRAlgorithmsMixin.calculate_xirr(cashflows)
        assert result is not None
        assert -100 < result < 1000

    def test_empty(self):
        assert IRRAlgorithmsMixin.calculate_xirr([]) is None

    def test_single(self):
        result = IRRAlgorithmsMixin.calculate_xirr([(date(2024, 1, 1), -1000)])
        assert result is None

    def test_two_flows(self):
        cashflows = [
            (date(2024, 1, 1), -10000),
            (date(2025, 1, 1), 11000),
        ]
        result = IRRAlgorithmsMixin.calculate_xirr(cashflows)
        assert result is not None
        assert 0 < result < 20
