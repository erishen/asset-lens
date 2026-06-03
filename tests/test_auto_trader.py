import json
from pathlib import Path

import pytest

from asset_lens.trading.auto_trader import AutoTradeAction, AutoTrader, AutoTradeRecord, TradeEvaluation, TradeReason


@pytest.fixture
def trader(tmp_path):
    return AutoTrader(data_dir=tmp_path / "auto_trader_test")


class TestAutoTradeAction:
    def test_values(self):
        assert AutoTradeAction.BUY.value == "buy"
        assert AutoTradeAction.SELL.value == "sell"


class TestTradeReason:
    def test_values(self):
        assert TradeReason.STRATEGY_SIGNAL.value == "strategy_signal"
        assert TradeReason.STOP_LOSS.value == "stop_loss"
        assert TradeReason.TAKE_PROFIT.value == "take_profit"
        assert TradeReason.MANUAL.value == "manual"
        assert TradeReason.REBALANCE.value == "rebalance"


class TestAutoTradeRecord:
    def test_creation(self):
        record = AutoTradeRecord(
            id="TRD001",
            timestamp="2025-01-01T10:00:00",
            action=AutoTradeAction.BUY,
            code="600519",
            name="贵州茅台",
            price=1800.0,
            shares=100,
            amount=180000.0,
            reason=TradeReason.STRATEGY_SIGNAL,
            reason_detail="test",
            strategy="momentum",
            market_data={},
            portfolio_state={},
        )
        assert record.id == "TRD001"
        assert record.action == AutoTradeAction.BUY
        assert record.amount == 180000.0


class TestAutoTrader:
    def test_init(self, trader):
        assert trader.data_dir.exists()
        assert isinstance(trader.trades, list)
        assert isinstance(trader.evaluations, list)
        assert isinstance(trader.config, dict)

    def test_default_config(self, trader):
        cfg = trader._default_config()
        assert cfg["strategy"] == "momentum"
        assert cfg["stop_loss_pct"] == -8.0
        assert cfg["take_profit_pct"] == 15.0
        assert cfg["auto_trade"] is False

    def test_generate_trade_id(self, trader):
        tid = trader._generate_trade_id()
        assert tid.startswith("TRD")
        assert len(tid) > 3

    def test_record_buy(self, trader):
        trade = trader.record_buy(
            code="600519",
            name="贵州茅台",
            price=1800.0,
            shares=100,
            reason=TradeReason.STRATEGY_SIGNAL,
        )
        assert trade.action == AutoTradeAction.BUY
        assert trade.code == "600519"
        assert trade.amount == 180000.0
        assert len(trader.trades) == 1

    def test_record_buy_default_reason(self, trader):
        trade = trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        assert trade.reason_detail != ""

    def test_record_sell(self, trader):
        trade = trader.record_sell(
            code="600519",
            name="贵州茅台",
            price=1900.0,
            shares=100,
            reason=TradeReason.TAKE_PROFIT,
        )
        assert trade.action == AutoTradeAction.SELL
        assert trade.amount == 190000.0
        assert len(trader.trades) == 1

    def test_record_sell_with_market_data(self, trader):
        trade = trader.record_sell(
            code="600519",
            name="贵州茅台",
            price=1900.0,
            shares=100,
            market_data={"volume": 10000},
            portfolio_state={"cash": 50000},
        )
        assert trade.market_data == {"volume": 10000}
        assert trade.portfolio_state == {"cash": 50000}

    def test_evaluate_trade(self, trader):
        buy_trade = trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        trade_dict = trader.trades[0]
        eval_result = trader.evaluate_trade(trade_dict["id"], current_price=1900.0)
        assert eval_result is not None
        assert eval_result.is_good_trade is True
        assert eval_result.profit_loss > 0

    def test_evaluate_trade_not_found(self, trader):
        result = trader.evaluate_trade("nonexistent", current_price=100.0)
        assert result is None

    def test_evaluate_sell_trade(self, trader):
        sell_trade = trader.record_sell(code="600519", name="贵州茅台", price=1800.0, shares=100)
        trade_dict = trader.trades[0]
        eval_result = trader.evaluate_trade(trade_dict["id"], current_price=1700.0)
        assert eval_result is not None
        assert eval_result.is_good_trade is True

    def test_auto_evaluate_buy_good(self, trader):
        trade = {"action": "buy"}
        result = trader._auto_evaluate(trade, 12.0, 10)
        assert "优秀" in result

    def test_auto_evaluate_buy_bad(self, trader):
        trade = {"action": "buy"}
        result = trader._auto_evaluate(trade, -8.0, 10)
        assert "反思" in result

    def test_auto_evaluate_sell_good(self, trader):
        trade = {"action": "sell"}
        result = trader._auto_evaluate(trade, -8.0, 10)
        assert "优秀" in result

    def test_auto_evaluate_sell_bad(self, trader):
        trade = {"action": "sell"}
        result = trader._auto_evaluate(trade, 8.0, 10)
        assert "反思" in result

    def test_auto_lessons_short_holding(self, trader):
        trade = {"action": "buy"}
        result = trader._auto_lessons(trade, 5.0, 2)
        assert "频繁" in result

    def test_auto_lessons_default(self, trader):
        trade = {"action": "buy"}
        result = trader._auto_lessons(trade, 1.0, 30)
        assert "观察" in result

    def test_get_trade_history(self, trader):
        trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        trader.record_buy(code="000858", name="五粮液", price=200.0, shares=500)
        assert len(trader.get_trade_history()) == 2
        assert len(trader.get_trade_history(code="600519")) == 1

    def test_get_trade_history_empty(self, trader):
        assert trader.get_trade_history() == []

    def test_get_evaluations(self, trader):
        buy_trade = trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        trade_dict = trader.trades[0]
        trader.evaluate_trade(trade_dict["id"], current_price=1900.0)
        assert len(trader.get_evaluations()) == 1
        assert len(trader.get_evaluations(trade_dict["id"])) == 1

    def test_generate_report(self, trader):
        trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        report = trader.generate_report()
        assert "自动交易系统报告" in report
        assert "600519" in report

    def test_generate_report_empty(self, trader):
        report = trader.generate_report()
        assert "总交易次数: 0" in report

    def test_generate_suggestions_no_evaluations(self, trader):
        result = trader.generate_suggestions()
        assert "暂无" in result

    def test_generate_suggestions_with_evaluations(self, trader):
        buy_trade = trader.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)
        trade_dict = trader.trades[0]
        trader.evaluate_trade(trade_dict["id"], current_price=1900.0)
        result = trader.generate_suggestions()
        assert "策略" in result

    def test_persistence(self, tmp_path):
        trader1 = AutoTrader(data_dir=tmp_path / "persist_test")
        trader1.record_buy(code="600519", name="贵州茅台", price=1800.0, shares=100)

        trader2 = AutoTrader(data_dir=tmp_path / "persist_test")
        assert len(trader2.trades) == 1
        assert trader2.trades[0]["code"] == "600519"
