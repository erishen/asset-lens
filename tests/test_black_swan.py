import pytest

from asset_lens.analysis.black_swan import (
    BlackSwanMonitor,
    BlackSwanRiskAlert,
    BlackSwanRiskLevel,
    MarketRiskAssessment,
    RiskType,
)


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "black_swan_test"


@pytest.fixture
def monitor(tmp_cache):
    return BlackSwanMonitor(cache_path=tmp_cache)


class TestBlackSwanRiskAlert:
    def test_to_dict(self):
        alert = BlackSwanRiskAlert(
            risk_type=RiskType.MARKET_CRASH,
            risk_level=BlackSwanRiskLevel.HIGH,
            title="测试",
            description="描述",
            impact_stocks=["000001"],
            suggested_action="减仓",
        )
        d = alert.to_dict()
        assert d["risk_type"] == "market_crash"
        assert d["risk_level"] == "high"
        assert d["title"] == "测试"
        assert d["impact_stocks"] == ["000001"]
        assert "timestamp" in d

    def test_default_timestamp(self):
        alert = BlackSwanRiskAlert(
            risk_type=RiskType.SYSTEMIC_RISK,
            risk_level=BlackSwanRiskLevel.LOW,
            title="t",
            description="d",
            impact_stocks=[],
            suggested_action="a",
        )
        assert len(alert.timestamp) > 0


class TestCheckMarketRisk:
    def test_no_market_data(self, monitor):
        assessment = monitor.check_market_risk()
        assert assessment.overall_risk_level == BlackSwanRiskLevel.LOW
        assert assessment.market_trend == "未知"
        assert len(assessment.risk_alerts) > 0

    def test_panic_selling(self, monitor):
        data = {"index_change": -6.0, "volatility": 1.0, "trend": "暴跌", "sentiment_score": 0.1}
        assessment = monitor.check_market_risk(data)
        assert assessment.overall_risk_level == BlackSwanRiskLevel.CRITICAL
        alert_types = [a.risk_type for a in assessment.risk_alerts]
        assert RiskType.MARKET_CRASH in alert_types

    def test_market_crash(self, monitor):
        data = {"index_change": -4.0, "volatility": 1.0, "trend": "下跌", "sentiment_score": 0.3}
        assessment = monitor.check_market_risk(data)
        assert assessment.overall_risk_level in (
            BlackSwanRiskLevel.HIGH,
            BlackSwanRiskLevel.MEDIUM,
            BlackSwanRiskLevel.CRITICAL,
        )

    def test_high_volatility(self, monitor):
        data = {"index_change": -1.0, "volatility": 5.0, "trend": "震荡", "sentiment_score": 0.4}
        assessment = monitor.check_market_risk(data)
        vol_alerts = [a for a in assessment.risk_alerts if "波动" in a.title]
        assert len(vol_alerts) > 0

    def test_stable_market(self, monitor):
        data = {"index_change": 0.5, "volatility": 0.5, "trend": "上涨", "sentiment_score": 0.7}
        assessment = monitor.check_market_risk(data)
        assert assessment.overall_risk_level == BlackSwanRiskLevel.LOW

    def test_market_data_fields_populated(self, monitor):
        data = {"index_change": 1.0, "volatility": 0.8, "trend": "上涨", "sentiment_score": 0.8}
        assessment = monitor.check_market_risk(data)
        assert assessment.market_trend == "上涨"
        assert assessment.volatility_level == 0.8
        assert assessment.sentiment_score == 0.8


class TestCheckPortfolioRisk:
    def test_empty_holdings(self, monitor):
        alerts = monitor.check_portfolio_risk([])
        assert alerts == []

    def test_losing_positions_majority(self, monitor):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 1000, "profit_rate": -6},
            {"code": "000002", "name": "B", "current_value": 1000, "profit_rate": -8},
            {"code": "000003", "name": "C", "current_value": 1000, "profit_rate": 2},
        ]
        alerts = monitor.check_portfolio_risk(holdings)
        titles = [a.title for a in alerts]
        assert any("大面积亏损" in t for t in titles)

    def test_severe_loss(self, monitor):
        holdings = [
            {"code": "000001", "name": "平安银行", "current_value": 5000, "profit_rate": -20},
        ]
        alerts = monitor.check_portfolio_risk(holdings)
        assert any("严重亏损" in a.title for a in alerts)
        severe = [a for a in alerts if a.risk_level == BlackSwanRiskLevel.CRITICAL]
        assert len(severe) > 0

    def test_concentration_risk(self, monitor):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 8000, "profit_rate": 5},
            {"code": "000002", "name": "B", "current_value": 2000, "profit_rate": 3},
        ]
        alerts = monitor.check_portfolio_risk(holdings)
        assert any("集中度" in a.title for a in alerts)

    def test_no_risk(self, monitor):
        holdings = [
            {"code": "000001", "name": "A", "current_value": 1500, "profit_rate": 5, "industry": "金融"},
            {"code": "000002", "name": "B", "current_value": 1500, "profit_rate": 3, "industry": "科技"},
            {"code": "000003", "name": "C", "current_value": 1500, "profit_rate": 8, "industry": "消费"},
            {"code": "000004", "name": "D", "current_value": 1500, "profit_rate": 2, "industry": "医药"},
        ]
        alerts = monitor.check_portfolio_risk(holdings)
        concentration_alerts = [a for a in alerts if "集中度" in a.title]
        assert len(concentration_alerts) == 0


class TestCheckIndustryRisk:
    def test_industry_decline(self, monitor):
        industry_data = {"科技": {"change": -7}}
        holdings = [
            {"code": "000001", "industry": "科技"},
            {"code": "000002", "industry": "金融"},
        ]
        alerts = monitor.check_industry_risk(industry_data, holdings)
        assert len(alerts) == 1
        assert "科技" in alerts[0].title

    def test_no_affected_stocks(self, monitor):
        industry_data = {"科技": {"change": -7}}
        holdings = [{"code": "000001", "industry": "金融"}]
        alerts = monitor.check_industry_risk(industry_data, holdings)
        assert len(alerts) == 0

    def test_stable_industry(self, monitor):
        industry_data = {"金融": {"change": -2}}
        holdings = [{"code": "000001", "industry": "金融"}]
        alerts = monitor.check_industry_risk(industry_data, holdings)
        assert len(alerts) == 0


class TestCheckExternalRisk:
    def test_high_severity(self, monitor):
        events = [{"title": "地缘冲突", "description": "测试", "severity": "high", "impact_stocks": ["000001"]}]
        alerts = monitor.check_external_risk(events)
        assert len(alerts) == 1
        assert alerts[0].risk_level == BlackSwanRiskLevel.HIGH

    def test_low_severity(self, monitor):
        events = [{"title": "小事件", "description": "测试", "severity": "low"}]
        alerts = monitor.check_external_risk(events)
        assert len(alerts) == 1
        assert alerts[0].risk_level == BlackSwanRiskLevel.MEDIUM

    def test_empty_events(self, monitor):
        alerts = monitor.check_external_risk([])
        assert alerts == []


class TestCalculateOverallRisk:
    def test_no_alerts(self, monitor):
        assert monitor._calculate_overall_risk([]) == BlackSwanRiskLevel.LOW

    def test_critical_alert(self, monitor):
        alerts = [
            BlackSwanRiskAlert(RiskType.MARKET_CRASH, BlackSwanRiskLevel.CRITICAL, "t", "d", [], "a"),
        ]
        assert monitor._calculate_overall_risk(alerts) == BlackSwanRiskLevel.CRITICAL

    def test_two_high_alerts(self, monitor):
        alerts = [
            BlackSwanRiskAlert(RiskType.MARKET_CRASH, BlackSwanRiskLevel.HIGH, "t1", "d1", [], "a1"),
            BlackSwanRiskAlert(RiskType.SYSTEMIC_RISK, BlackSwanRiskLevel.HIGH, "t2", "d2", [], "a2"),
        ]
        assert monitor._calculate_overall_risk(alerts) == BlackSwanRiskLevel.HIGH

    def test_one_high_alert(self, monitor):
        alerts = [
            BlackSwanRiskAlert(RiskType.MARKET_CRASH, BlackSwanRiskLevel.HIGH, "t", "d", [], "a"),
        ]
        assert monitor._calculate_overall_risk(alerts) == BlackSwanRiskLevel.MEDIUM


class TestSaveAndGetAlerts:
    def test_save_and_retrieve(self, monitor):
        alerts = [
            BlackSwanRiskAlert(RiskType.SYSTEMIC_RISK, BlackSwanRiskLevel.LOW, "测试", "描述", [], "操作"),
        ]
        monitor.save_alerts(alerts)
        recent = monitor.get_recent_alerts()
        assert len(recent) >= 1
        assert recent[-1]["title"] == "测试"

    def test_get_recent_alerts_no_file(self, monitor):
        recent = monitor.get_recent_alerts()
        assert recent == []

    def test_get_recent_alerts_limit(self, monitor):
        for i in range(5):
            alerts = [
                BlackSwanRiskAlert(RiskType.SYSTEMIC_RISK, BlackSwanRiskLevel.LOW, f"预警{i}", "描述", [], "操作"),
            ]
            monitor.save_alerts(alerts)
        recent = monitor.get_recent_alerts(limit=3)
        assert len(recent) <= 3

    def test_corrupted_history_file(self, tmp_cache, monitor):
        monitor.history_file.parent.mkdir(parents=True, exist_ok=True)
        monitor.history_file.write_text("not json")
        recent = monitor.get_recent_alerts()
        assert recent == []


class TestFormatAssessment:
    def test_format(self, monitor):
        assessment = MarketRiskAssessment(
            overall_risk_level=BlackSwanRiskLevel.MEDIUM,
            market_trend="震荡",
            volatility_level=2.5,
            sentiment_score=0.5,
            risk_alerts=[
                BlackSwanRiskAlert(RiskType.SYSTEMIC_RISK, BlackSwanRiskLevel.MEDIUM, "波动", "市场波动", [], "观望"),
            ],
            recommendations=["减少交易"],
        )
        report = monitor.format_assessment(assessment)
        assert "黑天鹅风险评估报告" in report
        assert "MEDIUM" in report
        assert "震荡" in report
