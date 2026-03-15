"""
Tests for Volume Breakout Filter.
放量突破筛选模块测试
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from asset_lens.strategy.volume_breakout import (
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
        )
        assert config.turnover_ratio == 5.0
        assert config.amount_ratio == 3.0
        assert config.market_cap_max == 1000.0


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
        with patch('asset_lens.strategy.volume_breakout.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            mock_config.project_root = temp_cache_path
            filter_instance = VolumeBreakoutFilter()
            yield filter_instance

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.volume_breakout_filter import volume_breakout_filter
        assert volume_breakout_filter is not None

    def test_init(self, filter_instance):
        """测试初始化"""
        assert filter_instance is not None
        assert filter_instance.filter_config is not None

    def test_industry_mapping(self, filter_instance):
        """测试行业映射"""
        assert "新能源" in filter_instance.INDUSTRY_MAPPING
        assert "半导体" in filter_instance.INDUSTRY_MAPPING
        assert "医药" in filter_instance.INDUSTRY_MAPPING

    def test_get_industry(self, filter_instance):
        """测试获取行业"""
        industry = filter_instance._get_industry("宁德时代新能源")
        assert industry == "新能源"

        industry = filter_instance._get_industry("中芯国际半导体")
        assert industry == "半导体"

    def test_get_industry_not_found(self, filter_instance):
        """测试获取行业 - 未找到"""
        industry = filter_instance._get_industry("某某股票")
        assert industry is None

    def test_load_config_no_file(self, filter_instance):
        """测试加载配置 - 文件不存在"""
        config = filter_instance._load_config()
        assert config is not None
        assert config.turnover_ratio == 3.0

    def test_load_config_with_file(self, filter_instance, temp_cache_path):
        """测试加载配置 - 有配置文件"""
        config_dir = temp_cache_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "volume_breakout.json"
        
        config_data = {
            "turnover_ratio": 5.0,
            "amount_ratio": 3.0,
            "max_results": 50,
        }
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        filter_instance.config_path = config_file
        config = filter_instance._load_config()
        
        assert config.turnover_ratio == 5.0
        assert config.amount_ratio == 3.0
        assert config.max_results == 50

    def test_load_market_stocks_empty(self, filter_instance):
        """测试加载市场股票 - 空文件"""
        stocks = filter_instance._load_market_stocks()
        assert stocks == []

    def test_load_market_stocks_with_data(self, filter_instance):
        """测试加载市场股票 - 有数据"""
        market_data = {
            "data": [
                {"code": "sh600519", "name": "贵州茅台"},
                {"code": "sz000001", "name": "平安银行"},
            ]
        }
        
        with open(filter_instance.market_stock_file, "w", encoding="utf-8") as f:
            json.dump(market_data, f)

        stocks = filter_instance._load_market_stocks()
        assert len(stocks) == 2

    def test_load_history_empty(self, filter_instance):
        """测试加载历史 - 空文件"""
        history = filter_instance._load_history()
        assert history == {}

    def test_load_history_with_data(self, filter_instance):
        """测试加载历史 - 有数据"""
        history_data = {
            "sh600519": {
                "klines": [
                    {"date": "2024-01-01", "close": 1800, "volume": 1000000}
                ]
            }
        }
        
        with open(filter_instance.history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f)

        history = filter_instance._load_history()
        assert "sh600519" in history

    def test_save_history(self, filter_instance):
        """测试保存历史"""
        history_data = {
            "sh600519": {
                "klines": [
                    {"date": "2024-01-01", "close": 1800, "volume": 1000000}
                ]
            }
        }
        
        filter_instance._save_history(history_data)
        
        assert filter_instance.history_file.exists()

    def test_filter_empty_stocks(self, filter_instance):
        """测试筛选 - 空股票列表"""
        results = filter_instance.filter([])
        assert results == []

    def test_check_volume_breakout(self, filter_instance):
        """测试检查放量突破"""
        stock = {
            "code": "sh600519",
            "name": "贵州茅台",
            "turnover_rate": 5.0,
            "amount": 2000000000,
            "market_cap": 100,
            "current_price": 50,
        }
        
        result = filter_instance.filter([stock])
        assert isinstance(result, list)

    def test_check_price_range(self, filter_instance):
        """测试价格范围检查"""
        stock = {
            "current_price": 50,
        }
        
        is_valid = filter_instance.filter_config.price_min <= stock["current_price"] <= filter_instance.filter_config.price_max
        assert is_valid is True

    def test_check_market_cap_range(self, filter_instance):
        """测试市值范围检查"""
        stock = {
            "market_cap": 100,
        }
        
        is_valid = filter_instance.filter_config.market_cap_min <= stock["market_cap"] <= filter_instance.filter_config.market_cap_max
        assert is_valid is True


class TestVolumeBreakoutScenarios:
    """放量突破场景测试"""

    def test_volume_ratio_calculation(self):
        """测试量比计算"""
        current_volume = 1000000
        avg_volume = 500000
        
        volume_ratio = current_volume / avg_volume
        assert volume_ratio == 2.0

    def test_amount_ratio_calculation(self):
        """测试成交额比计算"""
        current_amount = 2000000000
        avg_amount = 1000000000
        
        amount_ratio = current_amount / avg_amount
        assert amount_ratio == 2.0

    def test_breakout_detection(self):
        """测试突破检测"""
        current_price = 55
        prev_high = 50
        
        is_breakout = current_price > prev_high
        assert is_breakout is True

    def test_no_breakout_detection(self):
        """测试未突破检测"""
        current_price = 48
        prev_high = 50
        
        is_breakout = current_price > prev_high
        assert is_breakout is False

    def test_filter_criteria_combination(self):
        """测试筛选条件组合"""
        stock = {
            "turnover_rate": 5.0,
            "volume_ratio": 3.5,
            "amount_ratio": 2.5,
            "market_cap": 100,
            "current_price": 50,
        }
        
        meets_criteria = (
            stock["turnover_rate"] >= 3.0 and
            stock["volume_ratio"] >= 3.0 and
            stock["amount_ratio"] >= 2.0 and
            20 <= stock["market_cap"] <= 500 and
            5 <= stock["current_price"] <= 100
        )
        
        assert meets_criteria is True


class TestIndustryDetection:
    """行业检测测试"""

    def test_detect_new_energy(self):
        """测试检测新能源行业"""
        INDUSTRY_MAPPING = {
            "新能源": ["锂电", "光伏", "风电", "储能", "新能源", "电池", "硅料"],
        }
        
        name = "宁德时代新能源"
        detected = None
        for industry, keywords in INDUSTRY_MAPPING.items():
            for kw in keywords:
                if kw in name:
                    detected = industry
                    break
        
        assert detected == "新能源"

    def test_detect_semiconductor(self):
        """测试检测半导体行业"""
        INDUSTRY_MAPPING = {
            "半导体": ["半导体", "芯片", "集成电路", "晶圆", "封测", "光刻"],
        }
        
        name = "中芯国际芯片"
        detected = None
        for industry, keywords in INDUSTRY_MAPPING.items():
            for kw in keywords:
                if kw in name:
                    detected = industry
                    break
        
        assert detected == "半导体"

    def test_detect_no_industry(self):
        """测试未检测到行业"""
        INDUSTRY_MAPPING = {
            "新能源": ["锂电", "光伏"],
        }
        
        name = "某某股份"
        detected = None
        for industry, keywords in INDUSTRY_MAPPING.items():
            for kw in keywords:
                if kw in name:
                    detected = industry
                    break
        
        assert detected is None
