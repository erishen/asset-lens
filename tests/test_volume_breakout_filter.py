"""
Tests for volume_breakout_filter.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.data.volume_breakout_filter import (
    VolumeBreakoutConfig,
    VolumeBreakoutFilter,
)


class TestVolumeBreakoutConfig:
    """VolumeBreakoutConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = VolumeBreakoutConfig()
        assert config.turnover_ratio == 3.0
        assert config.amount_ratio == 2.0
        assert config.market_cap_max == 500.0
        assert config.market_cap_min == 20.0
        assert config.price_min == 5.0
        assert config.price_max == 100.0
        assert config.require_hot_industry is True
        assert config.max_results == 30

    def test_custom_values(self):
        """测试自定义值"""
        config = VolumeBreakoutConfig(
            turnover_ratio=5.0,
            amount_ratio=3.0,
            market_cap_max=1000.0,
            market_cap_min=50.0,
            price_min=10.0,
            price_max=200.0,
            require_hot_industry=False,
            max_results=50,
        )
        assert config.turnover_ratio == 5.0
        assert config.amount_ratio == 3.0
        assert config.market_cap_max == 1000.0
        assert config.market_cap_min == 50.0
        assert config.price_min == 10.0
        assert config.price_max == 200.0
        assert config.require_hot_industry is False
        assert config.max_results == 50


class TestVolumeBreakoutFilter:
    """VolumeBreakoutFilter 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def filter_instance(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.volume_breakout_filter.config') as mock_config:
            mock_config.project_root = temp_cache_path
            mock_config.cache_path = temp_cache_path
            filter_instance = VolumeBreakoutFilter()
            yield filter_instance

    def test_init(self, filter_instance):
        """测试初始化"""
        assert filter_instance.filter_config is not None
        assert filter_instance.cache_path is not None

    def test_get_industry_semiconductor(self, filter_instance):
        """测试获取行业 - 半导体"""
        result = filter_instance._get_industry("中芯国际半导体")
        assert result == "半导体"

    def test_get_industry_new_energy(self, filter_instance):
        """测试获取行业 - 新能源"""
        result = filter_instance._get_industry("宁德时代新能源")
        assert result == "新能源"

    def test_get_industry_medical(self, filter_instance):
        """测试获取行业 - 医药"""
        result = filter_instance._get_industry("恒瑞医药")
        assert result == "医药"

    def test_get_industry_unknown(self, filter_instance):
        """测试获取行业 - 未知"""
        result = filter_instance._get_industry("未知公司")
        assert result is None

    def test_load_market_stocks_no_file(self, filter_instance):
        """测试加载市场股票 - 文件不存在"""
        result = filter_instance._load_market_stocks()
        assert result == []

    def test_load_market_stocks_with_file(self, filter_instance):
        """测试加载市场股票 - 有文件"""
        data = {"data": [{"code": "sh600519", "name": "贵州茅台"}]}
        with open(filter_instance.market_stock_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = filter_instance._load_market_stocks()
        assert len(result) == 1
        assert result[0]["code"] == "sh600519"

    def test_load_history_no_file(self, filter_instance):
        """测试加载历史数据 - 文件不存在"""
        result = filter_instance._load_history()
        assert result == {}

    def test_load_history_with_file(self, filter_instance):
        """测试加载历史数据 - 有文件"""
        history = {"sh600519": {"name": "贵州茅台", "turnover_rates": [1.0, 2.0]}}
        with open(filter_instance.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f)

        result = filter_instance._load_history()
        assert "sh600519" in result

    def test_save_history(self, filter_instance):
        """测试保存历史数据"""
        history = {"sh600519": {"name": "贵州茅台", "turnover_rates": [1.0]}}
        filter_instance._save_history(history)

        assert filter_instance.history_file.exists()

    def test_update_history(self, filter_instance):
        """测试更新历史数据"""
        stocks = [
            {"code": "sh600519", "name": "贵州茅台", "turnover_rate": 0.5, "amount": 1000000},
        ]

        filter_instance.update_history(stocks)

        history = filter_instance._load_history()
        assert "sh600519" in history
        assert history["sh600519"]["name"] == "贵州茅台"

    def test_get_avg_turnover_60d(self, filter_instance):
        """测试获取60日平均换手率"""
        history = {
            "sh600519": {
                "name": "贵州茅台",
                "turnover_rates": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        }

        result = filter_instance._get_avg_turnover_60d("sh600519", history)

        assert result is not None
        assert result == 3.0  # (1+2+3+4+5) / 5

    def test_get_avg_turnover_60d_insufficient_data(self, filter_instance):
        """测试获取60日平均换手率 - 数据不足"""
        history = {
            "sh600519": {
                "name": "贵州茅台",
                "turnover_rates": [1.0, 2.0],
            }
        }

        result = filter_instance._get_avg_turnover_60d("sh600519", history)

        assert result is None

    def test_get_avg_amount_60d(self, filter_instance):
        """测试获取60日平均成交额"""
        history = {
            "sh600519": {
                "name": "贵州茅台",
                "amounts": [1000000, 2000000, 3000000, 4000000, 5000000, 6000000],
            }
        }

        result = filter_instance._get_avg_amount_60d("sh600519", history)

        assert result is not None
        assert result == 3000000.0

    def test_get_avg_amount_60d_insufficient_data(self, filter_instance):
        """测试获取60日平均成交额 - 数据不足"""
        history = {
            "sh600519": {
                "name": "贵州茅台",
                "amounts": [1000000],
            }
        }

        result = filter_instance._get_avg_amount_60d("sh600519", history)

        assert result is None
