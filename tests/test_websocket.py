"""
Tests for WebSocket functionality.
WebSocket 功能测试
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestWebSocketHook:
    """useWebSocket Hook 测试"""

    def test_hook_file_exists(self):
        """测试 Hook 文件存在"""
        import os
        hook_path = "web-react/src/hooks/useWebSocket.ts"
        assert os.path.exists(hook_path), f"Hook file not found: {hook_path}"


class TestWebSocketAPI:
    """WebSocket API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app
        return TestClient(app)

    def test_realtime_status_endpoint(self, client):
        """测试实时状态 API"""
        response = client.get("/api/realtime/status")
        assert response.status_code == 200
        data = response.json()
        assert "websocket_connections" in data
        assert "status" in data
        assert "timestamp" in data

    def test_websocket_connection(self, client):
        """测试 WebSocket 连接"""
        with client.websocket_connect("/ws/market") as websocket:
            # 发送 ping
            websocket.send_text(json.dumps({"action": "ping"}))
            # 接收 pong
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_get_market_indexes(self, client):
        """测试 WebSocket 获取市场指数"""
        with client.websocket_connect("/ws/market") as websocket:
            # 请求市场指数
            websocket.send_text(json.dumps({"action": "get_market_indexes"}))
            # 接收响应
            response = websocket.receive_json()
            assert response["type"] == "market_indexes"
            assert "data" in response
            assert "timestamp" in response

    def test_websocket_subscribe(self, client):
        """测试 WebSocket 订阅"""
        with client.websocket_connect("/ws/market") as websocket:
            # 订阅股票
            websocket.send_text(json.dumps({
                "action": "subscribe",
                "codes": ["sh600519", "sz000001"]
            }))
            # 接收确认
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert "codes" in response

    def test_websocket_invalid_json(self, client):
        """测试 WebSocket 无效 JSON"""
        with client.websocket_connect("/ws/market") as websocket:
            # 发送无效 JSON
            websocket.send_text("invalid json")
            # 接收错误响应
            response = websocket.receive_json()
            assert response["type"] == "error"


class TestConnectionManager:
    """ConnectionManager 测试"""

    def test_connection_manager_import(self):
        """测试 ConnectionManager 导入"""
        from asset_lens.web.api import ConnectionManager
        assert ConnectionManager is not None

    def test_connection_manager_init(self):
        """测试 ConnectionManager 初始化"""
        from asset_lens.web.api import ConnectionManager
        manager = ConnectionManager()
        assert manager.active_connections is not None
        assert len(manager.active_connections) == 0


class TestStockPoolAPI:
    """股票池 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app
        return TestClient(app)

    def test_stock_pool_endpoint(self, client):
        """测试股票池 API"""
        response = client.get("/api/stock-pool")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "stocks" in data


class TestPortfolioPerformanceAPI:
    """投资组合收益 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app
        return TestClient(app)

    def test_portfolio_performance_endpoint(self, client):
        """测试投资组合收益 API"""
        response = client.get("/api/portfolio/performance")
        assert response.status_code == 200
        data = response.json()
        # 检查关键字段
        if "error" not in data or data.get("total_current") is not None:
            assert "total_current" in data or "error" in data


class TestPortfolioItemsAPI:
    """投资组合项目 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from asset_lens.web.api import app
        return TestClient(app)

    def test_portfolio_items_endpoint(self, client):
        """测试投资组合项目 API"""
        response = client.get("/api/portfolio/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_portfolio_items_with_type_filter(self, client):
        """测试投资组合项目 API - 类型过滤"""
        response = client.get("/api/portfolio/items?type=基金")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_portfolio_items_with_sort(self, client):
        """测试投资组合项目 API - 排序"""
        response = client.get("/api/portfolio/items?sort_by=profit_rate&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
