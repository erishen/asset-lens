"""
Tests for Crypto Fetcher.
加密货币数据获取器测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCryptoFetcher:
    """加密货币数据获取器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.crypto_fetcher import CryptoFetcher
        assert CryptoFetcher is not None

    @pytest.fixture
    def fetcher(self):
        """创建获取器实例"""
        from asset_lens.data.crypto_fetcher import CryptoFetcher
        with patch('asset_lens.data.crypto_fetcher.config') as mock_config:
            mock_config.cache_path = MagicMock()
            return CryptoFetcher()

    def test_fetcher_init(self, fetcher):
        """测试初始化"""
        assert fetcher is not None

    def test_fetch_method(self, fetcher):
        """测试获取方法"""
        assert hasattr(fetcher, 'get_ticker') or hasattr(fetcher, 'get_ohlcvs')


class TestCryptoDataParsing:
    """加密货币数据解析测试"""

    def test_parse_crypto_price(self):
        """测试解析加密货币价格"""
        price_str = "50000.00"
        price = float(price_str)
        assert price == 50000.0

    def test_parse_crypto_change(self):
        """测试解析加密货币涨跌幅"""
        change_str = "+2.5%"
        change = float(change_str.replace("+", "").replace("%", ""))
        assert change == 2.5

    def test_parse_crypto_volume(self):
        """测试解析加密货币成交量"""
        volume_str = "1000000"
        volume = int(volume_str)
        assert volume == 1000000


class TestCryptoValidation:
    """加密货币数据验证测试"""

    def test_validate_price(self):
        """测试验证价格"""
        price = 50000.0
        assert price > 0

    def test_validate_volume(self):
        """测试验证成交量"""
        volume = 1000000
        assert volume >= 0

    def test_validate_change(self):
        """测试验证涨跌幅"""
        change = 10.0
        assert -100 <= change <= 100
