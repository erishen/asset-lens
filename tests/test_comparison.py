"""
Tests for comparison module.
"""

from datetime import date
from decimal import Decimal

from asset_lens.core.comparison import ComparisonAnalyzer, ComparisonResult, TrendAnalysis
from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel


class TestComparisonResult:
    """Test ComparisonResult dataclass"""

    def test_creation(self):
        """Test creating ComparisonResult"""
        result = ComparisonResult(
            name="Test Product",
            type="股票",
            amount_before=Decimal("10000"),
            amount_after=Decimal("11000"),
            amount_change=Decimal("1000"),
            return_rate=Decimal("10.0"),
            investment_days=365,
            annualized_return=Decimal("10.0"),
        )

        assert result.name == "Test Product"
        assert result.type == "股票"
        assert result.amount_before == Decimal("10000")
        assert result.amount_after == Decimal("11000")
        assert result.amount_change == Decimal("1000")
        assert result.return_rate == Decimal("10.0")

    def test_to_dict(self):
        """Test to_dict method"""
        result = ComparisonResult(
            name="Test Product",
            type="股票",
            amount_before=Decimal("10000"),
            amount_after=Decimal("11000"),
            amount_change=Decimal("1000"),
            return_rate=Decimal("10.0"),
            investment_days=365,
            annualized_return=Decimal("10.0"),
        )

        d = result.to_dict()
        assert d["名称"] == "Test Product"
        assert d["类型"] == "股票"
        assert d["收益率"] == "10.00%"


class TestTrendAnalysis:
    """Test TrendAnalysis dataclass"""

    def test_creation(self):
        """Test creating TrendAnalysis"""
        trend = TrendAnalysis(
            period="周度",
            total_amount_before=Decimal("100000"),
            total_amount_after=Decimal("105000"),
            total_change=Decimal("5000"),
            total_return_rate=Decimal("5.0"),
            products_count=10,
            positive_count=7,
            negative_count=3,
        )

        assert trend.period == "周度"
        assert trend.total_amount_before == Decimal("100000")
        assert trend.total_amount_after == Decimal("105000")
        assert trend.products_count == 10
        assert trend.positive_count == 7
        assert trend.negative_count == 3

    def test_to_dict(self):
        """Test to_dict method"""
        trend = TrendAnalysis(
            period="周度",
            total_amount_before=Decimal("100000"),
            total_amount_after=Decimal("105000"),
            total_change=Decimal("5000"),
            total_return_rate=Decimal("5.0"),
            products_count=10,
            positive_count=7,
            negative_count=3,
        )

        d = trend.to_dict()
        assert d["分析周期"] == "周度"
        assert d["产品数量"] == 10


class TestComparisonAnalyzer:
    """Test ComparisonAnalyzer class"""

    def test_init(self):
        """Test initialization"""
        analyzer = ComparisonAnalyzer()
        assert analyzer is not None

    def test_compare_periods_empty(self):
        """Test comparing empty periods"""
        analyzer = ComparisonAnalyzer()
        result = analyzer.compare_periods([], [])

        assert result is not None
        assert "trend" in result
        assert "details" in result
        assert len(result["details"]) == 0

    def test_compare_periods_single_product(self):
        """Test comparing single product"""
        analyzer = ComparisonAnalyzer()

        product_before = InvestmentProduct(
            name="Product A",
            investment_type=InvestmentType.STOCK,
            risk_level=RiskLevel.HIGH,
            current_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
        )

        product_after = InvestmentProduct(
            name="Product A",
            investment_type=InvestmentType.STOCK,
            risk_level=RiskLevel.HIGH,
            current_amount=Decimal("11000"),
            start_date=date(2024, 1, 1),
        )

        result = analyzer.compare_periods([product_before], [product_after])

        assert result is not None
        assert "trend" in result
        assert "details" in result
        assert len(result["details"]) == 1

    def test_compare_periods_multiple_products(self):
        """Test comparing multiple products"""
        analyzer = ComparisonAnalyzer()

        products_before = [
            InvestmentProduct(
                name="Product A",
                investment_type=InvestmentType.STOCK,
                risk_level=RiskLevel.HIGH,
                current_amount=Decimal("10000"),
                start_date=date(2024, 1, 1),
            ),
            InvestmentProduct(
                name="Product B",
                investment_type=InvestmentType.BOND,
                risk_level=RiskLevel.LOW,
                current_amount=Decimal("20000"),
                start_date=date(2024, 2, 1),
            ),
        ]

        products_after = [
            InvestmentProduct(
                name="Product A",
                investment_type=InvestmentType.STOCK,
                risk_level=RiskLevel.HIGH,
                current_amount=Decimal("12000"),
                start_date=date(2024, 1, 1),
            ),
            InvestmentProduct(
                name="Product B",
                investment_type=InvestmentType.BOND,
                risk_level=RiskLevel.LOW,
                current_amount=Decimal("21000"),
                start_date=date(2024, 2, 1),
            ),
        ]

        result = analyzer.compare_periods(products_before, products_after)

        assert result is not None
        assert "trend" in result
        assert "details" in result
        assert len(result["details"]) == 2

    def test_compare_periods_new_product(self):
        """Test comparing with new product"""
        analyzer = ComparisonAnalyzer()

        product_after = InvestmentProduct(
            name="New Product",
            investment_type=InvestmentType.FUND,
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("5000"),
            start_date=date(2024, 3, 1),
        )

        result = analyzer.compare_periods([], [product_after])

        assert result is not None
        assert "trend" in result
        assert "details" in result
        assert len(result["details"]) == 1

    def test_compare_periods_removed_product(self):
        """Test comparing with removed product"""
        analyzer = ComparisonAnalyzer()

        product_before = InvestmentProduct(
            name="Removed Product",
            investment_type=InvestmentType.FUND,
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("5000"),
            start_date=date(2024, 1, 1),
        )

        result = analyzer.compare_periods([product_before], [])

        assert result is not None
        assert "trend" in result
        assert "details" in result
        assert len(result["details"]) == 1

    def test_analyze_by_type(self):
        """Test analyzing by type"""
        analyzer = ComparisonAnalyzer()

        products = [
            InvestmentProduct(
                name="Stock A",
                investment_type=InvestmentType.STOCK,
                risk_level=RiskLevel.HIGH,
                current_amount=Decimal("11000"),
                start_date=date(2024, 1, 1),
            ),
            InvestmentProduct(
                name="Bond A",
                investment_type=InvestmentType.BOND,
                risk_level=RiskLevel.LOW,
                current_amount=Decimal("21000"),
                start_date=date(2024, 2, 1),
            ),
        ]

        result = analyzer.analyze_by_type(products)

        assert result is not None
        assert "type_stats" in result
