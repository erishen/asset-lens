import pytest

from asset_lens.analysis.trade_logger import (
    DecisionBasis,
    EnhancedTradeLog,
    EnhancedTradeLogger,
    LogTradeAction,
    LogTradeResult,
    TradeContext,
    TradeSource,
)


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "trade_logger_test"


@pytest.fixture
def logger(tmp_cache):
    return EnhancedTradeLogger(cache_path=tmp_cache)


@pytest.fixture
def sample_context():
    return TradeContext(
        market_trend="上涨",
        market_change=1.5,
        sentiment="乐观",
        volatility=0.8,
        index_name="沪深300",
    )


@pytest.fixture
def sample_decision():
    return DecisionBasis(
        strategy_name="momentum",
        strategy_score=0.75,
        ml_prediction=0.8,
        ml_direction="up",
        ai_confidence=0.7,
        ai_action="buy",
        signals=["signal1"],
        reasons=["reason1"],
    )


class TestTradeContextToDict:
    def test_to_dict(self, sample_context):
        d = sample_context.to_dict()
        assert d["market_trend"] == "上涨"
        assert d["market_change"] == 1.5
        assert d["sentiment"] == "乐观"
        assert d["volatility"] == 0.8
        assert d["index_name"] == "沪深300"
        assert "timestamp" in d


class TestDecisionBasisToDict:
    def test_to_dict(self, sample_decision):
        d = sample_decision.to_dict()
        assert d["strategy_name"] == "momentum"
        assert d["strategy_score"] == 0.75
        assert d["ml_prediction"] == 0.8
        assert d["ml_direction"] == "up"
        assert d["ai_confidence"] == 0.7
        assert d["ai_action"] == "buy"
        assert d["signals"] == ["signal1"]
        assert d["reasons"] == ["reason1"]


class TestLogTrade:
    def test_log_trade(self, logger, sample_context, sample_decision):
        log = logger.log_trade(
            code="000001",
            name="平安银行",
            action=LogTradeAction.BUY,
            source=TradeSource.AUTO,
            result=LogTradeResult.SUCCESS,
            price=10.0,
            shares=100,
            context=sample_context,
            decision=sample_decision,
        )
        assert log.code == "000001"
        assert log.action == LogTradeAction.BUY
        assert log.amount == 1000.0
        assert log.id.startswith("20")

    def test_log_trade_with_tags(self, logger, sample_context, sample_decision):
        log = logger.log_trade(
            code="000001",
            name="平安银行",
            action=LogTradeAction.BUY,
            source=TradeSource.MANUAL,
            result=LogTradeResult.SUCCESS,
            price=10.0,
            shares=100,
            context=sample_context,
            decision=sample_decision,
            tags=["test", "momentum"],
        )
        assert log.tags == ["test", "momentum"]

    def test_log_trade_with_notes(self, logger, sample_context, sample_decision):
        log = logger.log_trade(
            code="000001",
            name="平安银行",
            action=LogTradeAction.SELL,
            source=TradeSource.SIGNAL,
            result=LogTradeResult.SUCCESS,
            price=15.0,
            shares=50,
            context=sample_context,
            decision=sample_decision,
            notes="止盈卖出",
        )
        assert log.notes == "止盈卖出"


class TestLogBuy:
    def test_log_buy_default_context(self, logger):
        log = logger.log_buy(code="000001", name="平安银行", price=10.0, shares=100)
        assert log.action == LogTradeAction.BUY
        assert log.result == LogTradeResult.SUCCESS
        assert log.source == TradeSource.AUTO
        assert log.context.market_trend == "未知"
        assert log.decision.strategy_name == "default"

    def test_log_buy_custom_context(self, logger, sample_context, sample_decision):
        log = logger.log_buy(
            code="000001",
            name="平安银行",
            price=10.0,
            shares=100,
            source=TradeSource.ML,
            context=sample_context,
            decision=sample_decision,
        )
        assert log.source == TradeSource.ML
        assert log.context.market_trend == "上涨"


class TestLogSell:
    def test_log_sell_default_context(self, logger):
        log = logger.log_sell(code="000001", name="平安银行", price=15.0, shares=100)
        assert log.action == LogTradeAction.SELL
        assert log.result == LogTradeResult.SUCCESS

    def test_log_sell_custom_context(self, logger, sample_context, sample_decision):
        log = logger.log_sell(
            code="000001",
            name="平安银行",
            price=15.0,
            shares=50,
            source=TradeSource.AI,
            context=sample_context,
            decision=sample_decision,
        )
        assert log.source == TradeSource.AI


class TestGetStatistics:
    def test_empty_logs(self, logger):
        stats = logger.get_statistics()
        assert stats.total_trades == 0
        assert stats.buy_count == 0
        assert stats.sell_count == 0

    def test_with_trades(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001", name="A", price=10.0, shares=100, context=sample_context, decision=sample_decision
        )
        logger.log_sell(
            code="000001", name="A", price=15.0, shares=100, context=sample_context, decision=sample_decision
        )
        stats = logger.get_statistics()
        assert stats.total_trades == 2
        assert stats.buy_count == 1
        assert stats.sell_count == 1
        assert stats.total_amount > 0


class TestGetRecentLogs:
    def test_empty(self, logger):
        logs = logger.get_recent_logs()
        assert logs == []

    def test_returns_logs(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001", name="A", price=10.0, shares=100, context=sample_context, decision=sample_decision
        )
        logs = logger.get_recent_logs()
        assert len(logs) >= 1


class TestSearchLogs:
    def test_search_by_code(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001", name="A", price=10.0, shares=100, context=sample_context, decision=sample_decision
        )
        logger.log_buy(code="000002", name="B", price=20.0, shares=50, context=sample_context, decision=sample_decision)
        results = logger.search_logs(code="000001")
        assert all(r["code"] == "000001" for r in results)

    def test_search_by_action(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001", name="A", price=10.0, shares=100, context=sample_context, decision=sample_decision
        )
        logger.log_sell(
            code="000001", name="A", price=15.0, shares=100, context=sample_context, decision=sample_decision
        )
        results = logger.search_logs(action=LogTradeAction.BUY)
        assert all(r["action"] == "buy" for r in results)

    def test_search_by_source(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001",
            name="A",
            price=10.0,
            shares=100,
            source=TradeSource.ML,
            context=sample_context,
            decision=sample_decision,
        )
        results = logger.search_logs(source=TradeSource.ML)
        assert all(r["source"] == "ml" for r in results)

    def test_search_no_results(self, logger):
        results = logger.search_logs(code="999999")
        assert results == []


class TestEnhancedTradeLogToDict:
    def test_to_dict(self, sample_context, sample_decision):
        log = EnhancedTradeLog(
            id="20260101120000_000001",
            code="000001",
            name="平安银行",
            action=LogTradeAction.BUY,
            source=TradeSource.AUTO,
            result=LogTradeResult.SUCCESS,
            price=10.0,
            shares=100,
            amount=1000.0,
            context=sample_context,
            decision=sample_decision,
            execution_time=0.5,
            notes="",
            tags=[],
        )
        d = log.to_dict()
        assert d["code"] == "000001"
        assert d["action"] == "buy"
        assert d["amount"] == 1000.0
        assert isinstance(d["context"], dict)
        assert isinstance(d["decision"], dict)


class TestFormatStatisticsReport:
    def test_format(self, logger, sample_context, sample_decision):
        logger.log_buy(
            code="000001", name="A", price=10.0, shares=100, context=sample_context, decision=sample_decision
        )
        stats = logger.get_statistics()
        report = logger.format_statistics_report(stats)
        assert "交易日志统计报告" in report
        assert "总交易数" in report


class TestLoadLogsCorrupted:
    def test_corrupted_file(self, tmp_cache):
        cache = tmp_cache / "corrupted"
        logger = EnhancedTradeLogger(cache_path=cache)
        logger.log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.log_file.write_text("not valid json")
        logs = logger._load_logs()
        assert logs == []
