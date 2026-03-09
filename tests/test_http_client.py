"""
Tests for HTTP Client.
HTTP 客户端测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHTTPClient:
    """HTTP 客户端测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.utils.http_client import HTTPClient, http_client, safe_get, safe_post, get_json
        assert HTTPClient is not None
        assert http_client is not None
        assert safe_get is not None
        assert safe_post is not None
        assert get_json is not None

    def test_client_init(self):
        """测试初始化"""
        from asset_lens.utils.http_client import HTTPClient
        
        client = HTTPClient(default_timeout=15, max_retries=5, retry_delay=2.0)
        assert client.default_timeout == 15
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    @patch('asset_lens.utils.http_client.requests.request')
    def test_get_success(self, mock_request):
        """测试 GET 请求成功"""
        from asset_lens.utils.http_client import HTTPClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = HTTPClient()
        response = client.get("https://example.com/api")
        
        assert response is not None
        mock_request.assert_called_once()

    @patch('asset_lens.utils.http_client.requests.request')
    def test_get_timeout_retry(self, mock_request):
        """测试 GET 请求超时重试"""
        from asset_lens.utils.http_client import HTTPClient
        from requests.exceptions import Timeout
        
        # 第一次超时，第二次成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.side_effect = [Timeout(), mock_response]
        
        client = HTTPClient(max_retries=3)
        response = client.get("https://example.com/api")
        
        assert response is not None
        assert mock_request.call_count == 2

    @patch('asset_lens.utils.http_client.requests.request')
    def test_get_json_success(self, mock_request):
        """测试 GET JSON 成功"""
        from asset_lens.utils.http_client import HTTPClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        client = HTTPClient()
        data = client.get_json("https://example.com/api")
        
        assert data == {"data": "test"}

    @patch('asset_lens.utils.http_client.requests.request')
    def test_post_success(self, mock_request):
        """测试 POST 请求成功"""
        from asset_lens.utils.http_client import HTTPClient
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = HTTPClient()
        response = client.post("https://example.com/api", json={"key": "value"})
        
        assert response is not None


class TestSafeFunctions:
    """安全函数测试"""

    @patch('asset_lens.utils.http_client.requests.request')
    def test_safe_get(self, mock_request):
        """测试 safe_get"""
        from asset_lens.utils.http_client import safe_get
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        response = safe_get("https://example.com/api")
        assert response is not None

    @patch('asset_lens.utils.http_client.requests.request')
    def test_safe_post(self, mock_request):
        """测试 safe_post"""
        from asset_lens.utils.http_client import safe_post
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        response = safe_post("https://example.com/api", json={"key": "value"})
        assert response is not None

    @patch('asset_lens.utils.http_client.requests.request')
    def test_get_json(self, mock_request):
        """测试 get_json"""
        from asset_lens.utils.http_client import get_json
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        data = get_json("https://example.com/api")
        assert data == {"data": "test"}
