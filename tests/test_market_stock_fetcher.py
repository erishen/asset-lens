"""
Tests for market_stock_fetcher.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestMarketStockFetcher:
    """MarketStockFetcher 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_path):
        """创建测试实例"""
        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        fetcher = MarketStockFetcher(cache_path=temp_cache_path)
        yield fetcher

    def test_init(self, fetcher, temp_cache_path):
        """测试初始化"""
        assert fetcher.cache_path == temp_cache_path
        assert fetcher.market_stock_cache_file == temp_cache_path / "market_stocks.json"

    def test_save_market_stocks(self, fetcher):
        """测试保存市场股票数据"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "current_price": 1800},
            {"code": "sz000001", "name": "平安银行", "current_price": 10},
        ]

        fetcher.save_market_stocks(stocks)

        assert fetcher.market_stock_cache_file.exists()
        with open(fetcher.market_stock_cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["total"] == 2
            assert len(data["data"]) == 2

    def test_get_cached_market_stocks_empty(self, fetcher):
        """测试获取缓存的市场股票数据 - 空缓存"""
        result = fetcher.get_cached_market_stocks()
        assert result == []

    def test_get_cached_market_stocks_with_data(self, fetcher):
        """测试获取缓存的市场股票数据 - 有数据"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "current_price": 1800},
        ]
        fetcher.save_market_stocks(stocks)

        result = fetcher.get_cached_market_stocks()
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_fetch_cn_stock_list_with_mock(self, fetcher):
        """测试获取A股股票列表 - 使用 mock"""
        mock_data = {
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "最新价": [1800],
            "涨跌幅": [2.5],
            "成交量": [1000000],
            "成交额": [1800000000],
            "换手率": [0.5],
            "市盈率-动态": [30],
            "总市值": [2000000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list(page=1, page_size=100)
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"
        assert result[0]["name"] == "贵州茅台"

    def test_fetch_cn_stock_list_empty_data(self, fetcher):
        """测试获取A股股票列表 - 空数据"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert result == []

    def test_fetch_cn_stock_list_exception(self, fetcher):
        """测试获取A股股票列表 - 异常"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.side_effect = Exception("网络错误")

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert result == []

    def test_fetch_all_cn_stocks_with_mock(self, fetcher):
        """测试获取所有A股股票 - 使用 mock"""
        mock_data = {
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "最新价": [1800],
            "涨跌幅": [2.5],
            "成交量": [1000000],
            "成交额": [1800000000],
            "换手率": [0.5],
            "市盈率-动态": [30],
            "总市值": [2000000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_all_cn_stocks()
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_fetch_all_cn_stocks_empty_data(self, fetcher):
        """测试获取所有A股股票 - 空数据"""
        mock_df = pd.DataFrame()

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_all_cn_stocks()
        assert result == []

    def test_fetch_all_cn_stocks_exception(self, fetcher):
        """测试获取所有A股股票 - 异常"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.side_effect = Exception("网络错误")

        fetcher._akshare = mock_ak

        result = fetcher.fetch_all_cn_stocks()
        assert result == []

    def test_fetch_cn_stock_list_sz_code(self, fetcher):
        """测试获取A股股票列表 - 深圳代码"""
        mock_data = {
            "代码": ["000001"],
            "名称": ["平安银行"],
            "最新价": [10],
            "涨跌幅": [1.5],
            "成交量": [5000000],
            "成交额": [50000000],
            "换手率": [0.3],
            "市盈率-动态": [10],
            "总市值": [200000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 1
        assert result[0]["code"] == "sz000001"

    def test_fetch_cn_stock_list_kcb_code(self, fetcher):
        """测试获取A股股票列表 - 科创板代码"""
        mock_data = {
            "代码": ["688001"],
            "名称": ["华兴源创"],
            "最新价": [50],
            "涨跌幅": [3.0],
            "成交量": [100000],
            "成交额": [5000000],
            "换手率": [1.0],
            "市盈率-动态": [50],
            "总市值": [5000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 1
        assert result[0]["code"] == "sh688001"

    def test_fetch_cn_stock_list_skip_invalid_code(self, fetcher):
        """测试获取A股股票列表 - 跳过无效代码"""
        mock_data = {
            "代码": ["999999"],
            "名称": ["无效代码"],
            "最新价": [0],
            "涨跌幅": [0],
            "成交量": [0],
            "成交额": [0],
            "换手率": [0],
            "市盈率-动态": [0],
            "总市值": [0],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 0

    def test_fetch_cn_stock_list_skip_empty_name(self, fetcher):
        """测试获取A股股票列表 - 跳过空名称"""
        mock_data = {
            "代码": ["600519"],
            "名称": [""],
            "最新价": [1800],
            "涨跌幅": [2.5],
            "成交量": [1000000],
            "成交额": [1800000000],
            "换手率": [0.5],
            "市盈率-动态": [30],
            "总市值": [2000000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 0

    def test_fetch_cn_stock_list_value_error(self, fetcher):
        """测试获取A股股票列表 - 数值转换错误"""
        mock_data = {
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "最新价": ["invalid"],
            "涨跌幅": ["invalid"],
            "成交量": ["invalid"],
            "成交额": ["invalid"],
            "换手率": ["invalid"],
            "市盈率-动态": ["invalid"],
            "总市值": ["invalid"],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 0

    def test_fetch_cn_stock_list_none_data(self, fetcher):
        """测试获取A股股票列表 - None 数据"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = None

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert result == []

    def test_fetch_all_cn_stocks_none_data(self, fetcher):
        """测试获取所有A股股票 - None 数据"""
        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = None

        fetcher._akshare = mock_ak

        result = fetcher.fetch_all_cn_stocks()
        assert result == []

    def test_fetch_cn_stock_list_chuangye_code(self, fetcher):
        """测试获取A股股票列表 - 创业板代码"""
        mock_data = {
            "代码": ["300001"],
            "名称": ["特锐德"],
            "最新价": [25],
            "涨跌幅": [2.0],
            "成交量": [200000],
            "成交额": [5000000],
            "换手率": [0.8],
            "市盈率-动态": [40],
            "总市值": [10000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 1
        assert result[0]["code"] == "sz300001"

    def test_fetch_cn_stock_list_skip_empty_code(self, fetcher):
        """测试获取A股股票列表 - 跳过空代码"""
        mock_data = {
            "代码": ["", "600519"],
            "名称": ["空代码", "贵州茅台"],
            "最新价": [0, 1800],
            "涨跌幅": [0, 2.5],
            "成交量": [0, 1000000],
            "成交额": [0, 1800000000],
            "换手率": [0, 0.5],
            "市盈率-动态": [0, 30],
            "总市值": [0, 2000000000000],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_fetch_cn_stock_list_with_none_values(self, fetcher):
        """测试获取A股股票列表 - None 值处理"""
        mock_data = {
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "最新价": [None],
            "涨跌幅": [None],
            "成交量": [None],
            "成交额": [None],
            "换手率": [None],
            "市盈率-动态": [None],
            "总市值": [None],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_ak = MagicMock()
        mock_ak.stock_zh_a_spot_em.return_value = mock_df

        fetcher._akshare = mock_ak

        result = fetcher.fetch_cn_stock_list()
        assert len(result) == 1
        assert result[0]["current_price"] == 0
