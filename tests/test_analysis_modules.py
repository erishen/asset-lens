"""Smoke tests for asset_lens.analysis untested modules."""

from asset_lens.analysis.black_swan import BlackSwanRiskAlert, BlackSwanRiskLevel, RiskType
from asset_lens.analysis.rebalancer import RebalanceAction, RebalanceReason, RebalanceSuggestion
from asset_lens.analysis.trade_logger import (
    LogTradeAction,
    LogTradeResult,
    TradeContext,
    TradeSource,
)


class TestBlackSwan:
    def test_risk_level_enum(self):
        assert BlackSwanRiskLevel.LOW.value == "low"
        assert BlackSwanRiskLevel.CRITICAL.value == "critical"

    def test_risk_type_enum(self):
        assert RiskType.MARKET_CRASH.value == "market_crash"
        assert RiskType.EXTERNAL_SHOCK.value == "external_shock"

    def test_risk_alert_creation(self):
        alert = BlackSwanRiskAlert(
            risk_type=RiskType.MARKET_CRASH,
            risk_level=BlackSwanRiskLevel.HIGH,
            title="测试预警",
            description="测试描述",
            impact_stocks=["000001"],
            suggested_action="减仓",
        )
        assert alert.title == "测试预警"
        assert alert.risk_level == BlackSwanRiskLevel.HIGH
        d = alert.to_dict()
        assert d["risk_type"] == "market_crash"
        assert d["risk_level"] == "high"


class TestRebalancer:
    def test_rebalance_action_enum(self):
        assert RebalanceAction.REDUCE.value == "reduce"
        assert RebalanceAction.INCREASE.value == "increase"
        assert RebalanceAction.SELL.value == "sell"
        assert RebalanceAction.HOLD.value == "hold"

    def test_rebalance_reason_enum(self):
        assert RebalanceReason.STOP_LOSS.value == "stop_loss"
        assert RebalanceReason.TAKE_PROFIT.value == "take_profit"

    def test_rebalance_suggestion_creation(self):
        suggestion = RebalanceSuggestion(
            code="000001",
            name="平安银行",
            action=RebalanceAction.REDUCE,
            reason=RebalanceReason.STOP_LOSS,
            current_value=10000,
            target_value=5000,
            confidence=0.8,
            description="建议减仓",
        )
        assert suggestion.code == "000001"
        assert suggestion.action == RebalanceAction.REDUCE
        d = suggestion.to_dict()
        assert d["action"] == "reduce"


class TestTradeLogger:
    def test_trade_action_enum(self):
        assert LogTradeAction.BUY.value == "buy"
        assert LogTradeAction.SELL.value == "sell"

    def test_trade_source_enum(self):
        assert TradeSource.MANUAL.value == "manual"
        assert TradeSource.ML.value == "ml"

    def test_trade_result_enum(self):
        assert LogTradeResult.SUCCESS.value == "success"
        assert LogTradeResult.FAILED.value == "failed"

    def test_trade_context_creation(self):
        ctx = TradeContext(
            market_trend="上涨",
            market_change=1.5,
            sentiment="乐观",
            volatility=0.8,
            index_name="沪深300",
        )
        assert ctx.market_trend == "上涨"
        assert ctx.market_change == 1.5
        assert isinstance(ctx.timestamp, str)
