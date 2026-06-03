"""
Tests for Web Routes - Stock API.
股票 API 路由测试
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "asset_lens"))

from asset_lens.web.routes.stock import WebStockQuote, router


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestStockQuote:
    """测试股票行情模型"""

    def test_stock_quote_model(self):
        """测试股票行情模型"""
        quote = WebStockQuote(
            code="sh600519",
            name="贵州茅台",
            current_price=1800.0,
            change_percent=2.5,
            change_amount=45.0,
            volume=1000000,
            amount=1800000000,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1755.0,
        )

        assert quote.code == "sh600519"
        assert quote.name == "贵州茅台"
        assert quote.current_price == 1800.0


class TestGetStockQuote:
    """测试获取股票行情"""

    def test_get_stock_quote_success(self, client):
        """测试获取股票行情成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'var hq_str_sh600519="贵州茅台,1790.0,1755.0,1800.0,1820.0,1780.0,1785.0,1800.0,1000000,1800000000,500000,900000,200000,400000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2024-01-01,15:00:00";'

        with patch("asset_lens.utils.http_client.safe_get") as mock_get:
            mock_get.return_value = mock_response

            response = client.get("/api/stock/quote/sh600519")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "sh600519"
            assert data["name"] == "贵州茅台"

    def test_get_stock_quote_not_found(self, client):
        """测试股票不存在"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'var hq_str_sh999999="";'

        with patch("asset_lens.utils.http_client.safe_get") as mock_get:
            mock_get.return_value = mock_response

            response = client.get("/api/stock/quote/sh999999")

            assert response.status_code == 404

    def test_get_stock_quote_service_unavailable(self, client):
        """测试服务不可用"""
        with patch("asset_lens.utils.http_client.safe_get") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/stock/quote/sh600519")

            assert response.status_code == 503


class TestSearchStock:
    """测试搜索股票"""

    def test_search_stock(self, client):
        """测试搜索股票"""
        with patch("asset_lens.strategy.screener.stock_screener") as mock_screener:
            mock_screener._load_market_stocks.return_value = [
                {"code": "sh600519", "name": "贵州茅台", "market": "A股"},
                {"code": "sz000001", "name": "平安银行", "market": "A股"},
            ]

            response = client.get("/api/stock/search?keyword=茅台")

            assert response.status_code == 200
            data = response.json()
            assert data["keyword"] == "茅台"

    def test_search_stock_by_code(self, client):
        """测试按代码搜索股票"""
        with patch("asset_lens.strategy.screener.stock_screener") as mock_screener:
            mock_screener._load_market_stocks.return_value = [
                {"code": "sh600519", "name": "贵州茅台", "market": "A股"},
                {"code": "sz000001", "name": "平安银行", "market": "A股"},
            ]

            response = client.get("/api/stock/search?keyword=600519")

            assert response.status_code == 200


class TestStockKline:
    """测试股票 K 线"""

    def test_get_stock_kline(self, client):
        """测试获取股票 K 线"""
        with patch("asset_lens.web.routes.stock._get_kline_tencent") as mock_kline:
            mock_kline.return_value = [
                {
                    "date": "2024-01-01",
                    "open": 1800.0,
                    "close": 1810.0,
                    "high": 1820.0,
                    "low": 1790.0,
                    "volume": 1000000,
                },
            ]

            response = client.get("/api/stock/kline/sh600519")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "sh600519"

    def test_get_stock_kline_weekly(self, client):
        """测试获取周 K 线"""
        with patch("asset_lens.web.routes.stock._get_kline_tencent") as mock_kline:
            mock_kline.return_value = []

            response = client.get("/api/stock/kline/sh600519?ktype=week")

            assert response.status_code == 200
