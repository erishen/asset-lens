"""
Tests for models.py
"""

from datetime import date
from decimal import Decimal

import pytest

from asset_lens.data.models import (
    Currency,
    InvestmentProduct,
    InvestmentType,
    Portfolio,
    Platform,
    RiskLevel,
    Transaction,
)


class TestCurrency:
    """Currency 测试"""

    def test_currency_values(self):
        """测试货币类型值"""
        assert Currency.CNY.value == "CNY"
        assert Currency.USD.value == "USD"
        assert Currency.HKD.value == "HKD"
        assert Currency.EUR.value == "EUR"
        assert Currency.JPY.value == "JPY"


class TestInvestmentType:
    """InvestmentType 测试"""

    def test_investment_type_values(self):
        """测试投资类型值"""
        assert InvestmentType.MONETARY.value == "货币"
        assert InvestmentType.STOCK.value == "股票"
        assert InvestmentType.FUND.value == "基金"
        assert InvestmentType.ETF.value == "ETF"


class TestRiskLevel:
    """RiskLevel 测试"""

    def test_risk_level_values(self):
        """测试风险等级值"""
        assert RiskLevel.LOW.value == "低"
        assert RiskLevel.MEDIUM_LOW.value == "中低"
        assert RiskLevel.MEDIUM.value == "中"
        assert RiskLevel.MEDIUM_HIGH.value == "中高"
        assert RiskLevel.HIGH.value == "高"


class TestPlatform:
    """Platform 测试"""

    def test_platform_values(self):
        """测试平台类型值"""
        assert Platform.THIRD_PARTY.value == "第三方平台"
        assert Platform.BANK.value == "银行"
        assert Platform.SECURITIES.value == "证券"
        assert Platform.OTHER.value == "其他"


class TestTransaction:
    """Transaction 测试"""

    def test_transaction_cny(self):
        """测试人民币交易"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("10000"),
            currency=Currency.CNY,
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("10000")

    def test_transaction_usd(self):
        """测试美元交易"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.USD,
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("7200")

    def test_transaction_usd_with_exchange_rate(self):
        """测试美元交易 - 带汇率"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.USD,
            exchange_rate=Decimal("7.0"),
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("7000")

    def test_transaction_hkd(self):
        """测试港币交易"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("10000"),
            currency=Currency.HKD,
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("9200")

    def test_transaction_hkd_with_exchange_rate(self):
        """测试港币交易 - 带汇率"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("10000"),
            currency=Currency.HKD,
            exchange_rate=Decimal("0.90"),
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("9000")

    def test_transaction_other_currency(self):
        """测试其他货币交易"""
        tx = Transaction(
            transaction_date=date(2024, 1, 1),
            action="buy",
            amount=Decimal("1000"),
            currency=Currency.EUR,
        )

        result = tx.to_cny(Decimal("7.2"), Decimal("0.92"))

        assert result == Decimal("1000")


class TestInvestmentProduct:
    """InvestmentProduct 测试"""

    def test_investment_product_creation(self):
        """测试投资产品创建"""
        product = InvestmentProduct(
            name="测试产品",
            investment_type=InvestmentType.FUND,
            platform_amounts={"平台A": Decimal("10000")},
            initial_amount=Decimal("8000"),
            return_rate=Decimal("25.0"),
            annual_return=Decimal("25.0"),
            risk_level=RiskLevel.MEDIUM,
        )

        assert product.name == "测试产品"
        assert product.investment_type == InvestmentType.FUND
        assert product.total_amount == Decimal("10000")
        assert product.initial_amount == Decimal("8000")
        assert product.return_rate == Decimal("25.0")

    def test_investment_product_total_amount(self):
        """测试投资产品总金额"""
        product = InvestmentProduct(
            name="测试产品",
            investment_type=InvestmentType.FUND,
            platform_amounts={
                "平台A": Decimal("10000"),
                "平台B": Decimal("5000"),
            },
            initial_amount=Decimal("12000"),
            return_rate=Decimal("25.0"),
            annual_return=Decimal("25.0"),
            risk_level=RiskLevel.MEDIUM,
        )

        assert product.total_amount == Decimal("15000")


class TestPortfolio:
    """Portfolio 测试"""

    def test_portfolio_creation(self):
        """测试投资组合创建"""
        products = [
            InvestmentProduct(
                name="产品A",
                investment_type=InvestmentType.FUND,
                platform_amounts={"平台A": Decimal("10000")},
                initial_amount=Decimal("8000"),
                return_rate=Decimal("25.0"),
                annual_return=Decimal("25.0"),
                risk_level=RiskLevel.MEDIUM,
            ),
        ]

        portfolio = Portfolio(products=products)

        assert len(portfolio.products) == 1

    def test_portfolio_empty(self):
        """测试空投资组合"""
        portfolio = Portfolio(products=[])

        assert len(portfolio.products) == 0
