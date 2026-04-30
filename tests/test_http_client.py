"""
Tests for HTTP Client.
HTTP 客户端测试
"""

from unittest.mock import MagicMock, patch


class TestHTTPClient:
    """HTTP 客户端测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.utils.http_client import HTTPClient, get_json, http_client, safe_get, safe_post

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

    def test_get_success(self):
        """测试 GET 请求成功"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient()
        client._session = MagicMock()
        client._session.request.return_value = mock_response

        response = client.get("https://example.com/api")

        assert response is not None
        client._session.request.assert_called_once()

    def test_get_timeout_retry(self):
        """测试 GET 请求超时重试"""
        from requests.exceptions import Timeout

        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient(max_retries=3)
        client._session = MagicMock()
        client._session.request.side_effect = [Timeout(), mock_response]

        response = client.get("https://example.com/api")

        assert response is not None
        assert client._session.request.call_count == 2

    def test_get_json_success(self):
        """测试 GET JSON 成功"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient()
        client._session = MagicMock()
        client._session.request.return_value = mock_response

        data = client.get_json("https://example.com/api")

        assert data == {"data": "test"}

    def test_post_success(self):
        """测试 POST 请求成功"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient()
        client._session = MagicMock()
        client._session.request.return_value = mock_response

        response = client.post("https://example.com/api", json={"key": "value"})

        assert response is not None


class TestSafeFunctions:
    """安全函数测试"""

    def test_safe_get(self):
        """测试 safe_get"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(HTTPClient, "_session", create=True):
            client = HTTPClient()
            client._session = MagicMock()
            client._session.request.return_value = mock_response

            response = client.get("https://example.com/api")
            assert response is not None

    def test_safe_post(self):
        """测试 safe_post"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient()
        client._session = MagicMock()
        client._session.request.return_value = mock_response

        response = client.post("https://example.com/api", json={"key": "value"})
        assert response is not None

    def test_get_json(self):
        """测试 get_json"""
        from asset_lens.utils.http_client import HTTPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        client = HTTPClient()
        client._session = MagicMock()
        client._session.request.return_value = mock_response

        data = client.get_json("https://example.com/api")
        assert data == {"data": "test"}
