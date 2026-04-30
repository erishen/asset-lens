"""
Tests for Stock Screener.
股票筛选器测试
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestScreenerConfig:
    """筛选器配置测试"""

    def test_fundamental_config_defaults(self):
        """测试基本面配置默认值"""
        from asset_lens.strategy.screener import FundamentalConfig

        config = FundamentalConfig()

        assert config.pe_max == 30.0
        assert config.pe_min == 0.0
        assert config.pb_max == 5.0
        assert config.pb_min == 0.0
        assert config.roe_min == 10.0
        assert config.market_cap_min == 20.0
        assert config.market_cap_max == 1000.0

    def test_technical_config_defaults(self):
        """测试技术面配置默认值"""
        from asset_lens.strategy.screener import TechnicalConfig

        config = TechnicalConfig()

        assert config.ma_trend is True
        assert config.macd_golden_cross is False
        assert config.rsi_oversold is False
        assert config.rsi_min == 30.0
        assert config.rsi_max == 70.0
        assert config.volume_breakout is False
        assert config.volume_ratio_min == 2.0

    def test_scoring_weights_defaults(self):
        """测试评分权重默认值"""
        from asset_lens.strategy.screener import ScoringWeights

        weights = ScoringWeights()

        assert weights.fundamental == 0.4
        assert weights.technical == 0.3
        assert weights.capital_flow == 0.2
        assert weights.industry == 0.1

    def test_screener_config_defaults(self):
        """测试筛选器配置默认值"""
        from asset_lens.strategy.screener import ScreenerConfig

        config = ScreenerConfig()

        assert config.max_results == 20
        assert config.min_score == 60.0


class TestStockScreener:
    """股票筛选器测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def screener(self, temp_cache_path):
        """创建筛选器实例"""
        with patch("asset_lens.strategy.screener.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            from asset_lens.strategy.screener import StockScreener

            screener = StockScreener()
            yield screener

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.strategy.screener import StockScreener

        assert StockScreener is not None

    def test_screener_init(self, screener):
        """测试初始化"""
        assert screener is not None
        assert screener.screener_config is not None

    def test_load_config_no_file(self, screener):
        """测试加载配置 - 文件不存在"""
        config = screener._load_config()
        assert config is not None
        assert config.max_results == 20

    def test_load_config_with_file(self, screener, temp_cache_path):
        """测试加载配置 - 有配置文件"""
        config_path = temp_cache_path / "config" / "stock_screener.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            "max_results": 30,
            "min_score": 70.0,
            "fundamental": {"pe_max": 25.0},
            "technical": {"ma_trend": False},
            "scoring_weights": {"fundamental": 0.5},
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        screener.config_path = config_path
        config = screener._load_config()

        assert config.max_results == 30
        assert config.min_score == 70.0

    def test_load_market_stocks_no_file(self, screener):
        """测试加载市场股票 - 文件不存在"""
        stocks = screener._load_market_stocks()
        assert stocks == []

    def test_load_market_stocks_with_file(self, screener, temp_cache_path):
        """测试加载市场股票 - 有文件"""
        market_file = temp_cache_path / "market_stocks.json"
        market_data = {
            "data": [
                {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 30},
                {"code": "sz000001", "name": "平安银行", "pe_ratio": 8},
            ]
        }

        with open(market_file, "w", encoding="utf-8") as f:
            json.dump(market_data, f)

        stocks = screener._load_market_stocks()
        assert len(stocks) == 2

    def test_filter_by_fundamental(self, screener):
        """测试基本面筛选"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "pe_ratio": 30, "market_cap": 200},
            {"code": "sz000001", "name": "平安银行", "pe_ratio": 8, "market_cap": 150},
            {"code": "sh601318", "name": "中国平安", "pe_ratio": 50, "market_cap": 500},
            {"code": "sh600000", "name": "ST某某", "pe_ratio": 10, "market_cap": 50},
        ]

        results = screener.filter_by_fundamental(stocks)

        assert len(results) <= len(stocks)
        for r in results:
            assert "fundamental_pass" in r
            assert "fundamental_score" in r

    def test_filter_by_fundamental_exclude_st(self, screener):
        """测试基本面筛选 - 排除ST股"""
        stocks = [
            {"code": "sh600000", "name": "ST某某", "pe_ratio": 10, "market_cap": 50},
            {"code": "sh600001", "name": "退市股票", "pe_ratio": 10, "market_cap": 50},
        ]

        results = screener.filter_by_fundamental(stocks)

        assert len(results) == 0

    def test_calculate_fundamental_score(self, screener):
        """测试计算基本面得分"""
        stock = {"pe_ratio": 12, "market_cap": 100, "turnover_rate": 5, "change_percent": 2}

        score = screener._calculate_fundamental_score(stock)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_calculate_fundamental_score_high_pe(self, screener):
        """测试计算基本面得分 - 高PE"""
        stock = {"pe_ratio": 50, "market_cap": 100, "turnover_rate": 5, "change_percent": 2}

        score = screener._calculate_fundamental_score(stock)

        assert score < 80

    def test_calculate_fundamental_score_negative_change(self, screener):
        """测试计算基本面得分 - 负涨幅"""
        stock = {"pe_ratio": 15, "market_cap": 100, "turnover_rate": 5, "change_percent": -8}

        score = screener._calculate_fundamental_score(stock)

        assert "change_percent" in str(score) or score < 100

    def test_filter_by_technical(self, screener):
        """测试技术面筛选"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台"},
        ]

        histories = {"sh600519": {"klines": [{"close": 1800 + i, "volume": 100000 + i * 1000} for i in range(60)]}}

        results = screener.filter_by_technical(stocks, histories)

        assert isinstance(results, list)

    def test_filter_by_technical_no_history(self, screener):
        """测试技术面筛选 - 无历史数据"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台"},
        ]

        results = screener.filter_by_technical(stocks, {})

        assert len(results) == 0

    def test_calculate_technical_score(self, screener):
        """测试计算技术面得分"""
        stock = {"change_percent": 3}
        klines = [{"close": 100 + i, "volume": 100000 + i * 1000} for i in range(20)]

        score = screener._calculate_technical_score(stock, klines)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_check_technical_conditions(self, screener):
        """测试检查技术面条件"""
        from asset_lens.strategy.screener import TechnicalConfig

        stock = {"change_percent": 3}
        klines = [{"close": 100 + i * 0.5, "volume": 100000 + i * 1000} for i in range(60)]
        cfg = TechnicalConfig()

        result = screener._check_technical_conditions(stock, klines, cfg)

        assert isinstance(result, bool)

    def test_calculate_comprehensive_score(self, screener):
        """测试计算综合评分"""
        stock = {"fundamental_score": 70, "technical_score": 80, "turnover_rate": 5, "name": "贵州茅台"}

        result = screener.calculate_comprehensive_score(stock)

        assert "total_score" in result
        assert "fundamental_score" in result
        assert "technical_score" in result
        assert "capital_score" in result
        assert "industry_score" in result

    def test_calculate_comprehensive_score_hot_industry(self, screener):
        """测试计算综合评分 - 热门行业"""
        stock = {"fundamental_score": 70, "technical_score": 80, "turnover_rate": 5, "name": "某某科技"}

        result = screener.calculate_comprehensive_score(stock)

        assert result["industry_score"] == 70

    def test_screen_empty_stocks(self, screener):
        """测试筛选 - 空股票列表"""
        results = screener.screen([])

        assert results == []

    def test_screen_fundamental_only(self, screener):
        """测试筛选 - 仅基本面"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
            },
        ]

        results = screener.screen(stocks, filter_type="fundamental")

        assert isinstance(results, list)

    def test_screen_with_custom_strategy(self, screener):
        """测试自定义策略筛选"""
        stocks = [
            {
                "code": "sh600519",
                "name": "贵州茅台",
                "pe_ratio": 15,
                "market_cap": 200,
                "turnover_rate": 3,
                "change_percent": 2,
                "current_price": 50,
            },
        ]

        strategy = {
            "pe_max": 20,
            "market_cap_min": 50,
            "market_cap_max": 500,
            "turnover_min": 1,
            "turnover_max": 10,
            "change_min": -5,
            "change_max": 5,
            "price_min": 10,
            "price_max": 100,
            "min_match_rate": 0.5,
            "max_results": 10,
        }

        results = screener.screen_with_custom_strategy(stocks, strategy)

        assert isinstance(results, list)

    def test_screen_with_custom_strategy_exclude_st(self, screener):
        """测试自定义策略筛选 - 排除ST"""
        stocks = [
            {
                "code": "sh600000",
                "name": "ST某某",
                "pe_ratio": 10,
                "market_cap": 50,
                "turnover_rate": 3,
                "change_percent": 0,
                "current_price": 20,
            },
        ]

        strategy = {"pe_max": 30}

        results = screener.screen_with_custom_strategy(stocks, strategy)

        assert len(results) == 0


class TestScreenerFilters:
    """筛选条件测试"""

    def test_price_filter(self):
        """测试价格筛选"""
        stocks = [
            {"code": "sh600519", "price": 1800.0},
            {"code": "sz000001", "price": 15.0},
            {"code": "sh601318", "price": 50.0},
        ]

        min_price = 10.0
        max_price = 100.0

        filtered = [s for s in stocks if min_price <= s["price"] <= max_price]
        assert len(filtered) == 2

    def test_volume_filter(self):
        """测试成交量筛选"""
        stocks = [
            {"code": "sh600519", "volume": 1000000},
            {"code": "sz000001", "volume": 5000000},
            {"code": "sh601318", "volume": 3000000},
        ]

        min_volume = 2000000

        filtered = [s for s in stocks if s["volume"] >= min_volume]
        assert len(filtered) == 2

    def test_pe_ratio_filter(self):
        """测试市盈率筛选"""
        stocks = [
            {"code": "sh600519", "pe_ratio": 25.0},
            {"code": "sz000001", "pe_ratio": 8.0},
            {"code": "sh601318", "pe_ratio": 15.0},
        ]

        max_pe = 20.0

        filtered = [s for s in stocks if s["pe_ratio"] <= max_pe]
        assert len(filtered) == 2


class TestScreenerSorting:
    """筛选排序测试"""

    def test_sort_by_price(self):
        """测试按价格排序"""
        stocks = [
            {"code": "sh600519", "price": 1800.0},
            {"code": "sz000001", "price": 15.0},
            {"code": "sh601318", "price": 50.0},
        ]

        sorted_stocks = sorted(stocks, key=lambda x: x["price"], reverse=True)
        assert sorted_stocks[0]["code"] == "sh600519"

    def test_sort_by_volume(self):
        """测试按成交量排序"""
        stocks = [
            {"code": "sh600519", "volume": 1000000},
            {"code": "sz000001", "volume": 5000000},
            {"code": "sh601318", "volume": 3000000},
        ]

        sorted_stocks = sorted(stocks, key=lambda x: x["volume"], reverse=True)
        assert sorted_stocks[0]["code"] == "sz000001"

    def test_sort_by_change(self):
        """测试按涨跌幅排序"""
        stocks = [
            {"code": "sh600519", "change_percent": 1.5},
            {"code": "sz000001", "change_percent": -0.5},
            {"code": "sh601318", "change_percent": 3.0},
        ]

        sorted_stocks = sorted(stocks, key=lambda x: x["change_percent"], reverse=True)
        assert sorted_stocks[0]["code"] == "sh601318"
