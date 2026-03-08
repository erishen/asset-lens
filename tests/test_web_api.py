"""
Tests for web/api.py
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from asset_lens.web.api import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestAPIRoot:
    """API 根路径测试"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Asset Lens API"
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestStockAPI:
    """股票 API 测试"""

    def test_get_stock_quote_not_found(self, client):
        """测试获取股票行情 - 未找到"""
        with patch('asset_lens.data.multi_source_fetcher.multi_source_fetcher') as mock_fetcher:
            mock_fetcher.fetch_stock_quote.return_value = None

            response = client.get("/api/stock/quote/invalid")

            assert response.status_code == 404

    def test_get_stock_quote_success(self, client):
        """测试获取股票行情 - 成功"""
        with patch('asset_lens.data.multi_source_fetcher.multi_source_fetcher') as mock_fetcher:
            mock_fetcher.fetch_stock_quote.return_value = {
                "code": "sh600519",
                "name": "贵州茅台",
                "current_price": 1800.0,
                "change_percent": 1.5,
                "change_amount": 27.0,
                "volume": 1000000,
                "amount": 1800000000,
                "high": 1820.0,
                "low": 1780.0,
                "open": 1790.0,
                "prev_close": 1773.0,
            }

            response = client.get("/api/stock/quote/sh600519")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "sh600519"
            assert data["name"] == "贵州茅台"

    def test_search_stocks(self, client):
        """测试搜索股票"""
        with patch('asset_lens.data.stock_screener.stock_screener') as mock_screener:
            mock_screener._load_market_stocks.return_value = [
                {"code": "sh600519", "name": "贵州茅台", "market": "A股"},
                {"code": "sh600000", "name": "浦发银行", "market": "A股"},
            ]

            response = client.get("/api/stock/search?keyword=茅台")

            assert response.status_code == 200
            data = response.json()
            assert data["keyword"] == "茅台"
            assert data["count"] >= 0


class TestPortfolioAPI:
    """投资组合 API 测试"""

    def test_get_portfolio_summary(self, client):
        """测试获取投资组合摘要"""
        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser, \
             patch('asset_lens.config.config') as mock_config:
            mock_parser.load_data.return_value = []
            mock_config.default_usd_rate = 7.2
            mock_config.default_hkd_rate = 0.92

            response = client.get("/api/portfolio/summary")

            assert response.status_code == 200
            data = response.json()
            assert "total_assets" in data
            assert "total_profit" in data
            assert "total_return" in data
            assert "position_count" in data

    def test_get_portfolio_summary_error(self, client):
        """测试获取投资组合摘要 - 错误"""
        with patch('asset_lens.data.csv_parser.CSVParser') as mock_parser:
            mock_parser.load_data.side_effect = Exception("测试错误")

            response = client.get("/api/portfolio/summary")

            assert response.status_code == 500


class TestStrategyAPI:
    """策略 API 测试"""

    def test_list_strategies(self, client):
        """测试获取策略列表"""
        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            mock_engine.list_strategies.return_value = [
                {
                    "name": "value",
                    "description": "价值投资策略",
                    "buy_conditions": 3,
                    "sell_conditions": 2,
                    "position_size": 0.1,
                    "max_positions": 10,
                    "stop_loss": -0.08,
                    "take_profit": 0.15,
                }
            ]

            response = client.get("/api/strategies")

            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert data[0]["name"] == "value"
