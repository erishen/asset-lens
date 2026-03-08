"""
Tests for async_market_data_fetcher.py
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from asset_lens.data.async_market_data_fetcher import AsyncMarketDataFetcher


class TestAsyncMarketDataFetcher:
    """AsyncMarketDataFetcher 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.async_market_data_fetcher.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            fetcher = AsyncMarketDataFetcher()
            yield fetcher

    def test_init(self, fetcher, temp_cache_path):
        """测试初始化"""
        assert fetcher.cache_path == temp_cache_path
        assert fetcher.max_concurrent == 5
        assert fetcher.request_delay == 0.1
        assert fetcher._semaphore is None
        assert fetcher._akshare is None

    def test_init_with_params(self, temp_cache_path):
        """测试带参数初始化"""
        with patch('asset_lens.data.async_market_data_fetcher.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            fetcher = AsyncMarketDataFetcher(max_concurrent=10, request_delay=0.5)
            assert fetcher.max_concurrent == 10
            assert fetcher.request_delay == 0.5

    def test_akshare_lazy_load(self, fetcher):
        """测试 AkShare 延迟加载"""
        mock_ak = MagicMock()
        with patch.dict('sys.modules', {'akshare': mock_ak}):
            ak = fetcher.akshare
            assert ak == mock_ak

    def test_akshare_import_error(self, fetcher):
        """测试 AkShare 未安装"""
        with patch.dict('sys.modules', {'akshare': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module")):
                fetcher._akshare = None
                with pytest.raises(ImportError) as exc_info:
                    _ = fetcher.akshare
                assert "请先安装 AkShare" in str(exc_info.value)

    def test_fetch_domestic_index_sync_success(self, fetcher):
        """测试同步获取国内指数成功"""
        import pandas as pd
        
        mock_df = pd.DataFrame({
            "代码": ["000001"],
            "名称": ["上证指数"],
            "最新价": [3000.0],
            "昨收": [2990.0],
            "今开": [2995.0],
            "最高": [3010.0],
            "最低": [2990.0],
            "成交量": [1000000],
            "成交额": [5000000],
        })

        mock_ak = MagicMock()
        mock_ak.stock_zh_index_spot_em = MagicMock(return_value=mock_df)

        fetcher._akshare = mock_ak

        result = fetcher.fetch_domestic_index_sync("sh000001")

        assert result is not None
        assert result["name"] == "上证指数"
        assert result["current_price"] == 3000.0
        assert result["prev_close"] == 2990.0

    def test_fetch_domestic_index_sync_empty_df(self, fetcher):
        """测试同步获取国内指数 - 空数据"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_index_spot_em = MagicMock(return_value=None)
        fetcher._akshare = mock_ak

        result = fetcher.fetch_domestic_index_sync("sh000001")
        assert result is None

    def test_fetch_domestic_index_sync_exception(self, fetcher):
        """测试同步获取国内指数 - 异常"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_index_spot_em = MagicMock(side_effect=Exception("Network error"))
        fetcher._akshare = mock_ak

        result = fetcher.fetch_domestic_index_sync("sh000001")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_domestic_index_async(self, fetcher):
        """测试异步获取国内指数"""
        fetcher.fetch_domestic_index_sync = MagicMock(return_value={"name": "test"})

        result = await fetcher.fetch_domestic_index_async("sh000001")
        assert result == {"name": "test"}

    @pytest.mark.asyncio
    async def test_fetch_domestic_index_async_with_semaphore(self, fetcher):
        """测试异步获取国内指数 - 带信号量"""
        fetcher._semaphore = asyncio.Semaphore(1)
        fetcher.fetch_domestic_index_sync = MagicMock(return_value={"name": "test"})

        result = await fetcher.fetch_domestic_index_async("sh000001")
        assert result == {"name": "test"}

    def test_load_existing_history_success(self, fetcher, temp_cache_path):
        """测试加载历史数据成功"""
        cache_data = {
            "指数数据": {
                "上证指数": {
                    "历史走势": [
                        {"日期": "2024-01-01", "收盘": 3000}
                    ]
                }
            }
        }

        cache_file = temp_cache_path / "market_index_domestic.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        result = fetcher._load_existing_history()
        assert "上证指数" in result
        assert len(result["上证指数"]) == 1

    def test_load_existing_history_no_file(self, fetcher):
        """测试加载历史数据 - 文件不存在"""
        result = fetcher._load_existing_history()
        assert result == {}

    def test_load_existing_history_exception(self, fetcher, temp_cache_path):
        """测试加载历史数据 - 异常"""
        cache_file = temp_cache_path / "market_index_domestic.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        result = fetcher._load_existing_history()
        assert result == {}

    def test_update_history_new_data(self, fetcher):
        """测试更新历史数据 - 新数据"""
        today_data = {
            "数据日期": "2024-01-02",
            "今开": 3000,
            "最新价": 3010,
            "最高": 3020,
            "最低": 2990,
            "成交量": 1000000,
        }

        result = fetcher._update_history([], today_data)
        assert len(result) == 1
        assert result[0]["日期"] == "2024-01-02"

    def test_update_history_append(self, fetcher):
        """测试更新历史数据 - 追加"""
        existing = [
            {"日期": "2024-01-01", "收盘": 3000}
        ]
        today_data = {
            "数据日期": "2024-01-02",
            "今开": 3000,
            "最新价": 3010,
            "最高": 3020,
            "最低": 2990,
            "成交量": 1000000,
        }

        result = fetcher._update_history(existing, today_data)
        assert len(result) == 2
        assert result[0]["日期"] == "2024-01-02"

    def test_update_history_same_day(self, fetcher):
        """测试更新历史数据 - 同一天更新"""
        existing = [
            {"日期": "2024-01-02", "收盘": 3000}
        ]
        today_data = {
            "数据日期": "2024-01-02",
            "今开": 3000,
            "最新价": 3010,
            "最高": 3020,
            "最低": 2990,
            "成交量": 1000000,
        }

        result = fetcher._update_history(existing, today_data)
        assert len(result) == 1
        assert result[0]["收盘"] == 3010

    def test_update_history_limit(self, fetcher):
        """测试更新历史数据 - 限制数量"""
        existing = [{"日期": f"2024-01-{i:02d}", "收盘": 3000} for i in range(1, 8)]
        today_data = {
            "数据日期": "2024-01-08",
            "今开": 3000,
            "最新价": 3010,
            "最高": 3020,
            "最低": 2990,
            "成交量": 1000000,
        }

        result = fetcher._update_history(existing, today_data)
        assert len(result) == 7

    @pytest.mark.asyncio
    async def test_fetch_all_domestic_indexes_async(self, fetcher):
        """测试异步获取所有国内指数"""
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows = MagicMock(return_value=iter([
            (0, {"代码": "000001", "名称": "上证指数", "最新价": 3000.0, "昨收": 2990.0, 
                 "今开": 2995.0, "最高": 3010.0, "最低": 2990.0, "成交量": 1000000, "成交额": 5000000}),
            (1, {"代码": "000300", "名称": "沪深300", "最新价": 4000.0, "昨收": 3990.0,
                 "今开": 3995.0, "最高": 4010.0, "最低": 3990.0, "成交量": 2000000, "成交额": 6000000}),
        ]))

        mock_ak = MagicMock()
        mock_ak.stock_zh_index_spot_em = MagicMock(return_value=mock_df)
        fetcher._akshare = mock_ak

        result = await fetcher.fetch_all_domestic_indexes_async()

        assert isinstance(result, dict)
