"""
Tests for data models.
"""

import pytest
from datetime import date
from decimal import Decimal

from asset_lens.data.models import (
    Currency,
    InvestmentType,
    RiskLevel,
    Platform,
    Transaction,
    InvestmentProduct,
    AssetSummary,
    ExchangeRateHistory,
    SellRecord,
    Portfolio,
)


class TestCurrency:
    """Test Currency enum"""

    def test_currency_values(self):
        assert Currency.CNY.value == "CNY"
        assert Currency.USD.value == "USD"
        assert Currency.HKD.value == "HKD"
        assert Currency.EUR.value == "EUR"
        assert Currency.JPY.value == "JPY"

    def test_currency_is_string_enum(self):
        assert isinstance(Currency.CNY, str)
        assert Currency.CNY == "CNY"


class TestInvestmentType:
    """Test InvestmentType enum"""

    def test_investment_type_values(self):
        assert InvestmentType.MONETARY.value == "货币"
        assert InvestmentType.INDEX_FUND.value == "指数基金"
        assert InvestmentType.BOND_FUND.value == "债券基金"
        assert InvestmentType.STOCK.value == "股票"
        assert InvestmentType.OTHER.value == "其他"

    def test_all_investment_types_exist(self):
        types = [
            InvestmentType.MONETARY,
            InvestmentType.INDEX_FUND,
            InvestmentType.BOND_FUND,
            InvestmentType.MIXED_FUND,
            InvestmentType.STOCK,
            InvestmentType.US_STOCK,
            InvestmentType.HK_STOCK,
            InvestmentType.QDII,
            InvestmentType.WEALTH,
            InvestmentType.FIXED_DEPOSIT,
            InvestmentType.BOND,
            InvestmentType.REITS,
            InvestmentType.GOLD,
            InvestmentType.FUND,
            InvestmentType.OTHER,
        ]
        assert len(types) == 15


class TestRiskLevel:
    """Test RiskLevel enum"""

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "低"
        assert RiskLevel.MEDIUM_LOW.value == "中低"
        assert RiskLevel.MEDIUM.value == "中"
        assert RiskLevel.MEDIUM_HIGH.value == "中高"
        assert RiskLevel.HIGH.value == "高"


class TestPlatform:
    """Test Platform enum"""

    def test_platform_values(self):
        assert Platform.WECHAT.value == "微信"
        assert Platform.ALIPAY.value == "支付宝"
        assert Platform.BANK.value == "银行"
        assert Platform.FUND_COMPANY.value == "基金公司"
        assert Platform.SECURITIES.value == "证券"
        assert Platform.OTHER.value == "其他"


class TestTransaction:
    """Test Transaction dataclass"""

    def test_transaction_creation(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="buy",
            amount=Decimal("1000"),
        )
        assert tx.transaction_date == date(2024, 1, 15)
        assert tx.action == "buy"
        assert tx.amount == Decimal("1000")
        assert tx.currency == Currency.CNY
        assert tx.exchange_rate is None

    def test_transaction_with_currency(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="sell",
            amount=Decimal("100"),
            currency=Currency.USD,
            exchange_rate=Decimal("7.2"),
        )
        assert tx.currency == Currency.USD
        assert tx.exchange_rate == Decimal("7.2")

    def test_to_cny_cny(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.CNY,
        )
        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))
        assert result == Decimal("1000")

    def test_to_cny_usd(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="buy",
            amount=Decimal("100"),
            currency=Currency.USD,
            exchange_rate=Decimal("7.2"),
        )
        result = tx.to_cny(Decimal("7.1"), Decimal("0.92"))
        assert result == Decimal("720")

    def test_to_cny_usd_default_rate(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="buy",
            amount=Decimal("100"),
            currency=Currency.USD,
        )
        result = tx.to_cny(Decimal("7.1"), Decimal("0.92"))
        assert result == Decimal("710")

    def test_to_cny_hkd(self):
        tx = Transaction(
            transaction_date=date(2024, 1, 15),
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.HKD,
            exchange_rate=Decimal("0.92"),
        )
        result = tx.to_cny(Decimal("7.2"), Decimal("0.91"))
        assert result == Decimal("920")


class TestInvestmentProduct:
    """Test InvestmentProduct dataclass"""

    def test_product_creation(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="中证500ETF",
            risk_level=RiskLevel.MEDIUM,
        )
        assert product.investment_type == InvestmentType.INDEX_FUND
        assert product.name == "中证500ETF"
        assert product.risk_level == RiskLevel.MEDIUM

    def test_total_amount_wechat_only(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            wechat_amount=Decimal("1000"),
        )
        assert product.total_amount == Decimal("1000")

    def test_total_amount_alipay_only(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            alipay_amount=Decimal("2000"),
        )
        assert product.total_amount == Decimal("2000")

    def test_total_amount_both(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            wechat_amount=Decimal("1000"),
            alipay_amount=Decimal("2000"),
        )
        assert product.total_amount == Decimal("3000")

    def test_total_amount_current_amount(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("5000"),
        )
        assert product.total_amount == Decimal("5000")

    def test_platform_wechat(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            wechat_amount=Decimal("1000"),
        )
        assert product.platform == Platform.WECHAT

    def test_platform_alipay(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            alipay_amount=Decimal("1000"),
        )
        assert product.platform == Platform.ALIPAY

    def test_platform_both(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            wechat_amount=Decimal("1000"),
            alipay_amount=Decimal("1000"),
        )
        assert product.platform == Platform.OTHER

    def test_platform_none(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
        )
        assert product.platform == Platform.OTHER

    def test_to_dict(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="中证500ETF",
            risk_level=RiskLevel.MEDIUM,
            wechat_amount=Decimal("1000"),
            current_amount=Decimal("1200"),
            initial_amount=Decimal("1000"),
            investment_days=365,
            return_rate=Decimal("20"),
        )
        result = product.to_dict()
        assert result["投资类型"] == "指数基金"
        assert result["名称"] == "中证500ETF"
        assert result["风险等级"] == "中"
        assert result["当前金额"] == "1200"
        assert result["投资天数"] == 365


class TestAssetSummary:
    """Test AssetSummary dataclass"""

    def test_asset_summary_creation(self):
        summary = AssetSummary(summary_date=date(2024, 1, 15))
        assert summary.summary_date == date(2024, 1, 15)

    def test_total_platform_amount(self):
        summary = AssetSummary(
            summary_date=date(2024, 1, 15),
            wechat_amount=Decimal("1000"),
            alipay_amount=Decimal("2000"),
            zhaoshang_amount=Decimal("3000"),
        )
        assert summary.total_platform_amount == Decimal("6000")

    def test_total_credit_amount(self):
        summary = AssetSummary(
            summary_date=date(2024, 1, 15),
            credit_card_amount=Decimal("1000"),
            jingdong_white_amount=Decimal("500"),
        )
        assert summary.total_credit_amount == Decimal("1500")

    def test_total_investment_value(self):
        summary = AssetSummary(
            summary_date=date(2024, 1, 15),
            wechat_amount=Decimal("1000"),
            credit_card_amount=Decimal("500"),
            gold_amount=Decimal("200"),
        )
        assert summary.total_investment_value == Decimal("1700")

    def test_to_dict(self):
        summary = AssetSummary(
            summary_date=date(2024, 1, 15),
            wechat_amount=Decimal("1000"),
            usd_rate=Decimal("7.2"),
        )
        result = summary.to_dict()
        assert result["汇总日期"] == "2024-01-15"
        assert result["微信金额"] == "1000"
        assert result["美元汇率"] == "7.2"


class TestExchangeRateHistory:
    """Test ExchangeRateHistory dataclass"""

    def test_exchange_rate_history_creation(self):
        rate = ExchangeRateHistory(
            rate_date=date(2024, 1, 15),
            usd_rate=Decimal("7.2"),
            hkd_rate=Decimal("0.92"),
        )
        assert rate.rate_date == date(2024, 1, 15)
        assert rate.usd_rate == Decimal("7.2")
        assert rate.hkd_rate == Decimal("0.92")

    def test_default_rates(self):
        rate = ExchangeRateHistory(rate_date=date(2024, 1, 15))
        assert rate.usd_rate == Decimal("7.1242")
        assert rate.hkd_rate == Decimal("0.9157")

    def test_to_dict(self):
        rate = ExchangeRateHistory(
            rate_date=date(2024, 1, 15),
            usd_rate=Decimal("7.2"),
            hkd_rate=Decimal("0.92"),
        )
        result = rate.to_dict()
        assert result["汇率日期"] == "2024-01-15"
        assert result["美元汇率"] == "7.2"
        assert result["港元汇率"] == "0.92"


class TestSellRecord:
    """Test SellRecord dataclass"""

    def test_sell_record_creation(self):
        record = SellRecord(
            sell_date=date(2024, 1, 15),
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
        )
        assert record.sell_date == date(2024, 1, 15)
        assert record.name == "测试产品"
        assert record.risk_level == RiskLevel.MEDIUM

    def test_to_dict(self):
        record = SellRecord(
            sell_date=date(2024, 1, 15),
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            initial_amount=Decimal("1000"),
            profit_amount=Decimal("100"),
            return_rate=Decimal("10"),
        )
        result = record.to_dict()
        assert result["卖出日期"] == "2024-01-15"
        assert result["名称"] == "测试产品"
        assert result["风险等级"] == "中"
        assert result["初始金额"] == "1000"


class TestPortfolio:
    """Test Portfolio dataclass"""

    def test_portfolio_creation(self):
        portfolio = Portfolio()
        assert len(portfolio.products) == 0

    def test_add_product(self):
        portfolio = Portfolio()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1000"),
        )
        portfolio.add_product(product)
        assert len(portfolio.products) == 1

    def test_get_by_type(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="指数基金1",
            risk_level=RiskLevel.MEDIUM,
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="债券1",
            risk_level=RiskLevel.LOW,
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        index_funds = portfolio.get_by_type(InvestmentType.INDEX_FUND)
        assert len(index_funds) == 1
        assert index_funds[0].name == "指数基金1"

    def test_get_by_risk(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="产品2",
            risk_level=RiskLevel.LOW,
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        low_risk = portfolio.get_by_risk(RiskLevel.LOW)
        assert len(low_risk) == 1
        assert low_risk[0].name == "产品2"

    def test_total_value(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1000"),
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="产品2",
            risk_level=RiskLevel.LOW,
            current_amount=Decimal("2000"),
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        assert portfolio.total_value == Decimal("3000")

    def test_total_initial(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            initial_amount=Decimal("1000"),
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="产品2",
            risk_level=RiskLevel.LOW,
            initial_amount=Decimal("2000"),
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        assert portfolio.total_initial == Decimal("3000")

    def test_total_profit(self):
        portfolio = Portfolio()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1200"),
            initial_amount=Decimal("1000"),
        )
        portfolio.add_product(product)

        assert portfolio.total_profit == Decimal("200")

    def test_overall_return_rate(self):
        portfolio = Portfolio()
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1200"),
            initial_amount=Decimal("1000"),
        )
        portfolio.add_product(product)

        assert portfolio.overall_return_rate == Decimal("20")

    def test_overall_return_rate_zero_initial(self):
        portfolio = Portfolio()
        assert portfolio.overall_return_rate is None

    def test_get_type_distribution(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1000"),
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品2",
            risk_level=RiskLevel.LOW,
            current_amount=Decimal("1000"),
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        distribution = portfolio.get_type_distribution()
        assert "指数基金" in distribution
        assert distribution["指数基金"]["count"] == 2
        assert distribution["指数基金"]["total_value"] == Decimal("2000")

    def test_get_risk_distribution(self):
        portfolio = Portfolio()
        product1 = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="产品1",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("1000"),
        )
        product2 = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="产品2",
            risk_level=RiskLevel.LOW,
            current_amount=Decimal("2000"),
        )
        portfolio.add_product(product1)
        portfolio.add_product(product2)

        distribution = portfolio.get_risk_distribution()
        assert "中" in distribution
        assert "低" in distribution
        assert distribution["中"]["count"] == 1
        assert distribution["低"]["count"] == 1
