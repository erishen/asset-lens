import pytest

from asset_lens.analysis.rebalancer import (
    PortfolioRebalancer,
    RebalanceAction,
    RebalanceHealth,
    RebalanceReason,
    RebalanceReport,
    RebalanceSuggestion,
)


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "rebalancer_test"


@pytest.fixture
def rebalancer(tmp_cache):
    return PortfolioRebalancer(cache_path=tmp_cache)


class TestRebalanceSuggestionToDict:
    def test_to_dict(self):
        s = RebalanceSuggestion(
            code="000001",
            name="平安银行",
            action=RebalanceAction.REDUCE,
            reason=RebalanceReason.STOP_LOSS,
            current_value=10000,
            target_value=5000,
            confidence=0.8,
            description="减仓",
        )
        d = s.to_dict()
        assert d["code"] == "000001"
        assert d["action"] == "reduce"
        assert d["reason"] == "stop_loss"
        assert d["confidence"] == 0.8
        assert "timestamp" in d


class TestAnalyzePortfolio:
    def test_empty_holdings(self, rebalancer):
        health = rebalancer.analyze_portfolio([])
        assert health.overall_score == 0
        assert "无持仓" in health.issues

    def test_healthy_portfolio(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 3000, "profit_rate": 5, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 3000, "profit_rate": 8, "industry": "科技"},
            {"code": "000003", "name": "C", "current_value": 3000, "profit_rate": 3, "industry": "消费"},
            {"code": "000004", "name": "D", "current_value": 3000, "profit_rate": 6, "industry": "医药"},
        ]
        health = rebalancer.analyze_portfolio(holdings)
        assert health.overall_score > 0
        assert health.diversification_score > 0
        assert health.risk_score > 0
        assert health.performance_score > 0
        assert health.efficiency_score > 0

    def test_poor_diversification(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 9000, "profit_rate": 5, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 1000, "profit_rate": -3, "industry": "金融"},
        ]
        health = rebalancer.analyze_portfolio(holdings)
        assert health.diversification_score < 80


class TestGenerateSuggestions:
    def test_empty_holdings(self, rebalancer):
        suggestions = rebalancer.generate_suggestions([])
        assert suggestions == []

    def test_stop_loss(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "profit_rate": -0.10},
        ]
        suggestions = rebalancer.generate_suggestions(holdings)
        assert len(suggestions) >= 1
        assert suggestions[0].action == RebalanceAction.SELL
        assert suggestions[0].reason == RebalanceReason.STOP_LOSS

    def test_take_profit(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "profit_rate": 0.20},
        ]
        suggestions = rebalancer.generate_suggestions(holdings)
        assert any(s.reason == RebalanceReason.TAKE_PROFIT for s in suggestions)

    def test_concentration_risk(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 9000, "profit_rate": 0.05},
            {"code": "000002", "name": "B", "current_value": 1000, "profit_rate": 0.03},
        ]
        suggestions = rebalancer.generate_suggestions(holdings)
        assert any(s.reason == RebalanceReason.RISK_CONTROL for s in suggestions)

    def test_low_performance(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 1000, "profit_rate": -0.06},
            {"code": "000002", "name": "B", "current_value": 2000, "profit_rate": 0.03},
            {"code": "000003", "name": "C", "current_value": 3000, "profit_rate": 0.05},
            {"code": "000004", "name": "D", "current_value": 4000, "profit_rate": 0.02},
            {"code": "000005", "name": "E", "current_value": 5000, "profit_rate": 0.04},
        ]
        stock_scores = {"000001": 30, "000002": 50, "000003": 50, "000004": 50, "000005": 50}
        suggestions = rebalancer.generate_suggestions(holdings, stock_scores=stock_scores)
        assert any(s.reason == RebalanceReason.LOW_PERFORMANCE for s in suggestions)

    def test_opportunity_cost(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 1000, "profit_rate": 0.02},
            {"code": "000002", "name": "B", "current_value": 2000, "profit_rate": 0.03},
            {"code": "000003", "name": "C", "current_value": 3000, "profit_rate": 0.04},
            {"code": "000004", "name": "D", "current_value": 4000, "profit_rate": 0.01},
        ]
        stock_scores = {"000001": 85, "000002": 50, "000003": 50, "000004": 50}
        suggestions = rebalancer.generate_suggestions(holdings, stock_scores=stock_scores)
        assert any(s.reason == RebalanceReason.OPPORTUNITY_COST for s in suggestions)

    def test_no_suggestions_for_stable(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 1000, "profit_rate": 0.05, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 1000, "profit_rate": 0.03, "industry": "科技"},
            {"code": "000003", "name": "C", "current_value": 1000, "profit_rate": 0.07, "industry": "消费"},
            {"code": "000004", "name": "D", "current_value": 1000, "profit_rate": 0.04, "industry": "医药"},
            {"code": "000005", "name": "E", "current_value": 1000, "profit_rate": 0.06, "industry": "能源"},
            {"code": "000006", "name": "F", "current_value": 1000, "profit_rate": 0.02, "industry": "工业"},
        ]
        stock_scores = {"000001": 60, "000002": 55, "000003": 65, "000004": 50, "000005": 55, "000006": 60}
        suggestions = rebalancer.generate_suggestions(holdings, stock_scores=stock_scores)
        assert len(suggestions) == 0


class TestOptimizeIndustryAllocation:
    def test_overconcentrated_industry(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 4000, "industry": "金融"},
            {"code": "000003", "name": "C", "current_value": 1000, "industry": "科技"},
        ]
        suggestions = rebalancer.optimize_industry_allocation(holdings)
        assert "金融" in suggestions
        assert suggestions["金融"].action == RebalanceAction.REDUCE

    def test_balanced_industries(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 3000, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 3000, "industry": "科技"},
            {"code": "000003", "name": "C", "current_value": 3000, "industry": "消费"},
        ]
        suggestions = rebalancer.optimize_industry_allocation(holdings)
        assert len(suggestions) == 0

    def test_empty_holdings(self, rebalancer):
        suggestions = rebalancer.optimize_industry_allocation([])
        assert suggestions == {}


class TestCalculateRiskExposure:
    def test_empty_holdings(self, rebalancer):
        exposure = rebalancer.calculate_risk_exposure([])
        assert exposure["market_risk"] == 0
        assert exposure["industry_risk"] == 0

    def test_basic_exposure(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "profit_rate": -5, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 5000, "profit_rate": 3, "industry": "科技"},
        ]
        exposure = rebalancer.calculate_risk_exposure(holdings)
        assert 0 <= exposure["market_risk"] <= 1
        assert 0 <= exposure["industry_risk"] <= 1
        assert 0 <= exposure["concentration_risk"] <= 1
        assert 0 <= exposure["performance_risk"] <= 1


class TestGenerateReport:
    def test_full_report(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "profit_rate": -0.10, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 5000, "profit_rate": 0.05, "industry": "科技"},
        ]
        report = rebalancer.generate_report(holdings)
        assert isinstance(report, RebalanceReport)
        assert isinstance(report.portfolio_health, RebalanceHealth)
        assert len(report.rebalance_suggestions) > 0
        assert len(report.industry_allocation) > 0
        assert len(report.risk_exposure) > 0

    def test_empty_holdings_report(self, rebalancer):
        report = rebalancer.generate_report([])
        assert report.portfolio_health.overall_score == 0
        assert report.rebalance_suggestions == []


class TestFormatReport:
    def test_format(self, rebalancer):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 5000, "profit_rate": -0.10, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 5000, "profit_rate": 0.05, "industry": "科技"},
        ]
        report = rebalancer.generate_report(holdings)
        text = rebalancer.format_report(report)
        assert "持仓调仓建议报告" in text
        assert "健康度" in text


class TestEstimateImprovement:
    def test_no_suggestions(self, rebalancer):
        health = RebalanceHealth(50, 50, 50, 50, 50, [], [])
        result = rebalancer._estimate_improvement(health, [])
        assert result == 0

    def test_with_suggestions(self, rebalancer):
        health = RebalanceHealth(50, 50, 50, 50, 50, [], [])
        suggestions = [
            RebalanceSuggestion("000001", "A", RebalanceAction.SELL, RebalanceReason.STOP_LOSS, 5000, 0, 0.9, "止损"),
            RebalanceSuggestion(
                "000002", "B", RebalanceAction.REDUCE, RebalanceReason.TAKE_PROFIT, 5000, 2500, 0.8, "减仓"
            ),
        ]
        result = rebalancer._estimate_improvement(health, suggestions)
        assert result > 0

    def test_capped_at_30(self, rebalancer):
        health = RebalanceHealth(50, 50, 50, 50, 50, [], [])
        suggestions = [
            RebalanceSuggestion(f"00{i}", "A", RebalanceAction.SELL, RebalanceReason.STOP_LOSS, 5000, 0, 0.9, "止损")
            for i in range(10)
        ]
        result = rebalancer._estimate_improvement(health, suggestions)
        assert result <= 30
