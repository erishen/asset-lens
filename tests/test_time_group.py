"""
Tests for time group analysis.
"""

from datetime import date, timedelta
from decimal import Decimal

from asset_lens.core.time_group import TimeGroupAnalyzer, TimeGroupStats
from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel


class TestTimeGroupStats:
    """Test TimeGroupStats dataclass"""

    def test_stats_creation(self):
        stats = TimeGroupStats(
            group_name="短期投资",
            group_description="90天以内",
            products_count=5,
            total_amount=Decimal("50000"),
            total_initial=Decimal("45000"),
            total_profit=Decimal("5000"),
            avg_return_rate=Decimal("10"),
            avg_holding_days=45.5,
            products=["产品A", "产品B"],
        )
        assert stats.group_name == "短期投资"
        assert stats.products_count == 5
        assert stats.total_amount == Decimal("50000")

    def test_stats_to_dict(self):
        stats = TimeGroupStats(
            group_name="短期投资",
            group_description="90天以内",
            products_count=5,
            total_amount=Decimal("50000"),
            total_initial=Decimal("45000"),
            total_profit=Decimal("5000"),
            avg_return_rate=Decimal("10"),
            avg_holding_days=45.5,
            products=["产品A", "产品B"],
        )
        result = stats.to_dict()
        assert result["分组名称"] == "短期投资"
        assert result["产品数量"] == 5
        assert result["总金额"] == "50000"


class TestTimeGroupAnalyzer:
    """Test TimeGroupAnalyzer class"""

    def setup_method(self):
        self.analyzer = TimeGroupAnalyzer()

    def test_analyze_empty_products(self):
        result = self.analyzer.analyze_by_holding_period([])
        assert len(result["groups"]) == 0
        assert result["total_products"] == 0

    def test_analyze_short_term(self):
        today = date.today()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="短期产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("9000"),
            profit_amount=Decimal("1000"),
            start_date=today - timedelta(days=30),
        )
        result = self.analyzer.analyze_by_holding_period([product])

        assert len(result["groups"]) == 1
        assert result["groups"][0].group_name == "短期投资"

    def test_analyze_mid_term(self):
        today = date.today()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="中期产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("9000"),
            profit_amount=Decimal("1000"),
            start_date=today - timedelta(days=180),
        )
        result = self.analyzer.analyze_by_holding_period([product])

        assert len(result["groups"]) == 1
        assert result["groups"][0].group_name == "中期投资"

    def test_analyze_long_term(self):
        today = date.today()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="长期产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("8000"),
            profit_amount=Decimal("2000"),
            start_date=today - timedelta(days=400),
        )
        result = self.analyzer.analyze_by_holding_period([product])

        assert len(result["groups"]) == 1
        assert result["groups"][0].group_name == "长期投资"

    def test_analyze_unknown_term(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="未知期限产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("9000"),
            profit_amount=Decimal("1000"),
            start_date=None,
        )
        result = self.analyzer.analyze_by_holding_period([product])

        assert len(result["groups"]) == 1
        assert result["groups"][0].group_name == "未知期限"

    def test_analyze_multiple_products(self):
        today = date.today()
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="短期产品A",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                initial_amount=Decimal("9000"),
                profit_amount=Decimal("1000"),
                start_date=today - timedelta(days=30),
            ),
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="长期产品B",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("20000"),
                initial_amount=Decimal("18000"),
                profit_amount=Decimal("2000"),
                start_date=today - timedelta(days=400),
            ),
        ]
        result = self.analyzer.analyze_by_holding_period(products)

        assert len(result["groups"]) == 2
        assert result["total_products"] == 2

    def test_analyze_zero_amount_product(self):
        today = date.today()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="零金额产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("0"),
            initial_amount=Decimal("9000"),
            start_date=today - timedelta(days=30),
        )
        result = self.analyzer.analyze_by_holding_period([product])

        assert len(result["groups"]) == 0

    def test_analyze_by_start_year(self):
        date.today()
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="2023年产品",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                initial_amount=Decimal("9000"),
                profit_amount=Decimal("1000"),
                start_date=date(2023, 1, 1),
            ),
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="2024年产品",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("20000"),
                initial_amount=Decimal("18000"),
                profit_amount=Decimal("2000"),
                start_date=date(2024, 1, 1),
            ),
        ]
        result = self.analyzer.analyze_by_start_year(products)

        assert "year_groups" in result
        assert len(result["year_groups"]) == 2

    def test_analyze_by_start_year_unknown(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="未知年份产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("9000"),
            profit_amount=Decimal("1000"),
            start_date=None,
        )
        result = self.analyzer.analyze_by_start_year([product])

        assert "year_groups" in result
        assert len(result["year_groups"]) == 1
        assert result["year_groups"][0].group_name == "未知年份"

    def test_custom_thresholds(self):
        today = date.today()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("9000"),
            profit_amount=Decimal("1000"),
            start_date=today - timedelta(days=60),
        )
        result = self.analyzer.analyze_by_holding_period(
            [product],
            short_term_days=30,
            mid_term_days=90,
        )

        assert len(result["groups"]) == 1
        assert result["groups"][0].group_name == "中期投资"

    def test_total_statistics(self):
        today = date.today()
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="产品A",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                initial_amount=Decimal("9000"),
                profit_amount=Decimal("1000"),
                start_date=today - timedelta(days=30),
            ),
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="产品B",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("20000"),
                initial_amount=Decimal("18000"),
                profit_amount=Decimal("2000"),
                start_date=today - timedelta(days=400),
            ),
        ]
        result = self.analyzer.analyze_by_holding_period(products)

        assert result["total_amount"] == Decimal("30000")
        assert result["total_initial"] == Decimal("27000")
        assert result["total_profit"] == Decimal("3000")
