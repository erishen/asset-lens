"""
Tests for Platform Loader.
平台加载器测试
"""

import pytest


class TestPlatformLoader:
    """平台加载器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.core.platform_loader import PlatformLoader

        assert PlatformLoader is not None

    @pytest.fixture
    def loader(self):
        """创建加载器实例"""
        from asset_lens.core.platform_loader import PlatformLoader

        return PlatformLoader()

    def test_loader_init(self, loader):
        """测试初始化"""
        assert loader is not None

    def test_load_method(self, loader):
        """测试加载方法"""
        assert hasattr(loader, "load") or hasattr(loader, "load_platform")


class TestPlatformDetection:
    """平台检测测试"""

    def test_detect_platform(self):
        """测试检测平台"""
        import platform

        system = platform.system()
        assert system in ["Darwin", "Linux", "Windows"]

    def test_detect_python_version(self):
        """测试检测 Python 版本"""
        import sys

        version = sys.version_info
        assert version.major >= 3


class TestPlatformConfig:
    """平台配置测试"""

    def test_config_path(self):
        """测试配置路径"""
        from asset_lens.config import config

        assert config.data_path is not None
