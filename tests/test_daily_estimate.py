"""Tests for daily estimate module."""
from decimal import Decimal
import pytest
from asset_lens.core.daily_estimate import (
    DailyEstimateResult,
    get_expected_annual_return,
    get_market_sensitivity,
    get_adjusted_market_sensitivity,
    estimate_product_return,
    estimate_all_products,
)
from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel


class TestDailyEstimateResult:
    """Test DailyEstimateResult class."""

    def test_init(self):
        """Test DailyEstimateResult initialization."""
        result = DailyEstimateResult(
            product_name="测试产品",
            product_type="基金",
            current_value=Decimal("10000"),
            estimated_daily_return=Decimal("10"),
            estimated_daily_return_rate=Decimal("0.001"),
            expected_annual_return=Decimal("0.04"),
            market_sensitivity=Decimal("0.8"),
            risk_level="中风险",
        )
        assert result.product_name == "测试产品"
        assert result.product_type == "基金"
        assert result.current_value == Decimal("10000")
        assert result.estimated_daily_return == Decimal("10")
        assert result.estimated_daily_return_rate == Decimal("0.001")
        assert result.expected_annual_return == Decimal("0.04")
        assert result.market_sensitivity == Decimal("0.8")
        assert result.risk_level == "中风险"

    def test_to_dict(self):
        """Test DailyEstimateResult.to_dict()."""
        result = DailyEstimateResult(
            product_name="测试产品",
            product_type="基金",
            current_value=Decimal("10000"),
            estimated_daily_return=Decimal("10"),
            estimated_daily_return_rate=Decimal("0.001"),
            expected_annual_return=Decimal("0.04"),
            market_sensitivity=Decimal("0.8"),
            risk_level="中风险",
        )
        d = result.to_dict()
        assert d["product_name"] == "测试产品"
        assert d["product_type"] == "基金"
        assert d["current_value"] == 10000.0
        assert d["estimated_daily_return"] == 10.0
        assert d["estimated_daily_return_rate"] == 0.001
        assert d["expected_annual_return"] == 0.04
        assert d["market_sensitivity"] == 0.8
        assert d["risk_level"] == "中风险"

    def test_to_dict_without_risk_level(self):
        """Test DailyEstimateResult.to_dict() without risk level."""
        result = DailyEstimateResult(
            product_name="测试产品",
            product_type="基金",
            current_value=Decimal("10000"),
            estimated_daily_return=Decimal("10"),
            estimated_daily_return_rate=Decimal("0.001"),
            expected_annual_return=Decimal("0.04"),
            market_sensitivity=Decimal("0.8"),
        )
        d = result.to_dict()
        assert d["risk_level"] is None


class TestGetExpectedAnnualReturn:
    """Test get_expected_annual_return function."""

    def test_bond(self):
        """Test bond type."""
        assert get_expected_annual_return("债券") == Decimal("0.02")
        assert get_expected_annual_return("债券基金") == Decimal("0.02")
        assert get_expected_annual_return("bond") == Decimal("0.02")

    def test_gold(self):
        """Test gold type."""
        assert get_expected_annual_return("黄金") == Decimal("0.05")
        assert get_expected_annual_return("黄金ETF") == Decimal("0.05")
        assert get_expected_annual_return("Gold") == Decimal("0.05")

    def test_currency(self):
        """Test currency type."""
        assert get_expected_annual_return("货币基金") == Decimal("0.005")
        assert get_expected_annual_return("currency") == Decimal("0.005")

    def test_high_end_wealth(self):
        """Test high end wealth type."""
        assert get_expected_annual_return("高端理财") == Decimal("0.03")

    def test_financial(self):
        """Test financial type."""
        assert get_expected_annual_return("理财产品") == Decimal("0.02")
        assert get_expected_annual_return("financial") == Decimal("0.02")

    def test_us_stock(self):
        """Test US stock type."""
        assert get_expected_annual_return("美股") == Decimal("0.05")
        assert get_expected_annual_return("QDII基金") == Decimal("0.05")
        assert get_expected_annual_return("us_equity") == Decimal("0.05")

    def test_fund(self):
        """Test fund type."""
        assert get_expected_annual_return("基金") == Decimal("0.04")
        assert get_expected_annual_return("fund") == Decimal("0.04")

    def test_dividend(self):
        """Test dividend type."""
        assert get_expected_annual_return("股息") == Decimal("0.03")

    def test_unknown(self):
        """Test unknown type."""
        assert get_expected_annual_return("未知类型") == Decimal("0.02")
        assert get_expected_annual_return("unknown") == Decimal("0.02")


class TestGetMarketSensitivity:
    """Test get_market_sensitivity function."""

    def test_bond(self):
        """Test bond sensitivity."""
        assert get_market_sensitivity("债券") == Decimal("-0.3")
        assert get_market_sensitivity("债券基金") == Decimal("-0.3")

    def test_gold(self):
        """Test gold sensitivity."""
        assert get_market_sensitivity("黄金") == Decimal("0.5")

    def test_currency(self):
        """Test currency sensitivity."""
        assert get_market_sensitivity("货币基金") == Decimal("0.1")

    def test_high_end_wealth(self):
        """Test high end wealth sensitivity."""
        assert get_market_sensitivity("高端理财") == Decimal("0.5")

    def test_financial(self):
        """Test financial sensitivity."""
        assert get_market_sensitivity("理财产品") == Decimal("0.2")

    def test_us_stock(self):
        """Test US stock sensitivity."""
        assert get_market_sensitivity("美股") == Decimal("0.9")
        assert get_market_sensitivity("QDII基金") == Decimal("0.9")

    def test_fund(self):
        """Test fund sensitivity."""
        assert get_market_sensitivity("基金") == Decimal("0.8")

    def test_dividend(self):
        """Test dividend sensitivity."""
        assert get_market_sensitivity("股息") == Decimal("0.6")

    def test_unknown(self):
        """Test unknown sensitivity."""
        assert get_market_sensitivity("未知类型") == Decimal("0.3")


class TestGetAdjustedMarketSensitivity:
    """Test get_adjusted_market_sensitivity function."""

    def test_currency_zero_sensitivity(self):
        """Test currency returns zero sensitivity."""
        assert get_adjusted_market_sensitivity("货币基金", "测试") == Decimal("0")

    def test_low_risk(self):
        """Test low risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "低风险")
        assert result == Decimal("0.08")

    def test_stable_risk(self):
        """Test stable risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "稳健")
        assert result == Decimal("0.08")

    def test_conservative_risk(self):
        """Test conservative risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "保守")
        assert result == Decimal("0.08")

    def test_medium_low_risk(self):
        """Test medium low risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "中低")
        assert result == Decimal("0.24")

    def test_medium_risk(self):
        """Test medium risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "中风险")
        assert result == Decimal("0.48")

    def test_medium_high_risk(self):
        """Test medium high risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "中高风险")
        assert result == Decimal("0.64")

    def test_high_risk(self):
        """Test high risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "高风险")
        assert result == Decimal("0.8")

    def test_aggressive_risk(self):
        """Test aggressive risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", "进取")
        assert result == Decimal("0.8")

    def test_no_risk_level(self):
        """Test no risk level."""
        result = get_adjusted_market_sensitivity("基金", "测试", None)
        assert result == Decimal("0.4")


class TestEstimateProductReturn:
    """Test estimate_product_return function."""

    def test_estimate_with_valid_product(self):
        """Test estimate with valid product."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("8000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is not None
        assert result.product_name == "测试基金"
        assert result.product_type == "指数基金"
        assert result.current_value == Decimal("10000")
        assert result.estimated_daily_return > 0

    def test_estimate_with_zero_amount(self):
        """Test estimate with zero amount returns None."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("0"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is None

    def test_estimate_with_negative_amount(self):
        """Test estimate with negative amount returns None."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("-1000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is None

    def test_estimate_with_none_amount(self):
        """Test estimate with None amount returns None."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is None

    def test_estimate_with_market_change(self):
        """Test estimate with market change."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("8000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product, market_change=Decimal("0.01"))
        assert result is not None
        assert result.estimated_daily_return > 0

    def test_estimate_weekly(self):
        """Test weekly estimate."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            initial_amount=Decimal("8000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product, is_weekly=True)
        assert result is not None
        assert result.estimated_daily_return > 0

    def test_estimate_without_investment_type(self):
        """Test estimate without investment type."""
        product = InvestmentProduct(
            investment_type=None,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is not None
        assert result.product_type == "未知"

    def test_estimate_without_risk_level(self):
        """Test estimate without risk level."""
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试基金",
            risk_level=None,
            current_amount=Decimal("10000"),
            start_date="2024-01-01",
        )
        result = estimate_product_return(product)
        assert result is not None
        assert result.risk_level is None


class TestEstimateAllProducts:
    """Test estimate_all_products function."""

    def test_estimate_multiple_products(self):
        """Test estimate with multiple products."""
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="基金1",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                start_date="2024-01-01",
            ),
            InvestmentProduct(
                investment_type=InvestmentType.BOND,
                name="债券1",
                risk_level=RiskLevel.LOW,
                current_amount=Decimal("20000"),
                start_date="2024-01-01",
            ),
        ]
        results = estimate_all_products(products)
        assert len(results) == 2
        assert results[0].product_name == "基金1"
        assert results[1].product_name == "债券1"

    def test_estimate_empty_list(self):
        """Test estimate with empty list."""
        results = estimate_all_products([])
        assert len(results) == 0

    def test_estimate_filters_invalid(self):
        """Test estimate filters invalid products."""
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="有效产品",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                start_date="2024-01-01",
            ),
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="无效产品",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("0"),
                start_date="2024-01-01",
            ),
        ]
        results = estimate_all_products(products)
        assert len(results) == 1
        assert results[0].product_name == "有效产品"

    def test_estimate_with_market_change(self):
        """Test estimate all with market change."""
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="基金1",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                start_date="2024-01-01",
            ),
        ]
        results = estimate_all_products(products, market_change=Decimal("0.01"))
        assert len(results) == 1

    def test_estimate_weekly(self):
        """Test estimate all weekly."""
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="基金1",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
                start_date="2024-01-01",
            ),
        ]
        results = estimate_all_products(products, is_weekly=True)
        assert len(results) == 1
