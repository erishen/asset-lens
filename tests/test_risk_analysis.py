"""
Tests for report risk analysis module.
"""

from decimal import Decimal

import pytest

from asset_lens.report.risk_analysis import LegacyRiskAnalyzer


class TestRiskAnalyzer:
    """Test RiskAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return LegacyRiskAnalyzer()

    def test_init(self, analyzer):
        """Test initialization"""
        assert analyzer is not None

    def test_get_type_distribution(self, analyzer):
        """Test get type distribution"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        product = MagicMock()
        product.product_type = "股票"
        product.current_amount = Decimal("10000")
        portfolio.products.append(product)

        result = analyzer.get_type_distribution(portfolio)

        assert isinstance(result, dict)

    def test_get_risk_distribution(self, analyzer):
        """Test get risk distribution"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        product = MagicMock()
        product.product_type = "股票"
        product.current_amount = Decimal("10000")
        product.profit_amount = Decimal("1000")
        portfolio.products.append(product)

        result = analyzer.get_risk_distribution(portfolio)

        assert isinstance(result, dict)

    def test_generate_risk_warnings(self, analyzer):
        """Test generate risk warnings"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        product = MagicMock()
        product.product_type = "股票"
        product.current_amount = Decimal("100000")
        product.profit_amount = Decimal("10000")
        product.risk_level = None
        product.maturity_date = None
        portfolio.products.append(product)

        warnings = analyzer.generate_risk_warnings(portfolio)

        assert isinstance(warnings, list)

    def test_empty_portfolio(self, analyzer):
        """Test with empty portfolio"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        result = analyzer.get_type_distribution(portfolio)
        assert "distribution" in result

        warnings = analyzer.generate_risk_warnings(portfolio)
        assert warnings == []
