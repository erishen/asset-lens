"""
Mock data configuration for asset-lens.
使用 mock 数据进行测试，避免真实网络请求
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests


@pytest.fixture
def mock_env():
    """设置 mock 环境变量"""
    with patch.dict(os.environ, {"PYTEST_USE_MOCK": "true"}):
        yield


@pytest.fixture
def mock_requests_get():
    """Mock requests.get"""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.text = "mock response"
        mock_response.headers = {"Content-type": "application/json"}
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_session():
    """Mock database会话"""
    session = MagicMock()
    session.query.return_value = MagicMock()
    session.add.return_value = None
    session.commit.return_value = None
    session.close.return_value = None
    yield session


@pytest.fixture
def mock_db_manager(mock_session):
    """Mock 数据库管理器"""
    manager = MagicMock()
    manager.get_session.return_value = mock_session
    manager.get_statistics.return_value = {
        "kline_count": 1000,
        "stock_count": 50,
        "latest_date": "2024-01-01",
    }
    yield manager
