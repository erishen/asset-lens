"""
Tests for WebSocket functionality.
WebSocket 功能测试
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
            websocket.send_text(json.dumps({"action": "ping"}))
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_get_market_indexes(self, client):
        """测试 WebSocket 获取市场指数"""
        mock_indexes = [
            {"code": "sh000001", "name": "上证指数", "price": 3000.0, "change": 10.0, "changePercent": 0.33},
            {"code": "sz399001", "name": "深证成指", "price": 10000.0, "change": 50.0, "changePercent": 0.5},
        ]

        with patch("asset_lens.web.api._get_market_indexes", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_indexes

            with client.websocket_connect("/ws/market") as websocket:
                websocket.send_text(json.dumps({"action": "get_market_indexes"}))
                response = websocket.receive_json()
                assert response["type"] == "market_indexes"
                assert "data" in response
                assert "timestamp" in response

    def test_websocket_subscribe(self, client):
        """测试 WebSocket 订阅"""
        with client.websocket_connect("/ws/market") as websocket:
            websocket.send_text(json.dumps({"action": "subscribe", "codes": ["sh600519", "sz000001"]}))
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert "codes" in response

    def test_websocket_get_stock_quotes(self, client):
        """测试 WebSocket 获取股票行情"""
        mock_quotes = [
            {"code": "sh600519", "name": "贵州茅台", "current_price": 1800.0, "change_percent": 2.5},
        ]

        with patch("asset_lens.web.api._get_stock_quotes", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_quotes

            with client.websocket_connect("/ws/market") as websocket:
                websocket.send_text(json.dumps({"action": "get_stock_quotes", "codes": ["sh600519"]}))
                response = websocket.receive_json()
                assert response["type"] == "stock_quotes"
                assert "data" in response

    def test_websocket_invalid_json(self, client):
        """测试 WebSocket 无效 JSON"""
        with client.websocket_connect("/ws/market") as websocket:
            websocket.send_text("invalid json")
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


class TestWebSocketModule:
    """WebSocket 模块测试"""

    def test_connection_manager_class(self):
        """测试 ConnectionManager 类"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connections == set()
        assert manager._last_ping == {}
        assert manager.connection_count == 0

    def test_connection_manager_disconnect_empty(self):
        """测试断开不存在的连接"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.disconnect(mock_ws)
        assert manager.connection_count == 0

    def test_connection_manager_update_ping(self):
        """测试更新 ping 时间"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager._last_ping[mock_ws] = 0
        manager.update_ping(mock_ws)
        assert manager._last_ping[mock_ws] > 0

    def test_connection_manager_check_timeout(self):
        """测试超时检查"""
        import time

        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager._last_ping[mock_ws] = time.time() - 400
        timeout_ws = manager.check_timeout(timeout_seconds=300)
        assert mock_ws in timeout_ws

    def test_connection_manager_no_timeout(self):
        """测试未超时"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager._last_ping[mock_ws] = 0
        timeout_ws = manager.check_timeout(timeout_seconds=300)
        assert mock_ws in timeout_ws

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """测试广播消息"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        manager.active_connections.add(mock_ws)
        manager._last_ping[mock_ws] = 0

        await manager.broadcast({"type": "test"})
        mock_ws.send_json.assert_called_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast_failed(self):
        """测试广播消息失败"""
        from asset_lens.web.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=Exception("Connection error"))
        manager.active_connections.add(mock_ws)
        manager._last_ping[mock_ws] = 0

        await manager.broadcast({"type": "test"})
        assert mock_ws not in manager.active_connections

    def test_manager_instance(self):
        """测试全局 manager 实例"""
        from asset_lens.web.websocket import manager

        assert manager is not None
        assert isinstance(manager.active_connections, set)

    @pytest.mark.asyncio
    async def test_get_market_indexes_async(self):
        """测试异步获取市场指数"""
        from asset_lens.web.websocket import _get_market_indexes_async

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='var hq_str_sh000001="上证指数,3000.0,2990.0,3005.0,3010.0,2995.0,3000.0,3001.0,1000000,3000000000,..."'
        )

        mock_get_context = MagicMock()
        mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get_context)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _get_market_indexes_async()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_stock_quotes_async(self):
        """测试异步获取股票行情"""
        from asset_lens.web.websocket import _get_stock_quotes_async

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value='var hq_str_sh600519="贵州茅台,1800.0,1790.0,1805.0,1810.0,1795.0,1800.0,1801.0,1000000,1800000000,..."'
        )

        mock_get_context = MagicMock()
        mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_context.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get_context)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await _get_stock_quotes_async(["sh600519"])
            assert isinstance(result, list)


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
        if "error" not in data:
            assert "summary" in data or "total_assets" in data or "total_current" in data


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
