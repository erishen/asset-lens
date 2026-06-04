"""
Tests for stock_activity_analyzer.py
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.data.stock_activity_analyzer import ActivityMetrics, ETFPrediction, StockActivityAnalyzer
from asset_lens.data.stock_activity_core import ETF_MAPPING, INDEX_FUND_MAPPING


class TestActivityMetrics:
    """ActivityMetrics 测试"""

    def test_default_values(self):
        """测试默认值"""
        metrics = ActivityMetrics()
        assert metrics.avg_turnover_rate == 0.0
        assert metrics.avg_change_percent == 0.0
        assert metrics.avg_volume == 0.0
        assert metrics.avg_amount == 0.0
        assert metrics.up_count == 0
        assert metrics.down_count == 0
        assert metrics.flat_count == 0
        assert metrics.total_count == 0
        assert metrics.activity_score == 0.0

    def test_custom_values(self):
        """测试自定义值"""
        metrics = ActivityMetrics(
            avg_turnover_rate=2.5,
            avg_change_percent=1.5,
            avg_volume=1000000,
            avg_amount=50000000,
            up_count=100,
            down_count=50,
            flat_count=20,
            total_count=170,
            activity_score=75.0,
        )
        assert metrics.avg_turnover_rate == 2.5
        assert metrics.avg_change_percent == 1.5
        assert metrics.up_count == 100
        assert metrics.activity_score == 75.0


class TestETFPrediction:
    """ETFPrediction 测试"""

    def test_etf_prediction_creation(self):
        """测试 ETF 预测创建"""
        prediction = ETFPrediction(
            etf_name="新能源",
            etf_code="sz516160",
            predicted_change=1.5,
            confidence=0.75,
            activity_score=80.0,
            up_ratio=0.6,
            down_ratio=0.3,
            related_stocks=50,
            top_gainers=[{"name": "股票A", "change_percent": 5.0}],
            top_losers=[{"name": "股票B", "change_percent": -3.0}],
        )
        assert prediction.etf_name == "新能源"
        assert prediction.etf_code == "sz516160"
        assert prediction.predicted_change == 1.5
        assert prediction.confidence == 0.75
        assert prediction.activity_score == 80.0


class TestStockActivityAnalyzer:
    """StockActivityAnalyzer 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def analyzer(self, temp_cache_path):
        """创建测试实例"""
        with patch("asset_lens.data.stock_activity_analyzer.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            analyzer = StockActivityAnalyzer()
            yield analyzer

    def test_init(self, analyzer):
        """测试初始化"""
        assert analyzer.cache_path is not None

    def test_index_fund_mapping(self, analyzer):
        """测试指数基金映射"""
        assert "沪深300" in INDEX_FUND_MAPPING
        assert "中证500" in INDEX_FUND_MAPPING
        assert "创业板" in INDEX_FUND_MAPPING

    def test_etf_mapping(self, analyzer):
        """测试 ETF 映射"""
        assert "新能源" in ETF_MAPPING
        assert "半导体" in ETF_MAPPING
        assert "医药" in ETF_MAPPING
        assert "消费" in ETF_MAPPING
        assert "军工" in ETF_MAPPING

    def test_load_market_stocks_no_file(self, analyzer):
        """测试加载市场股票 - 文件不存在"""
        result = analyzer.load_market_stocks()
        assert result == []

    def test_load_market_stocks_with_file(self, analyzer):
        """测试加载市场股票 - 有文件"""
        data = {
            "data": [
                {"code": "sh600519", "name": "贵州茅台", "change_percent": 1.5},
            ]
        }
        analyzer._cache.save_file("market_stocks.json", data, ttl=86400)

        result = analyzer.load_market_stocks()
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_analyze_activity_empty(self, analyzer):
        """测试分析活跃度 - 空数据"""
        result = analyzer.analyze_activity([])
        assert result.total_count == 0

    def test_analyze_activity_with_data(self, analyzer):
        """测试分析活跃度 - 有数据"""
        stocks = [
            {"name": "股票A", "change_percent": 5.0, "turnover_rate": 3.0, "volume": 1000000, "amount": 50000000},
            {"name": "股票B", "change_percent": -3.0, "turnover_rate": 2.0, "volume": 800000, "amount": 40000000},
            {"name": "股票C", "change_percent": 0.0, "turnover_rate": 1.0, "volume": 500000, "amount": 20000000},
        ]

        result = analyzer.analyze_activity(stocks)

        assert result.total_count == 3
        assert result.up_count == 1
        assert result.down_count == 1
        assert result.flat_count == 1

    def test_analyze_activity_calculation(self, analyzer):
        """测试分析活跃度 - 计算结果"""
        stocks = [
            {"name": "股票A", "change_percent": 2.0, "turnover_rate": 4.0, "volume": 1000000, "amount": 50000000},
            {"name": "股票B", "change_percent": 1.0, "turnover_rate": 2.0, "volume": 500000, "amount": 25000000},
        ]

        result = analyzer.analyze_activity(stocks)

        assert result.avg_change_percent == 1.5
        assert result.avg_turnover_rate == 3.0
        assert result.up_count == 2
