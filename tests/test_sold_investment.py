"""
Tests for sold investment analysis.
"""

import pytest
from datetime import date
from decimal import Decimal

from asset_lens.core.sold_investment import (
    SoldInvestmentStats,
    SoldInvestmentDetail,
    SoldInvestmentAnalyzer,
)
from asset_lens.data.models import SellRecord, RiskLevel


class TestSoldInvestmentStats:
    """Test SoldInvestmentStats dataclass"""

    def test_stats_creation(self):
        stats = SoldInvestmentStats(
            total_records=10,
            total_initial=Decimal("100000"),
            total_profit=Decimal("5000"),
            total_return_rate=Decimal("5"),
            positive_count=7,
            negative_count=3,
            avg_holding_days=180.5,
            avg_return_rate=Decimal("2.5"),
        )
        assert stats.total_records == 10
        assert stats.total_initial == Decimal("100000")
        assert stats.total_profit == Decimal("5000")

    def test_stats_to_dict(self):
        stats = SoldInvestmentStats(
            total_records=10,
            total_initial=Decimal("100000"),
            total_profit=Decimal("5000"),
            total_return_rate=Decimal("5"),
            positive_count=7,
            negative_count=3,
            avg_holding_days=180.5,
            avg_return_rate=Decimal("2.5"),
        )
        result = stats.to_dict()
        assert result["总记录数"] == 10
        assert result["总初始投资"] == "100000"
        assert result["总收益率"] == "5.00%"


class TestSoldInvestmentDetail:
    """Test SoldInvestmentDetail dataclass"""

    def test_detail_creation(self):
        detail = SoldInvestmentDetail(
            name="测试产品",
            sell_date=date(2024, 1, 15),
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            return_rate=Decimal("10"),
            holding_days=180,
            annualized_return=Decimal("20"),
            risk_level="中",
        )
        assert detail.name == "测试产品"
        assert detail.sell_date == date(2024, 1, 15)
        assert detail.initial_amount == Decimal("10000")

    def test_detail_to_dict(self):
        detail = SoldInvestmentDetail(
            name="测试产品",
            sell_date=date(2024, 1, 15),
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            return_rate=Decimal("10"),
            holding_days=180,
            annualized_return=Decimal("20"),
            risk_level="中",
        )
        result = detail.to_dict()
        assert result["名称"] == "测试产品"
        assert result["卖出日期"] == "2024-01-15"
        assert result["收益率"] == "10.00%"


class TestSoldInvestmentAnalyzer:
    """Test SoldInvestmentAnalyzer class"""

    def setup_method(self):
        self.analyzer = SoldInvestmentAnalyzer()

    def test_analyze_empty_records(self):
        result = self.analyzer.analyze_sold_investments([])
        assert result["stats"].total_records == 0
        assert len(result["details"]) == 0

    def test_analyze_single_record(self):
        record = SellRecord(
            sell_date=date(2024, 1, 15),
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            return_rate=Decimal("10"),
            investment_days=180,
        )
        result = self.analyzer.analyze_sold_investments([record])
        
        assert result["stats"].total_records == 1
        assert result["stats"].total_initial == Decimal("10000")
        assert result["stats"].total_profit == Decimal("1000")
        assert result["stats"].positive_count == 1
        assert result["stats"].negative_count == 0

    def test_analyze_multiple_records(self):
        records = [
            SellRecord(
                sell_date=date(2024, 1, 15),
                name="产品A",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("1000"),
                return_rate=Decimal("10"),
                investment_days=180,
            ),
            SellRecord(
                sell_date=date(2024, 2, 15),
                name="产品B",
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("5000"),
                profit_amount=Decimal("-200"),
                return_rate=Decimal("-4"),
                investment_days=90,
            ),
        ]
        result = self.analyzer.analyze_sold_investments(records)
        
        assert result["stats"].total_records == 2
        assert result["stats"].total_initial == Decimal("15000")
        assert result["stats"].total_profit == Decimal("800")
        assert result["stats"].positive_count == 1
        assert result["stats"].negative_count == 1

    def test_analyze_by_type(self):
        records = [
            SellRecord(
                sell_date=date(2024, 1, 15),
                name="产品A",
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("500"),
                return_rate=Decimal("5"),
                investment_days=180,
            ),
            SellRecord(
                sell_date=date(2024, 2, 15),
                name="产品B",
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("20000"),
                profit_amount=Decimal("2000"),
                return_rate=Decimal("10"),
                investment_days=365,
            ),
        ]
        result = self.analyzer.analyze_sold_investments(records)
        
        assert "by_type" in result
        assert "risk_stats" in result["by_type"]

    def test_get_top_performers(self):
        details = [
            SoldInvestmentDetail(
                name="产品A",
                sell_date=date(2024, 1, 15),
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("1000"),
                return_rate=Decimal("10"),
                holding_days=180,
                annualized_return=Decimal("20"),
                risk_level="中",
            ),
            SoldInvestmentDetail(
                name="产品B",
                sell_date=date(2024, 2, 15),
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("2000"),
                return_rate=Decimal("20"),
                holding_days=180,
                annualized_return=Decimal("40"),
                risk_level="中",
            ),
        ]
        top = self.analyzer.get_top_performers(details, top_n=2)
        assert len(top) == 2
        assert top[0].name == "产品B"

    def test_get_worst_performers(self):
        details = [
            SoldInvestmentDetail(
                name="产品A",
                sell_date=date(2024, 1, 15),
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("-500"),
                return_rate=Decimal("-5"),
                holding_days=180,
                annualized_return=Decimal("-10"),
                risk_level="中",
            ),
            SoldInvestmentDetail(
                name="产品B",
                sell_date=date(2024, 2, 15),
                initial_amount=Decimal("10000"),
                profit_amount=Decimal("-1000"),
                return_rate=Decimal("-10"),
                holding_days=180,
                annualized_return=Decimal("-20"),
                risk_level="中",
            ),
        ]
        worst = self.analyzer.get_worst_performers(details, top_n=2)
        assert len(worst) == 2
        assert worst[0].name == "产品B"

    def test_annualized_return_calculation(self):
        record = SellRecord(
            sell_date=date(2024, 1, 15),
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            initial_amount=Decimal("10000"),
            profit_amount=Decimal("1000"),
            return_rate=Decimal("10"),
            investment_days=365,
            annual_return=Decimal("10"),  # CSV中的年化收益率
        )
        result = self.analyzer.analyze_sold_investments([record])
        
        detail = result["details"][0]
        assert detail.annualized_return == Decimal("10")
