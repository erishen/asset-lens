from datetime import datetime
from unittest.mock import patch

import pytest

from asset_lens.trading.stock_pool_strategy import StockPoolConfig, StockPoolStrategyMixin, StockPosition


class FakeStockPool(StockPoolStrategyMixin):
    def __init__(self):
        self.positions = {}
        self._save_pool_called = False

    def add_stock(self, code, name, price, status, notes):
        self.positions[code] = StockPosition(
            code=code, name=name, buy_price=price, buy_date=datetime.now().strftime("%Y-%m-%d"), status=status, notes=notes
        )

    def remove_stock(self, code, reason=""):
        if code in self.positions:
            del self.positions[code]

    def list_stocks(self):
        result = []
        for code, pos in self.positions.items():
            stock = {"code": code, "name": pos.name, "status": pos.status, "selected_history": pos.selected_history}
            result.append(stock)
        return result

    def _save_pool(self):
        self._save_pool_called = True


@pytest.fixture
def pool():
    return FakeStockPool()


class TestStockPosition:
    def test_default_values(self):
        pos = StockPosition(code="600519", name="贵州茅台", buy_price=1800.0, buy_date="2025-01-01")
        assert pos.shares == 100
        assert pos.current_price == 0.0
        assert pos.status == "watching"
        assert pos.selected_count == 1

    def test_custom_values(self):
        pos = StockPosition(
            code="600519", name="贵州茅台", buy_price=1800.0, buy_date="2025-01-01",
            shares=200, status="holding", notes="test"
        )
        assert pos.shares == 200
        assert pos.status == "holding"


class TestStockPoolConfig:
    def test_default_values(self):
        cfg = StockPoolConfig()
        assert cfg.max_pool_size == 50
        assert cfg.auto_update is True
        assert cfg.min_score == 60.0

    def test_custom_values(self):
        cfg = StockPoolConfig(max_pool_size=30, min_score=70.0)
        assert cfg.max_pool_size == 30
        assert cfg.min_score == 70.0


class TestAddStocksByStrategy:
    def test_add_new_stocks(self, pool):
        stocks = [
            {"code": "600519", "name": "贵州茅台", "strategy_score": 80},
            {"code": "000858", "name": "五粮液", "strategy_score": 75},
        ]
        with patch("asset_lens.strategy.engine.strategy_engine") as mock_engine:
            mock_engine.screen_stocks.return_value = stocks
            result = pool.add_stocks_by_strategy("value", stocks, min_score=60.0, max_stocks=10)

        assert result["added"] == 2
        assert result["updated"] == 0
        assert "600519" in pool.positions
        assert "000858" in pool.positions
        assert pool._save_pool_called

    def test_update_existing_stocks(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        stocks = [{"code": "600519", "name": "贵州茅台", "strategy_score": 85}]
        with patch("asset_lens.strategy.engine.strategy_engine") as mock_engine:
            mock_engine.screen_stocks.return_value = stocks
            result = pool.add_stocks_by_strategy("value", stocks, min_score=60.0, max_stocks=10)

        assert result["added"] == 0
        assert result["updated"] == 1
        assert pool.positions["600519"].selected_count == 2

    def test_auto_remove_low_score(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        pool.add_stock("000858", "五粮液", 0.0, "watching", "test")
        stocks = [{"code": "600519", "name": "贵州茅台", "strategy_score": 80}]
        with patch("asset_lens.strategy.engine.strategy_engine") as mock_engine:
            mock_engine.screen_stocks.return_value = stocks
            result = pool.add_stocks_by_strategy("value", stocks, min_score=60.0, max_stocks=10, auto_remove_low_score=True)

        assert result["removed"] == 1
        assert "000858" not in pool.positions

    def test_max_stocks_limit(self, pool):
        stocks = [
            {"code": f"stock{i}", "name": f"Stock {i}", "strategy_score": 80 + i}
            for i in range(5)
        ]
        with patch("asset_lens.strategy.engine.strategy_engine") as mock_engine:
            mock_engine.screen_stocks.return_value = stocks
            result = pool.add_stocks_by_strategy("value", stocks, max_stocks=3)

        assert result["added"] == 3


class TestGetStrategyTopStocks:
    def test_top_stocks(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        pool.positions["600519"].selected_history = [
            {"date": "2025-01-01", "strategy": "value", "score": 85}
        ]
        pool.add_stock("000858", "五粮液", 0.0, "watching", "test")
        pool.positions["000858"].selected_history = [
            {"date": "2025-01-01", "strategy": "value", "score": 70}
        ]

        result = pool.get_strategy_top_stocks("value", top_n=5)
        assert len(result) == 2
        assert result[0]["strategy_score"] == 85

    def test_no_matching_strategy(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        pool.positions["600519"].selected_history = [
            {"date": "2025-01-01", "strategy": "momentum", "score": 85}
        ]
        result = pool.get_strategy_top_stocks("value")
        assert len(result) == 0


class TestClearStrategyStocks:
    def test_clear(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        pool.positions["600519"].selected_history = [
            {"date": "2025-01-01", "strategy": "value", "score": 85}
        ]
        pool.add_stock("000858", "五粮液", 0.0, "holding", "test")
        pool.positions["000858"].selected_history = [
            {"date": "2025-01-01", "strategy": "value", "score": 70}
        ]

        result = pool.clear_strategy_stocks("value")
        assert result["removed_count"] == 1
        assert "600519" not in pool.positions
        assert "000858" in pool.positions

    def test_clear_no_match(self, pool):
        pool.add_stock("600519", "贵州茅台", 0.0, "watching", "test")
        pool.positions["600519"].selected_history = [
            {"date": "2025-01-01", "strategy": "momentum", "score": 85}
        ]
        result = pool.clear_strategy_stocks("value")
        assert result["removed_count"] == 0
