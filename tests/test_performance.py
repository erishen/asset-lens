"""
Tests for report performance module.
"""

from decimal import Decimal

import pytest

from asset_lens.report.performance import PerformanceAnalyzer


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return PerformanceAnalyzer()

    def test_init(self, analyzer):
        """Test initialization"""
        assert analyzer is not None

    def test_analyze_portfolio_performance(self, analyzer):
        """Test analyze portfolio performance"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        product = MagicMock()
        product.current_amount = Decimal("10000")
        product.profit_amount = Decimal("1000")
        product.investment_days = 30
        portfolio.products.append(product)

        result = analyzer.generate_investment_efficiency(portfolio)

        assert "total_profit" in result
        assert "overall_return" in result

    def test_generate_optimization_suggestions(self, analyzer):
        """Test generate optimization suggestions"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        suggestions = analyzer.generate_optimization_suggestions(portfolio)

        assert isinstance(suggestions, list)

    def test_empty_portfolio(self, analyzer):
        """Test with empty portfolio"""
        from unittest.mock import MagicMock

        portfolio = MagicMock()
        portfolio.products = []

        result = analyzer.generate_investment_efficiency(portfolio)

        assert result["total_profit"] == "0"
        assert result["product_count"] == 0
