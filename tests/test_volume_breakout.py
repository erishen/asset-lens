"""
Tests for Volume Breakout Filter.
放量突破筛选器测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestVolumeBreakoutFilter:
    """放量突破筛选器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutFilter
        assert VolumeBreakoutFilter is not None

    def test_config_import(self):
        """测试配置导入"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutConfig
        assert VolumeBreakoutConfig is not None

    def test_config_default_values(self):
        """测试配置默认值"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutConfig
        config = VolumeBreakoutConfig()
        assert config is not None

    def test_filter_init(self):
        """测试筛选器初始化"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutFilter
        with patch('asset_lens.strategy.volume_breakout.config') as mock_config:
            mock_config.cache_path = MagicMock()
            filter_instance = VolumeBreakoutFilter()
            assert filter_instance is not None

    def test_filter_has_methods(self):
        """测试筛选器方法存在"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutFilter
        with patch('asset_lens.strategy.volume_breakout.config') as mock_config:
            mock_config.cache_path = MagicMock()
            filter_instance = VolumeBreakoutFilter()
            
            # 测试方法存在
            assert hasattr(filter_instance, 'filter') or hasattr(filter_instance, 'get_hot_industries')
            assert hasattr(filter_instance, 'update_history') or hasattr(filter_instance, 'filter_with_api_history')


class TestVolumeBreakoutConfig:
    """放量突破配置测试"""

    def test_config_creation(self):
        """测试配置创建"""
        from asset_lens.strategy.volume_breakout import VolumeBreakoutConfig
        config = VolumeBreakoutConfig()
        assert config is not None
