"""
Tests for Enhanced Data Fetcher.
增强版数据获取模块测试
"""

import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.data_fetcher_enhanced import (
    EnhancedDataFetcher,
    _disable_proxy,
    enhanced_fetcher,
    retry_with_backoff,
)


class TestRetryWithBackoff:
    """测试重试装饰器"""

    def test_success_on_first_try(self):
        """第一次就成功"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_success_on_second_try(self):
        """第二次成功"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt failed")
            return "success"

        result = retry_func()
        assert result == "success"
        assert call_count == 2

    def test_all_retries_fail(self):
        """所有重试都失败"""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fail()

        assert call_count == 2


class TestDisableProxy:
    """测试代理禁用上下文管理器"""

    def test_disable_proxy_removes_env(self, monkeypatch):
        """测试代理环境变量被移除"""
        monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy:8080")

        assert os.environ.get("HTTP_PROXY") == "http://proxy:8080"

        with _disable_proxy():
            assert os.environ.get("HTTP_PROXY") is None
            assert os.environ.get("HTTPS_PROXY") is None

        assert os.environ.get("HTTP_PROXY") == "http://proxy:8080"

    def test_disable_proxy_no_proxy_set(self):
        """没有设置代理时正常工作"""
        with _disable_proxy():
            pass


class TestEnhancedDataFetcher:
    """测试增强版数据获取器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)
        assert fetcher.cache_path == tmp_path
        assert fetcher.market_stock_cache_file == tmp_path / "market_stocks.json"

    def test_get_cached_stocks_no_cache(self, tmp_path):
        """没有缓存时返回 None"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)
        result = fetcher.get_cached_stocks()
        assert result is None

    def test_get_cached_stocks_valid(self, tmp_path):
        """有效缓存返回数据"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)

        cache_data = {
            "stocks": [{"code": "sh600000", "name": "浦发银行"}],
            "update_time": datetime.now().isoformat(),
        }

        with open(fetcher.market_stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.get_cached_stocks()
        assert result is not None
        assert len(result) == 1
        assert result[0]["code"] == "sh600000"

    def test_get_cached_stocks_expired(self, tmp_path):
        """过期缓存返回 None"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)

        old_time = datetime(2020, 1, 1).isoformat()
        cache_data = {
            "stocks": [{"code": "sh600000", "name": "浦发银行"}],
            "update_time": old_time,
        }

        with open(fetcher.market_stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher.get_cached_stocks(max_age_hours=24)
        assert result is None

    def test_save_to_cache(self, tmp_path):
        """测试保存缓存"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)

        stocks = [{"code": "sh600000", "name": "浦发银行"}]
        fetcher.save_to_cache(stocks)

        assert fetcher.market_stock_cache_file.exists()

        with open(fetcher.market_stock_cache_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["count"] == 1
        assert len(data["stocks"]) == 1

    @patch("requests.get")
    def test_fetch_from_tencent_success(self, mock_get, tmp_path):
        """测试腾讯财经获取成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'v_sh600000="1~浦发银行~600000~9.45~9.54"'
        mock_get.return_value = mock_response

        fetcher = EnhancedDataFetcher(cache_path=tmp_path)

        with patch.dict(os.environ, {"HTTP_PROXY": "http://proxy:8080"}):
            result = fetcher._fetch_from_tencent()

        assert result is not None
        assert result[0]["source"] == "tencent"

    @patch("requests.get")
    def test_fetch_from_sina_success(self, mock_get, tmp_path):
        """测试新浪财经获取成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'var hq_str_sh600000="浦发银行,9.45,9.54"'
        mock_get.return_value = mock_response

        fetcher = EnhancedDataFetcher(cache_path=tmp_path)
        result = fetcher._fetch_from_sina()

        assert result is not None
        assert result[0]["source"] == "sina"

    @patch("requests.get")
    def test_fetch_from_eastmoney_success(self, mock_get, tmp_path):
        """测试东方财富获取成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"diff": [{"f12": "600000", "f14": "浦发银行"}]}}
        mock_get.return_value = mock_response

        fetcher = EnhancedDataFetcher(cache_path=tmp_path)
        result = fetcher._fetch_from_eastmoney()

        assert result is not None
        assert result[0]["source"] == "eastmoney"

    def test_fetch_with_fallback_uses_cache(self, tmp_path):
        """测试降级使用缓存"""
        fetcher = EnhancedDataFetcher(cache_path=tmp_path)

        cache_data = {
            "stocks": [{"code": "sh600000", "name": "浦发银行"}],
            "update_time": datetime.now().isoformat(),
        }

        with open(fetcher.market_stock_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        with patch.object(fetcher, "_fetch_from_tencent", side_effect=Exception("Network error")):
            with patch.object(fetcher, "_fetch_from_sina", side_effect=Exception("Network error")):
                with patch.object(fetcher, "_fetch_from_eastmoney", side_effect=Exception("Network error")):
                    result = fetcher.fetch_with_fallback(use_cache=True)

        assert len(result) == 1


class TestEnhancedFetcherInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert enhanced_fetcher is not None
        assert isinstance(enhanced_fetcher, EnhancedDataFetcher)
