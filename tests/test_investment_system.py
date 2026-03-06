"""
Tests for investment strategy system.
投资策略系统测试
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from asset_lens.data.stock_pool import StockPool, StockPosition, StockPoolConfig
from asset_lens.data.strategy_engine import StrategyEngine, StrategyConfig, StrategyCondition
from asset_lens.data.stock_tracker import StockTracker, TrackerConfig, DailyRecord, MonsterStockSignal
from asset_lens.data.market_environment import MarketEnvironmentAnalyzer, MarketEnvironment


class TestStockPool:
    """股票池测试"""

    def setup_method(self):
        """测试前准备"""
        import time
        self.pool = StockPool(f"test_pool_{int(time.time())}")

    def test_add_stock(self):
        """测试添加股票"""
        result = self.pool.add_stock(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            status="watching",
            notes="测试股票",
            strategy_score=75.0,
        )
        assert result is True
        assert "sh600519" in self.pool.positions
        assert self.pool.positions["sh600519"].selected_count >= 1

    def test_add_stock_cumulative(self):
        """测试累积添加股票"""
        import time
        pool = StockPool(f"test_cumulative_{int(time.time())}")
        pool.add_stock("sh600519", "贵州茅台", 1800.0, "watching", strategy_score=75.0)
        pool.add_stock("sh600519", "贵州茅台", 1850.0, "watching", strategy_score=80.0)

        assert pool.positions["sh600519"].selected_count == 2
        assert len(pool.positions["sh600519"].selected_history) == 2

    def test_buy_stock(self):
        """测试买入股票"""
        self.pool.add_stock("sh600519", "贵州茅台", 1800.0, "watching")
        self.pool.buy_stock("sh600519", 1800.0, 100)

        assert self.pool.positions["sh600519"].status == "holding"
        assert self.pool.positions["sh600519"].buy_price == 1800.0
        assert self.pool.positions["sh600519"].shares == 100

    def test_sell_stock(self):
        """测试卖出股票"""
        self.pool.add_stock("sh600519", "贵州茅台", 1800.0, "watching")
        self.pool.buy_stock("sh600519", 1800.0, 100)
        self.pool.sell_stock("sh600519", 1900.0)

        assert self.pool.positions["sh600519"].status == "sold"
        assert self.pool.positions["sh600519"].sell_price == 1900.0

    def test_get_performance(self):
        """测试获取绩效"""
        self.pool.add_stock("sh600519", "贵州茅台", 1800.0, "watching")
        self.pool.buy_stock("sh600519", 1800.0, 100)
        self.pool.sell_stock("sh600519", 1900.0)

        performance = self.pool.get_performance()
        assert performance["total_stocks"] == 1
        assert performance["sold_count"] == 1
        assert performance["total_profit"] == pytest.approx(10000.0, rel=0.01)


class TestStrategyEngine:
    """策略引擎测试"""

    def test_list_strategies(self):
        """测试列出策略"""
        engine = StrategyEngine()
        strategies = engine.list_strategies()

        assert len(strategies) == 4
        strategy_names = [s["name"] for s in strategies]
        assert "value" in strategy_names
        assert "momentum" in strategy_names
        assert "reversal" in strategy_names
        assert "dividend" in strategy_names

    def test_get_strategy(self):
        """测试获取策略"""
        engine = StrategyEngine()
        strategy = engine.get_strategy("momentum")

        assert strategy is not None
        assert strategy.name == "momentum"
        assert len(strategy.buy_conditions) > 0

    def test_screen_stocks(self):
        """测试筛选股票"""
        engine = StrategyEngine()
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "change_percent": 5.0,
                "turnover_rate": 8.0,
                "volume": 1000000,
                "market_cap": 2000,
                "pe_ratio": 25.0,
            },
            {
                "code": "sh600000",
                "name": "浦发银行",
                "current_price": 10.0,
                "change_percent": 1.0,
                "turnover_rate": 2.0,
                "volume": 500000,
                "market_cap": 300,
                "pe_ratio": 5.0,
            },
        ]

        results = engine.screen_stocks(stocks, "momentum", min_score=0)
        assert isinstance(results, list)


class TestStockTracker:
    """股票跟踪器测试"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = StockTracker("test_pool")
        self.tracker.tracker_path = Path(self.temp_dir)
        self.tracker.tracker_file = self.tracker.tracker_path / "test_tracker.json"

    def test_record_daily(self):
        """测试记录每日数据"""
        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1800.0,
            "change_percent": 5.0,
            "turnover_rate": 8.0,
            "volume": 1000000,
            "amount": 1800000000,
        }

        self.tracker.record_daily(stock_data)

        assert "sh600519" in self.tracker.daily_records
        assert len(self.tracker.daily_records["sh600519"]) == 1

    def test_detect_monster_stocks(self):
        """测试检测妖股"""
        for i in range(5):
            stock_data = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0 + i * 50,
                "change_percent": 9.8,
                "turnover_rate": 10.0,
                "volume": 1000000 * (1 + i * 0.5),
                "amount": 1800000000,
            }
            self.tracker.record_daily(stock_data)

        signals = self.tracker.detect_monster_stocks("sh600519")
        assert isinstance(signals, list)


class TestMarketEnvironment:
    """市场环境分析测试"""

    def test_determine_market_type(self):
        """测试判断市场类型"""
        analyzer = MarketEnvironmentAnalyzer()

        bull_type = analyzer._determine_market_type(15, 12, 25, 2)
        assert bull_type == "bull"

        bear_type = analyzer._determine_market_type(-12, -15, -25, 2)
        assert bear_type == "bear"

        oscillation_type = analyzer._determine_market_type(2, 3, 5, 4)
        assert oscillation_type == "oscillation"

    def test_recommend_strategies(self):
        """测试推荐策略"""
        analyzer = MarketEnvironmentAnalyzer()

        bull_strategies = analyzer._recommend_strategies("bull", 2, "optimistic")
        assert "momentum" in bull_strategies

        bear_strategies = analyzer._recommend_strategies("bear", 2, "pessimistic")
        assert "dividend" in bear_strategies

    def test_adapt_strategy(self):
        """测试策略适配"""
        analyzer = MarketEnvironmentAnalyzer()
        environment = MarketEnvironment(
            date="2026-03-06",
            market_type="bull",
            index_change_5d=5.0,
            index_change_20d=12.0,
            index_change_60d=25.0,
            volatility=2.0,
            volume_trend="increasing",
            sentiment="optimistic",
            hot_sectors=["科技"],
            cold_sectors=["银行"],
            recommended_strategies=["momentum"],
            risk_level="medium",
        )

        adaptation = analyzer.adapt_strategy("momentum", environment)
        assert adaptation.strategy_name == "momentum"
        assert adaptation.expected_performance in ["good", "medium", "poor"]


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """测试前准备"""
        pass

    def test_full_workflow(self):
        """测试完整工作流"""
        pool = StockPool("test_pool")
        engine = StrategyEngine()

        pool.add_stock("sh600519", "贵州茅台", 1800.0, "watching", strategy_score=75.0)
        assert len(pool.positions) == 1

        strategies = engine.list_strategies()
        assert len(strategies) == 4

        pool.buy_stock("sh600519", 1800.0, 100)
        assert pool.positions["sh600519"].status == "holding"

        performance = pool.get_performance()
        assert performance["holding_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
